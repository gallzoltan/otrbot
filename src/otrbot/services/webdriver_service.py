import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException

class WebDriver:
  def __init__(self, argumens: tuple, os: str = 'windows', headless: bool = False):
    self.headless = headless
    self.options = Options()
    self.options.headless = self.headless
    self._set_arguments(argumens)
    if os == 'windows':
      self.driver = webdriver.Firefox(options=self.options)
    # else:
    #   service = FirefoxService('/snap/bin/geckodriver')    
    #   self.driver = webdriver.Firefox(options=self.options, service=service)
    self._logger = logging.getLogger() 
    self._logger.info('Start web driver')

  def close(self):
    self.driver.close()
    self._logger.info('Close web driver')
  
  def catchError(self, how, what):
    try:
      el = WebDriverWait(self.driver, timeout=20).until(EC.presence_of_element_located((how, what)))
      WebDriverWait(self.driver, timeout=20).until(EC.visibility_of(el))
      result = el.text      
      return result
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
      self._logger.error(e)
      return None    
  
  def clickElement(self, how, what):
    try: 
      el = WebDriverWait(self.driver, timeout=100).until(EC.presence_of_element_located((how, what)))
      WebDriverWait(self.driver, timeout=50).until(EC.visibility_of(el))
      WebDriverWait(self.driver, timeout=50).until(EC.element_to_be_clickable(el))
      # webdriver.ActionChains(self.driver).move_to_element(el).click(el).perform()
      el.click()  
      return True          
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e: 
      self._logger.error(e)
    return False
  
  def sendKeys(self, how, what, value):
    try:
      el = WebDriverWait(self.driver, timeout=50).until(EC.presence_of_element_located((how, what)))
      WebDriverWait(self.driver, timeout=50).until(EC.visibility_of(el))
      el.clear()
      el.send_keys(value)
      el.send_keys(Keys.TAB)
      return True
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e: 
      self._logger.error(e)
    return False    

  def selectBySendKeys(self, how:str, what:str, value:str):
    try:
      el = WebDriverWait(self.driver, timeout=20).until(EC.presence_of_element_located((how, what)))
      WebDriverWait(self.driver, timeout=10).until(EC.visibility_of(el))
      el.clear()
      el.send_keys(value)
      # el.send_keys(Keys.ARROW_DOWN)
      selId = el.get_attribute("aria-owns")
      first_option = WebDriverWait(self.driver, timeout=20).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{selId}-option-0']")))
      WebDriverWait(self.driver, timeout=10).until(EC.element_to_be_clickable(first_option))
      first_option.click()
      return True
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
      self._logger.error(e)
    return False
  
  def selectOption(self, how:str, what:str, value:str):
    try:
      el = WebDriverWait(self.driver, timeout=50).until(EC.presence_of_element_located((how, what)))
      WebDriverWait(self.driver, timeout=50).until(EC.visibility_of(el))
      # WebDriverWait(self.driver, timeout=50).until(EC.element_to_be_clickable(el))
      # WebDriverWait(self.driver, timeout=50).until(EC.element_to_be_selected(el))
      Select(el).select_by_visible_text(value)
      return True
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
      self._logger.error(e)
    return False 

  def selectOptionByValue(self, how:str, what:str, value:str):
    try:
      el = WebDriverWait(self.driver, timeout=50).until(EC.presence_of_element_located((how, what)))
      WebDriverWait(self.driver, timeout=50).until(EC.visibility_of(el))
      # WebDriverWait(self.driver, timeout=50).until(EC.element_to_be_clickable(el))
      # WebDriverWait(self.driver, timeout=50).until(EC.element_to_be_selected(el))
      # el = driver.execute_script("document.querySelector('#statusz > option:nth-child(3)')")            
      Select(el).select_by_value(value)
      return True
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
      self._logger.error(e)
    return False 

  def is_checked(self, item_id):
    checked = self.driver.execute_script(f"return document.getElementById('{item_id}').checked")
    return checked   

  def findGridElementRows(self):
    try:
      el = WebDriverWait(self.driver, timeout=20).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@id, '-grid-container')]/div[2]/div")))      
      WebDriverWait(self.driver, timeout=20).until(EC.visibility_of(el))
      grid = el.find_element(By.XPATH, "//div[@role='grid']/div[2]/div")
      rows = grid.find_elements(By.XPATH, ".//div[@role='row']")
      return rows         
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
      self._logger.error(e)
    return None

  # def itemsPerPage(self, how, what, value):
  #   try:
  #     el = WebDriverWait(self.driver, timeout=10).until(EC.presence_of_element_located((how, what)))
  #     WebDriverWait(self.driver, timeout=10).until(EC.visibility_of(el))
  #     self.driver.execute_script("arguments[0].setAttribute('value', arguments[1])", el, value)
  #     return True
  #   except () as e:
  #     self._logger.error(e)
  #   return None  

  def _set_arguments(self, argumens: tuple):
    for arg in argumens:
      self.options.add_argument(arg)