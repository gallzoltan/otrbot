import logging
from enum import Enum
from selenium.webdriver.common.by import By
from otrbot.constants import Categories
from otrbot.models import Amount, Deadline, Master, Address

class ConstantDecision(Enum):
  # Support basic
  INPUT_D_DATE = "//input[@id='dontes_datum']"
  INPUT_SUP_BEGIN = "//input[@id='dontes_felhasznalasKezdete']"
  INPUT_SUP_END = "//input[@id='dontes_felhasznalasVege']"
  INPUT_DEC_SUM_AMOUNT = "//input[@id='dontes_tervezettKoltseg']"
  INPUT_SUM_AMOUNT = "//input[@id='dontes_elszamolhatoKoltseg']"
  INPUT_AWARD_AMMOUNT = "//input[@id='dontes_megiteltOsszeg']"
  INPUT_AWARD_AMMOUNT_CONTENT = "//input[@id='dontes_megiteltTamogatasTartalom']"
  INPUT_OWN_SOURCE = "//input[@id='dontes_sajatForras']"
  INPUT_INTERMEDIARY_ORG = "//input[@id='dontes_kozvetitoNev']"
  INPUT_OTHER_AMOUNT = "//input[@id='dontes_megiteltTamogatasOsszegMas']"
  
  # Support decision
  BUTTON_SELECT_D = "//button[@id='donteshozo.tkkivonat.donteshozoLista[0]:kivalasztas']"
  
  # Support category
  BUTTON_CATEGORY_NEW = "//button[@id='dontes.tamkat_kategoria:rogzites']"
  # SEARCH_DECISION_OPEN = "//*[@id='dontes.tamkat_kategoria[0].idTamogatasiKategoria:select_single']"
  SEARCH_DECISION_OPEN = (
    "//*[@id='dontes.tamkat_kategoria[0].idTamogatasiKategoria:select_single']",
    "//*[@id='dontes.tamkat_kategoria[1].idTamogatasiKategoria:select_single']",
    "//*[@id='dontes.tamkat_kategoria[2].idTamogatasiKategoria:select_single']",
    "//*[@id='dontes.tamkat_kategoria[3].idTamogatasiKategoria:select_single']",
    "//*[@id='dontes.tamkat_kategoria[4].idTamogatasiKategoria:select_single']",
    "//*[@id='dontes.tamkat_kategoria[5].idTamogatasiKategoria:select_single']"
  )
  # SEARCH_DECISION_INPUT = "/html/body/div[13]/div/div/div[2]/ng-form/div/select"
  SEARCH_DECISION_INPUT = (
    "/html/body/div[13]/div/div/div[2]/ng-form/div/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[2]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[3]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[4]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[5]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[6]/select"
  )
  SEARCH_DECISION_COLSE = "//button[@id='popupSelectBtn']"
  # SELECT_DECISION_FORMAT = "//select[@id='dontes.tamkat_kategoria[0].idTamogatasiForma']"
  SELECT_DECISION_FORMAT = (
    "//select[@id='dontes.tamkat_kategoria[0].idTamogatasiForma']",
    "//select[@id='dontes.tamkat_kategoria[1].idTamogatasiForma']",
    "//select[@id='dontes.tamkat_kategoria[2].idTamogatasiForma']",
    "//select[@id='dontes.tamkat_kategoria[3].idTamogatasiForma']",
    "//select[@id='dontes.tamkat_kategoria[4].idTamogatasiForma']",
    "//select[@id='dontes.tamkat_kategoria[5].idTamogatasiForma']"
  )
  # SELECT_DECISION_REGIO = "//select[@id='dontes.tamkat_kategoria[0].idRegio']"
  SELECT_DECISION_REGIO = (
    "//select[@id='dontes.tamkat_kategoria[0].idRegio']",
    "//select[@id='dontes.tamkat_kategoria[1].idRegio']",
    "//select[@id='dontes.tamkat_kategoria[2].idRegio']",
    "//select[@id='dontes.tamkat_kategoria[3].idRegio']",
    "//select[@id='dontes.tamkat_kategoria[4].idRegio']",
    "//select[@id='dontes.tamkat_kategoria[5].idRegio']"
  )
  # INPUT_DECISION_AMOUNT = "//*[@id='dontes.tamkat_kategoria[0].tamogatasTartalom']"
  INPUT_DECISION_AMOUNT = (
    "//*[@id='dontes.tamkat_kategoria[0].tamogatasTartalom']",
    "//*[@id='dontes.tamkat_kategoria[1].tamogatasTartalom']",
    "//*[@id='dontes.tamkat_kategoria[2].tamogatasTartalom']",
    "//*[@id='dontes.tamkat_kategoria[3].tamogatasTartalom']",
    "//*[@id='dontes.tamkat_kategoria[4].tamogatasTartalom']",
    "//*[@id='dontes.tamkat_kategoria[5].tamogatasTartalom']"
  )


class DecisionService:
  def __init__(self, browser):
    self._browser = browser
    self._const = ConstantDecision
    self._logger = logging.getLogger()
  
  def __enter__(self):
    return self
  
  def __exit__(self, *args):
    self._logger.debug("The Decission done")
  
  def fillDecisionBasicTab(self, deadline: Deadline, amount: Amount):
    self._browser.sendKeys(By.XPATH, self._const.INPUT_D_DATE.value, deadline.decision_date)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_SUP_BEGIN.value, deadline.decision_support_begin)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_SUP_END.value, deadline.decision_support_finish)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_DEC_SUM_AMOUNT.value, amount.decision_all_cost)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_SUM_AMOUNT.value, amount.decision_cost)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_AWARD_AMMOUNT.value, amount.decision_awarded_sum)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_OWN_SOURCE.value, amount.decision_own_source)
    # if(decision_basic.intermediary_org != '-'):
    #   self._browser.sendKeys(By.XPATH, self._const.INPUT_INTERMEDIARY_ORG, decision_basic.intermediary_org)
    self._browser.sendKeys(By.XPATH, self._const.INPUT_OTHER_AMOUNT.value, amount.decision_other_sum)
  
  def fillDecisionTab(self):
    self._browser.clickElement(By.XPATH, self._const.BUTTON_SELECT_D.value)
  
  def fillDecisionCategoryTab(self, master: Master, address: Address, amount: Amount):
    cat_list = [x.strip() for x in master.category.split(";") if x.strip()]
    for i, cats in enumerate(cat_list):
      self._browser.clickElement(By.XPATH, self._const.BUTTON_CATEGORY_NEW.value)
      self._browser.clickElement(By.XPATH, self._const.SEARCH_DECISION_OPEN.value[i])
      for index, c in enumerate(self._split_by_dots(cats)):
        self._browser.selectOption(By.XPATH, self._const.SEARCH_DECISION_INPUT.value[index], Categories.CAT_TITLES.value[c])
      self._browser.clickElement(By.XPATH, self._const.SEARCH_DECISION_COLSE.value)
      self._browser.selectOption(By.XPATH, self._const.SELECT_DECISION_FORMAT.value[i], master.form)
      self._browser.selectOption(By.XPATH, self._const.SELECT_DECISION_REGIO.value[i], address.region)
      self._browser.sendKeys(By.XPATH, self._const.INPUT_DECISION_AMOUNT.value[i], amount.claim_sum_content)
  
  def _split_by_dots(self, s):
    res = []
    for i in range(len(s)):
      if s[i] == ".":
        res.append(s[:i+1])
    return tuple(res)