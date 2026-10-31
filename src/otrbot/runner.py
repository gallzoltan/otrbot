import logging
import time
import otrbot
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterator, Optional
from .constants import Navigate, SubmitForms, RunnerConfig
from .journal import Journal, OK, FAILED
from .models import Master, Address, Denomination, Deadline, Amount
from .services.webdriver_service import StepFailed
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException


@dataclass
class Item:
  master: Master
  address: Address
  denomination: Denomination
  deadline: Deadline
  amount: Amount


class FinalSubmitError(Exception):
  """The final submit was confirmed but did not succeed. Not retried, because a retry could duplicate the item."""


class SubmittedUncertain(FinalSubmitError):
  """No result message after confirming: the item may or may not have been submitted."""


class ModuleRunner:
  def __init__(self, supporter: str, journal: Optional[Journal] = None,
               max_attempts: int = RunnerConfig.MAX_ATTEMPTS,
               max_consecutive_failures: int = RunnerConfig.MAX_CONSECUTIVE_FAILURES):
    self._bot = otrbot
    self._logger = logging.getLogger()
    self._supporter = supporter
    self._journal = journal
    self._max_attempts = max_attempts
    self._max_consecutive_failures = max_consecutive_failures
    self._needs_menu = True
    self._rounds: Dict[int, Callable[[Item], Optional[str]]] = {
      1: self._run_round1,
      2: self._run_round2,
      3: self._run_round3
    }

  def load_datas(self, excel_file_path, sheet_name, begin: Optional[int] = None, end: Optional[int] = None):
    """Loads the Excel rows and registers them in the journal (applicants); begin/end filter on the rowid column (end=0 means no upper limit)."""
    self.datas = self._bot.services.read_excel_file(excel_file_path, sheet_name)
    if self._journal:
      self._journal.load_applicants((m.rowid, a.city, m.regid) for m, a in zip(self.datas.masters, self.datas.addresses))
    self._begin = begin
    self._end = end
    self._logger.info("The datas has been loaded from excel file")
    return self

  def start_driver(self, options: tuple, system: str, headless: bool = False):
    self._driver_args = (options, system, headless)
    self.browser = self._bot.services.WebDriver(arguments=options, os=system,  headless=headless)
    self.browser.strict = True
    return self

  def login_otr(self, url: str, username: str, password: str):
    self._credentials = (url, username, password)
    if not self._bot.services.LoginOtr(self.browser).login(url, username, password):
      raise RuntimeError(f"Login to {url} failed")
    return self

  def close(self):
    if getattr(self, "browser", None):
      self.browser.close()

  def run(self, round) -> bool:
    if round not in self._rounds:
      self._logger.error(f"Unsupported round: {round}")
      return False

    items = list(self._items())
    todo = [item for item in items if not self._is_done(item, round)]
    if round == 1:
      todo = [item for item in todo if not self._skip_submitted(item)]
    self._logger.info(f"Round {round}: {len(items)} items, {len(items) - len(todo)} already done, {len(todo)} to process")

    succeeded, failed, durations = 0, 0, []
    consecutive_failures = 0
    for number, item in enumerate(todo, start=1):
      self._logger.info(f"[{number}/{len(todo)}] id:{item.master.rowid} city:{item.address.city}")
      start = time.perf_counter()
      if self._run_item(round, item):
        succeeded += 1
        durations.append(time.perf_counter() - start)
        consecutive_failures = 0
      else:
        failed += 1
        consecutive_failures += 1
        if consecutive_failures >= self._max_consecutive_failures:
          self._logger.error(f"{consecutive_failures} consecutive failures, stopping the run")
          break

    self._log_summary(round, succeeded, failed, len(todo), durations)
    return failed == 0 and succeeded == len(todo)

  def _items(self) -> Iterator[Item]:
    for row in zip(self.datas.masters, self.datas.addresses, self.datas.denominations, self.datas.deadlines, self.datas.amounts):
      item = Item(*row)
      rowid = item.master.rowid
      if self._begin and rowid < self._begin:
        continue
      if self._end and rowid > self._end:
        continue
      yield item

  def _is_done(self, item: Item, round: int) -> bool:
    return self._journal is not None and self._journal.is_done(item.master.rowid, round)

  def _skip_submitted(self, item: Item) -> bool:
    """An item that already has an OTR id (journal or Excel) was submitted before; submitting it again would create a duplicate."""
    otrid = str(self._otrid(item) or "").strip()
    if not otrid:
      return False
    self._logger.warning(f"Skipped, already submitted id:{item.master.rowid} city:{item.address.city} otrid:{otrid}")
    if self._journal:
      self._journal.mark(item.master.rowid, 1, OK, otrid=otrid, error=f"Kihagyva, már van OTR azonosító: {otrid}")
    return True

  def _run_item(self, round: int, item: Item) -> bool:
    """Runs one item with retries and recovery; returns True on success. Never raises for item level errors."""
    rowid = item.master.rowid
    error = None
    start = time.perf_counter()
    for attempt in range(1, self._max_attempts + 1):
      if self._journal:
        self._journal.start(rowid, round)
      try:
        self.browser.disableAnimations()
        if self._needs_menu:
          self._navigateTab(main_tab=Navigate.MENU_TAMOGATASOK.value)
          self._needs_menu = False
        otrid = self._rounds[round](item)
        if self._journal:
          self._journal.mark(rowid, round, OK, otrid=otrid, duration=time.perf_counter() - start)
        return True
      except FinalSubmitError as e:
        error = f"BIZONYTALAN, ellenőrizni kell az OTR-ben: {e}" if isinstance(e, SubmittedUncertain) else str(e)
        self._logger.error(f"id:{rowid} city:{item.address.city} {error}")
        self._recover(round, item, attempt)
        break
      except Exception as e:
        error = str(e).splitlines()[0] if str(e) else type(e).__name__
        self._logger.error(f"Attempt {attempt}/{self._max_attempts} failed id:{rowid} city:{item.address.city}: {error}")
        self._recover(round, item, attempt)
    if self._journal:
      self._journal.mark(rowid, round, FAILED, error=error, duration=time.perf_counter() - start)
    return False

  def _recover(self, round: int, item: Item, attempt: int):
    """Brings the browser back to a clean, logged-in state after a failed item."""
    self._needs_menu = True
    try:
      self.browser.saveDebugInfo(str(Path(RunnerConfig.FAIL_DIR) / f"{item.master.rowid}_r{round}_a{attempt}"))
    except Exception as e:
      self._logger.debug(f"Could not save debug info: {e}")
    url, username, password = self._credentials
    login = self._bot.services.LoginOtr(self.browser)
    try:
      if not self.browser.is_alive():
        raise WebDriverException("browser is not responding")
      self.browser.open(url)
      if login.isLoggedIn() or (login.isLoginPage() and login.login(url, username, password)):
        return
      raise WebDriverException("could not get back to the main menu")
    except WebDriverException as e:
      self._logger.error(f"Restarting the browser: {e}")
      self._restart_browser()

  def _restart_browser(self):
    try:
      self.browser.close()
    except Exception as e:
      self._logger.debug(e)
    options, system, headless = self._driver_args
    timings = self.browser.timings
    self.start_driver(options=options, system=system, headless=headless)
    self.browser.timings = timings
    url, username, password = self._credentials
    if not self._bot.services.LoginOtr(self.browser).login(url, username, password):
      self._logger.error("Login failed after browser restart")

  def _otrid(self, item: Item) -> str:
    """The OTR id captured by an earlier round (journal), otherwise from the Excel file."""
    return (self._journal and self._journal.otrid(item.master.rowid)) or item.master.otrid

  def _run_round1(self, item: Item) -> None:
    master, address, denomination, deadline, amount = item.master, item.address, item.denomination, item.deadline, item.amount
    self._navigateTab(main_tab=Navigate.MENU_UJ_TAMOGATAS.value)
    self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIMING.value)
    self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIMING.value, sub_tab=Navigate.TAB_SUB_CLAIMING.value, index=0)
    with self._bot.services.SubmissionService(self.browser) as submission:
      submission.fillClaimingBasicTab(master=master)
      self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value)
      self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value, sub_tab=Navigate.TAB_SUB_CLAIM.value, index=0)
      submission.fillClaimBasicTab(supporter=self._supporter, master=master, denomination=denomination, deadline=deadline, amount=amount)
      self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value, sub_tab=Navigate.TAB_SUB_CLAIM.value, index=1)
      submission.fillClaimPlaceOfUseTab(address=address)
      self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value, sub_tab=Navigate.TAB_SUB_CLAIM.value, index=2)
      submission.fillClaimSupportCategoriesTab(master=master, address=address, amount=amount)
    self._fixingForm("RogzitesKesz")
    self._logger.debug(f"Rögzítés kész: {address.city}")

  def _run_round2(self, item: Item) -> Optional[str]:
    master, address, deadline, amount = item.master, item.address, item.deadline, item.amount
    otrid = self._openExisting(item, status=1)
    self._navigateTab(main_tab=Navigate.TAB_MAIN_DECISION.value)
    with self._bot.services.DecisionService(self.browser) as decision:
      decision.fillDecisionBasicTab(deadline=deadline, amount=amount)
      self._navigateTab(main_tab=Navigate.TAB_MAIN_DECISION.value, sub_tab=Navigate.TAB_SUB_DECISION.value, index=1)
      decision.fillDecisionTab()
      self._navigateTab(main_tab=Navigate.TAB_MAIN_DECISION.value, sub_tab=Navigate.TAB_SUB_DECISION.value, index=3)
      decision.fillDecisionCategoryTab(master=master, address=address, amount=amount)
    self._fixingForm("DontesKesz")
    self._logger.debug(f"Rögzítés kész: {address.city}")
    return otrid

  def _run_round3(self, item: Item) -> Optional[str]:
    otrid = self._openExisting(item, status=2)
    self._navigateTab(main_tab=Navigate.TAB_MAIN_CONTRACT.value)
    self._navigateTab(main_tab=Navigate.TAB_MAIN_CONTRACT.value, sub_tab=Navigate.TAB_SUB_CONTRACT.value, index=0)
    with self._bot.services.ContractService(self.browser) as contract:
      contract.fillContractBasicTab(deadline=item.deadline)
      self._navigateTab(main_tab=Navigate.TAB_MAIN_CONTRACT.value, sub_tab=Navigate.TAB_SUB_CONTRACT.value, index=2)
    self._fixingForm("SzerzodesKesz")
    self._logger.debug(f"Rögzítés kész: {item.address.city}")
    return otrid

  def _openExisting(self, item: Item, status: int) -> Optional[str]:
    """Finds and opens the item in the support list; returns its OTR id read from the result grid."""
    self._navigateTab(main_tab=Navigate.MENU_LIST_TAMOGATAS.value)
    with self._bot.services.SupportListService(self.browser) as search:
      row = search.selectCouncilOnSearchForm(kid=item.master.kid, council=item.address.city, otrid=self._otrid(item), status=status, regid=item.master.regid)
    if not row:
      raise StepFailed(f"{item.address.city} nevű önkormányzat nem található!")
    self.browser.waitForPageIdle()
    return row.otrid or None

  def _navigateTab(self, main_tab, sub_tab=None, index=None):
    """
    Navigate to a main tab and optionally a sub tab.

    :param main_tab: The XPath of the main tab.
    :param sub_tab: The XPath of the sub tab. Default is None.
    :param index: The index of the sub tab. Default is None.
    """
    self.browser.clickElement(By.XPATH, main_tab)
    if sub_tab:
      self.browser.clickElement(By.XPATH, sub_tab[index])
    # Tabs load their data asynchronously and would overwrite fields filled in too early
    self.browser.waitForPageIdle()

  def _validForm(self):
    self.browser.clickElement(By.XPATH, SubmitForms.BUTTON_VALIDATION.value)
    result = self.browser.catchError(By.XPATH, SubmitForms.ERROR_NOTICE.value)
    self._logger.info(result)
    return "nem talált hibát!" in result

  def _fixingForm(self, what):
    """Clicks the final submit button; raises if the success message does not appear."""
    self.browser.clickElement(By.XPATH, SubmitForms.BUTTON_FIX.value.format(what=what))
    try:
      self.browser.clickElement(By.XPATH, SubmitForms.CONFIRM_OK_BUTTON.value)
    except StepFailed as e:
      # The confirmation dialog did not come up, so nothing has been submitted yet
      raise StepFailed(f"{what}: {e}")
    result = self.browser.catchError(By.XPATH, SubmitForms.ERROR_NOTICE.value)
    self._logger.info(result)
    if "sikeresen megtörtént" in result:
      return True
    if result:
      raise FinalSubmitError(f"{what}: {result}")
    raise SubmittedUncertain(f"{what}: no result message after confirming")

  def _saveForm(self):
    self.browser.clickElement(By.XPATH, SubmitForms.BUTTON_SAVE.value)
    result = self.browser.catchError(By.XPATH, SubmitForms.ERROR_NOTICE.value)
    self._logger.info(result)
    return "sikeresen megtörtént" in result

  def _log_summary(self, round: int, succeeded: int, failed: int, total: int, durations: list):
    average = sum(durations) / len(durations) if durations else 0
    self._logger.info(f"Round {round} finished: {succeeded} ok, {failed} failed, {total - succeeded - failed} not started, {average:.1f}s/item")
    if self._journal:
      self._logger.info(f"Journal totals for round {round}: {self._journal.counts(round)}")
      for rowid, city, error in self._journal.failed(round):
        self._logger.info(f"not ok id:{rowid} city:{city}: {error}")
    for method, what, count, total_time in self.browser.timings.slowest(10):
      self._logger.info(f"slow step {total_time:7.1f}s {count:5}x {method} {what}")
