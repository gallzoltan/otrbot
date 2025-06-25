import otrbot as bot
import logging
import time
from .constants import Navigate, SubmitForms
from selenium.webdriver.common.by import By

class ModuleRunner:  
  def __init__(self, supporter: str):
    self._bot = bot
    self._logger = logging.getLogger()
    self._supporter = supporter
    self._rounds = {
      1: self._run_round1,
      2: self._run_round2,
      3: self._run_round3
    }
    
  def load_datas(self, excel_file_path, sheet_name):
    self.datas = self._bot.services.read_excel_file(excel_file_path, sheet_name)
    self._logger.info("The datas has been loaded from excel file")
    return self

  def start_driver(self, options: tuple, system: str, headless: bool = False):
    self.browser = self._bot.services.WebDriver(argumens=options, os=system,  headless=headless)    
    return self

  def login_otr(self, url, username, password):
    self._bot.services.LoginOtr(self.browser).login(url, username, password)    
    return self

  def run(self, round) -> None:
    if round in self._rounds:
      self._rounds[round]()
    else:
      self._logger.error(f"The round {round} is not supported")   
  
  def _run_round1(self) -> None:   
    self._navigateTab(main_tab=Navigate.MENU_TAMOGATASOK.value)
    for (master, address, denomination, deadline, amount) in zip(self.datas.masters, self.datas.addresses, self.datas.denominations, self.datas.deadlines, self.datas.amounts):
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
      if(self._validForm()):
        self._logger.debug("Valid form")
        if(self._fixingForm("RogzitesKesz")):
          self._logger.debug(f"Rögzítés kész: {address.city}")
        else:
          self._logger.error(f"Rögzítés hiba id:{master.rowid} city:{address.city}")
      else:
        self._logger.error(f"Ellenőrzés hiba. id:{master.rowid} city:{address.city}")
  
  def _run_round2(self) -> None:
    self._navigateTab(main_tab=Navigate.MENU_TAMOGATASOK.value)
    for (master, address, denomination, deadline, amount) in zip(self.datas.masters, self.datas.addresses, self.datas.denominations, self.datas.deadlines, self.datas.amounts):
      self._navigateTab(main_tab=Navigate.MENU_LIST_TAMOGATAS.value)
      found = False
      with self._bot.services.SupportListService(self.browser) as search:
        found = search.selectCouncilOnSearchForm(kid=master.kid, council=address.city, otrid=master.otrid, status=1)
      if(found):
        time.sleep(2)
        self._navigateTab(main_tab=Navigate.TAB_MAIN_DECISION.value)
        with self._bot.services.DecisionService(self.browser) as decision:
          decision.fillDecisionBasicTab(deadline=deadline, amount=amount)
          self._navigateTab(main_tab=Navigate.TAB_MAIN_DECISION.value, sub_tab=Navigate.TAB_SUB_DECISION.value, index=1)
          decision.fillDecisionTab()
          self._navigateTab(main_tab=Navigate.TAB_MAIN_DECISION.value, sub_tab=Navigate.TAB_SUB_DECISION.value, index=3)
          decision.fillDecisionCategoryTab(master=master, address=address, amount=amount)
        # if(self._validForm()):
        #   self._logger.debug("Valid form")
        if(self._fixingForm("DontesKesz")):
          self._logger.debug(f"Rögzítés kész: {address.city}")
        else:
          self._logger.error(f"Rögzítés hiba id:{master.rowid} city:{address.city}")
        # else:
        #   self._logger.error(f"Ellenőrzés hiba. id:{master.rowid} city:{address.city}")
      else:
        self._logger.error(f"{address.city} nevű önkormányzat nem található!")      

  def _run_round3(self) -> None:
    self._navigateTab(main_tab=Navigate.MENU_TAMOGATASOK.value)
    for (master, address, denomination, deadline, amount) in zip(self.datas.masters, self.datas.addresses, self.datas.denominations, self.datas.deadlines, self.datas.amounts):
      self._navigateTab(main_tab=Navigate.MENU_LIST_TAMOGATAS.value)
      found = False
      with self._bot.services.SupportListService(self.browser) as search:
        found = search.selectCouncilOnSearchForm(kid=master.kid, council=address.city, otrid=master.otrid, status=2)
      if(found):
        time.sleep(2)
        self._navigateTab(main_tab=Navigate.TAB_MAIN_CONTRACT.value)
        self._navigateTab(main_tab=Navigate.TAB_MAIN_CONTRACT.value, sub_tab=Navigate.TAB_SUB_CONTRACT.value, index=0)
        with self._bot.services.ContractService(self.browser) as contract:
          contract.fillContractBasicTab(deadline=deadline)
          self._navigateTab(main_tab=Navigate.TAB_MAIN_CONTRACT.value, sub_tab=Navigate.TAB_SUB_CONTRACT.value, index=2)
        # if(self._validForm()):
        #   self._logger.debug("Valid form")
        if(self._fixingForm("SzerzodesKesz")):
          self._logger.debug(f"Rögzítés kész: {address.city}")
        else:
          self._logger.error(f"Rögzítés hiba id:{master.rowid} city:{address.city}")
        # else:
        #   self._logger.error(f"Ellenőrzés hiba. id:{master.rowid} city:{address.city}")
      else:
        self._logger.error(f"{address.city} nevű önkormányzat nem található!")

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

  def _validForm(self):
    self.browser.clickElement(By.XPATH, SubmitForms.BUTTON_VALIDATION.value)
    result = self.browser.catchError(By.XPATH, SubmitForms.ERROR_NOTICE.value)
    self._logger.info(result)
    if("nem talált hibát!" in result):
      return True
    else:
      return False
  
  def _fixingForm(self, what):
    self.browser.clickElement(By.XPATH, SubmitForms.BUTTON_FIX.value.format(what=what))
    result = self.browser.catchError(By.XPATH, SubmitForms.ERROR_NOTICE.value)
    self._logger.info(result)
    if("sikeresen megtörtént" in result):
      return True
    else:
      return False
  
  def _saveForm(self):
    self.browser.clickElement(By.XPATH, SubmitForms.BUTTON_SAVE.value)
    result = self.browser.catchError(By.XPATH, SubmitForms.ERROR_NOTICE.value)
    self._logger.info(result)
    if("sikeresen megtörtént" in result):
      return True
    else:
      return False