import logging
from enum import Enum
from selenium.webdriver.common.by import By
from otrbot.models import Deadline

class ConstantContract(Enum):
  # Contract basic tab
  INPUT_ENTRY_DATE = "//input[@id='szerzodes_hatalybaLepesDatum']" 
  BUTTON_LIFTING = "//button[@id='szerzodes_adatokAtemelese']"


class ContractService:
  def __init__(self, browser):
    self._browser = browser
    self._const = ConstantContract
    self._logger = logging.getLogger() 

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self._logger.debug("The contract has been done")   

  def fillContractBasicTab(self, deadline: Deadline):
    self._browser.sendKeys(By.XPATH, self._const.INPUT_ENTRY_DATE.value, deadline.contract_entry_date)
    self._browser.clickElement(By.XPATH, self._const.BUTTON_LIFTING.value)