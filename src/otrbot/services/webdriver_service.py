import functools
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from otrbot.constants import TimeoutConfig, WebDriverConfig
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException

LOOKUP_ERRORS = (NoSuchElementException, StaleElementReferenceException, TimeoutException)

# Sets the value through the native setter so both React and AngularJS pick up the change
SET_VALUE_JS = """
const el = arguments[0], value = arguments[1];
const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));
el.dispatchEvent(new FocusEvent('blur'));
el.dispatchEvent(new FocusEvent('focusout', {bubbles: true}));
return el.value;
"""

DISABLE_ANIMATIONS_JS = """
if (!document.getElementById('otrbot-no-animation')) {
  const style = document.createElement('style');
  style.id = 'otrbot-no-animation';
  style.textContent = '*, *::before, *::after { transition: none !important; animation: none !important; }';
  document.head.appendChild(style);
}
"""

READ_GRID_JS = """
const grid = document.evaluate("//div[@role='grid']/div[2]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
if (!grid) return null;
return Array.from(grid.querySelectorAll("div[role='row']")).map(row =>
  Array.from(row.querySelectorAll("div[role='gridcell']")).map(cell => {
    const div = cell.querySelector('div');
    return {id: cell.id, title: div ? div.innerText.trim() : ''};
  }));
"""

# True when the page is loaded and no AngularJS app (OTR bootstraps it on #otr_angular_inner) has pending HTTP requests
PAGE_IDLE_JS = """
if (document.readyState !== 'complete') return false;
if (!window.angular) return true;
for (const root of document.querySelectorAll('[ng-app], [data-ng-app]')) {
  try {
    const injector = window.angular.element(root).injector();
    if (injector && injector.get('$http').pendingRequests.length > 0) return false;
  } catch (e) {}
}
return true;
"""


class StepFailed(Exception):
  """A browser step failed; the current item cannot be completed."""


class StepTimings:
  """Collects how long each browser step takes, to find the slow ones."""
  def __init__(self):
    self._steps: Dict[Tuple[str, str], List[float]] = {}

  def record(self, method: str, what: str, elapsed: float):
    entry = self._steps.setdefault((method, what), [0, 0.0])
    entry[0] += 1
    entry[1] += elapsed

  def slowest(self, n: int = 10) -> List[Tuple[str, str, int, float]]:
    """Returns (method, locator, count, total seconds) ordered by total time."""
    rows = [(method, what, count, total) for (method, what), (count, total) in self._steps.items()]
    return sorted(rows, key=lambda r: r[3], reverse=True)[:n]


def _timed(func):
  @functools.wraps(func)
  def wrapper(self, how, what, *args, **kwargs):
    start = time.perf_counter()
    try:
      return func(self, how, what, *args, **kwargs)
    finally:
      elapsed = time.perf_counter() - start
      self.timings.record(func.__name__, what, elapsed)
      self._logger.debug(f"{func.__name__} {elapsed:.2f}s {what}")
  return wrapper


class WebDriver:
  def __init__(self, arguments: Tuple[str, ...] = None, os: str = 'windows', headless: bool = False):
    options = arguments or WebDriverConfig.DEFAULT_OPTIONS
    self.headless = headless
    self.options = Options()
    self._set_arguments(options)
    if self.headless:
      self.options.add_argument("-headless")
    for name, value in WebDriverConfig.PREFERENCES.items():
      self.options.set_preference(name, value)
    self.options.page_load_strategy = WebDriverConfig.PAGE_LOAD_STRATEGY
    # Linux: geckodriver from snap may need FirefoxService('/snap/bin/geckodriver')
    self.driver = webdriver.Firefox(options=self.options)
    # Headless Firefox starts at 1366x768; a bigger viewport keeps buttons on screen
    width, height = WebDriverConfig.WINDOW_SIZE
    self.driver.set_window_size(width, height)
    # When strict, a failed step raises StepFailed instead of returning False
    self.strict = False
    self.timings = StepTimings()
    self._logger = logging.getLogger()
    self._logger.info('Start web driver')

  def close(self):
    try:
      self.driver.quit()
    except WebDriverException as e:
      self._logger.error(e)
    self._logger.info('Close web driver')

  def is_alive(self) -> bool:
    try:
      self.driver.title
      return True
    except WebDriverException:
      return False

  def open(self, url: str):
    self.driver.get(url)
    self.disableAnimations()

  def disableAnimations(self):
    if not WebDriverConfig.DISABLE_ANIMATIONS:
      return
    try:
      self.driver.execute_script(DISABLE_ANIMATIONS_JS)
    except WebDriverException as e:
      self._logger.debug(f"Could not disable animations: {e}")

  def waitForPageIdle(self, timeout: int = TimeoutConfig.DEFAULT) -> bool:
    try:
      self._wait(timeout).until(lambda d: d.execute_script(PAGE_IDLE_JS))
      return True
    except TimeoutException:
      self._logger.debug("Page is still busy")
      return False

  def isPresent(self, how, what, timeout: int = TimeoutConfig.SHORT) -> bool:
    try:
      self._wait(timeout).until(EC.visibility_of_element_located((how, what)))
      return True
    except LOOKUP_ERRORS:
      return False

  def saveDebugInfo(self, path_base: str):
    """Saves a screenshot and the page source as <path_base>.png / .html."""
    Path(path_base).parent.mkdir(parents=True, exist_ok=True)
    self.driver.save_screenshot(f"{path_base}.png")
    Path(f"{path_base}.html").write_text(self.driver.page_source, encoding="utf-8")

  @_timed
  def catchError(self, how: str, what: str) -> str:
    try:
      el = self._wait(TimeoutConfig.DEFAULT).until(EC.visibility_of_element_located((how, what)))
      return el.text
    except LOOKUP_ERRORS as e:
      self._logger.error(e)
      return ""

  @_timed
  def clickElement(self, how, what):
    try:
      el = self._wait(TimeoutConfig.LONG).until(EC.element_to_be_clickable((how, what)))
      # An overlay (backdrop, spinner) may still cover the element: retry until it is gone
      self._wait(TimeoutConfig.MEDIUM, ignored=(ElementClickInterceptedException,)).until(lambda d: el.click() or True)
      return True
    except LOOKUP_ERRORS as e:
      return self._fail(f"Failed to click element {what}: {e}")
    except Exception as e:
      return self._fail(f"Unexpected error clicking element {what}: {e}")

  @_timed
  def sendKeys(self, how, what, value):
    try:
      el = self._wait(TimeoutConfig.MEDIUM).until(EC.visibility_of_element_located((how, what)))
      el.clear()
      el.send_keys(value + Keys.TAB)
      return True
    except LOOKUP_ERRORS as e:
      return self._fail(f"Failed to send keys to {what}: {e}")

  @_timed
  def setValue(self, how, what, value):
    """Fast fill for plain text inputs; falls back to typing if the page rejects it."""
    try:
      el = self._wait(TimeoutConfig.MEDIUM).until(EC.visibility_of_element_located((how, what)))
      if self.driver.execute_script(SET_VALUE_JS, el, value) == value:
        return True
      self._logger.debug(f"setValue was not accepted, typing instead: {what}")
      el.clear()
      el.send_keys(value + Keys.TAB)
      return True
    except LOOKUP_ERRORS as e:
      return self._fail(f"Failed to set value of {what}: {e}")

  @_timed
  def selectBySendKeys(self, how:str, what:str, value:str):
    try:
      el = self._wait(TimeoutConfig.DEFAULT).until(EC.visibility_of_element_located((how, what)))
      el.clear()
      el.send_keys(value)
      selId = el.get_attribute("aria-owns")
      first_option = self._wait(TimeoutConfig.DEFAULT).until(EC.element_to_be_clickable((By.XPATH, f"//li[@id='{selId}-option-0']")))
      first_option.click()
      return True
    except LOOKUP_ERRORS as e:
      return self._fail(f"Failed to select {value} in {what}: {e}")

  @_timed
  def selectOption(self, how:str, what:str, value:str):
    try:
      el = self._wait(TimeoutConfig.MEDIUM).until(EC.visibility_of_element_located((how, what)))
      # The options of popup selects are loaded after the select itself becomes visible
      self._wait(TimeoutConfig.SHORT).until(lambda d: any(o.text.strip() == value.strip() for o in Select(el).options))
      Select(el).select_by_visible_text(value)
      return True
    except LOOKUP_ERRORS as e:
      return self._fail(f"Failed to select {value} in {what}: {e}")

  @_timed
  def selectOptionByValue(self, how:str, what:str, value:str):
    try:
      el = self._wait(TimeoutConfig.MEDIUM).until(EC.visibility_of_element_located((how, what)))
      self._wait(TimeoutConfig.SHORT).until(lambda d: any(o.get_attribute("value") == value for o in Select(el).options))
      Select(el).select_by_value(value)
      return True
    except LOOKUP_ERRORS as e:
      return self._fail(f"Failed to select {value} in {what}: {e}")

  def is_checked(self, item_id):
    return self.driver.execute_script("return document.getElementById(arguments[0]).checked", item_id)

  def readGrid(self) -> Optional[List[List[dict]]]:
    """Reads the search result grid in one call: a list of rows, each a list of {id, title} cells."""
    try:
      self._wait(TimeoutConfig.DEFAULT).until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@id, '-grid-container')]/div[2]/div")))
      self.waitForPageIdle()
      # The grid is rendered before the search response arrives, wait for its rows
      return self._wait(TimeoutConfig.SHORT).until(lambda d: d.execute_script(READ_GRID_JS))
    except LOOKUP_ERRORS as e:
      self._logger.error(f"Empty search result grid: {e}")
    return None

  def _wait(self, timeout, ignored=None) -> WebDriverWait:
    return WebDriverWait(self.driver, timeout=timeout, poll_frequency=TimeoutConfig.POLL, ignored_exceptions=ignored)

  def _fail(self, message: str) -> bool:
    self._logger.error(message)
    if self.strict:
      raise StepFailed(message)
    return False

  def _set_arguments(self, arguments: tuple):
    for arg in arguments:
      self.options.add_argument(arg)
