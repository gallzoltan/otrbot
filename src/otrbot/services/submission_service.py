import logging
from enum import Enum
from selenium.webdriver.common.by import By
from otrbot.constants import Categories
from otrbot.models import Master, Denomination, Deadline, Amount, Address


class ConstantSubmission(Enum):
  CHECKBOX_CLAIM_COUNTRY_ID = "felhasznalasHelyszinek.orszagosFejlesztes"
  # SUPPORTER_BM = "Belügyminisztérium Önkormányzati Államtitkárság (09)"
  # SUPPORTER_KTM = "Közigazgatási és Területfejlesztési Minisztérium (2023.12.31-ig BMÖÁ) (09)"
  SUPPORTER = {
    "BM": "Belügyminisztérium Önkormányzati Államtitkárság (09)",
    "KTM": "Közigazgatási és Területfejlesztési Minisztérium (2023.12.31-ig BMÖÁ) (09)"
  }

  ''' Basic data TAB '''
  RADIO_CLASSIFICATIONS = (    
    "//input[@id='igenylo_alapadatok_besorolas_0']",
    "//input[@id='igenylo_alapadatok_besorolas_1']",
    "//input[@id='igenylo_alapadatok_besorolas_2']",
    "//input[@id='igenylo_alapadatok_besorolas_3']",
  )
  POPUP_SEARCH_FOR_TAX =  "//*[@id='belfoldi_jogiszemely_addon']"
  POPUP_INPUT_SEARCH_TAX = "//input[@id='adoszam']"
  POPUP_BUTTON_SEARCH = "//button[@id='keresesBtn']"
  POPUP_GRID_CLICK = "//div[contains(@id, '-grid-container')]/div[2]/div/div/div"
  POPUP_BUTTON_SELECT = "//button[@id='igenylo_kereses_popup:kivalasztas']"
  
  ''' Claim TAB '''
  SEARCH_FOR_KID = "//*[@id='tk_kereses_addon']"
  INPUT_KID = "//input[@id='tkazonosito']"
  BUTTON_SERACH_KID = "//button[@id='keresesBtn']"
  GRID_CLICK_KID = "//div[contains(@id, '-grid-container')]/div[2]/div/div/div"
  BUTTON_SELECT_KID = "//button[@id='tk_kereses_popup:kivalasztas']" 
  INPUT_CLAIM_NAME = "//input[@id='igenyles_alapadatok_megnevezes']"
  INPUT_CLAIM_DATE = "//input[@id='benyujtas_datum']"
  INPUT_CLAIM_SUMMARY = "//input[@id='igenyles_alapadatok_osszefoglalas']"
  SELECT_CLAIM_SUPPORTER = "//select[@id='igenyles.idTamogato']" # Belügyminisztérium Önkormányzati Államtitkárság (09) | Közigazgatási és Területfejlesztési Minisztérium (2023.12.31-ig BMÖÁ) (09)  
  INPUT_CLAIM_AMOUNT = "//input[@id='igeny_alapadatok_osszeg']"
  INPUT_CLAIM_GOAL = "//input[@id='igeny_alapadatok_cel']"
  INPUT_CLAIM_SCOPE = "//div[@id='teaor']/div/input" 
  INPUT_CLAIM_SOURCE = "//div[@id='tamogatas_forrasok']/div/input"  
  
  ''' Place of use TAB '''
  CHECKBOX_CLAIM_PLACE = "//input[@id='felhasznalasHelyszinek.helyseghezKotott']"
  CHECKBOX_CLAIM_COUNTRY = "//input[@id='felhasznalasHelyszinek.orszagosFejlesztes']"
  BUTTON_CLAIM_PLACE_NEW = "//button[@id='tamogatasi_igeny_rogzites:felhasznalasiHelyszinHozzaadas']"
  INPUT_CLAIM_ADDRESS_COUNCIL = "//input[@id='cimblock_varos_igenyles_felh_helyszin_cimadatok_cimBlokk_0']"
  INPUT_CLAIM_ADDRESS_STREET = "//input[@id='cimblock_kozterulet_igenyles_felh_helyszin_cimadatok_cimBlokk_0']"
  INPUT_CLAIM_ADDRESS_HOUSE = "//*[@id='cimblock_hazszam_igenyles_felh_helyszin_cimadatok_cimBlokk_0']"
  INPUT_CLAIM_ADDRESS_IRSZ = "//*[@id='cimblock_iranyitoszam_igenyles_felh_helyszin_cimadatok_cimBlokk_0']"
  
  ''' Supports and Categories '''
  BUTTON_CLAIM_SUPPORT_NEW = "//button[@id='igenyles.tamkat_kategoria:rogzites']"
  SEARCH_CLAIM_CATEGORY_OPEN = (
    "//*[@id='igenyles.tamkat_kategoria[0].idTamogatasiKategoria:select_single']",
    "//*[@id='igenyles.tamkat_kategoria[1].idTamogatasiKategoria:select_single']",
    "//*[@id='igenyles.tamkat_kategoria[2].idTamogatasiKategoria:select_single']",
    "//*[@id='igenyles.tamkat_kategoria[3].idTamogatasiKategoria:select_single']",
    "//*[@id='igenyles.tamkat_kategoria[4].idTamogatasiKategoria:select_single']",
    "//*[@id='igenyles.tamkat_kategoria[5].idTamogatasiKategoria:select_single']",
  )
  SEARCH_CLAIM_CATEGORY_INPUT = (
    "/html/body/div[13]/div/div/div[2]/ng-form/div/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[2]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[3]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[4]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[5]/select",
    "/html/body/div[13]/div/div/div[2]/ng-form/div[6]/select"
  )
  SEARCH_CLAIM_CATEGORY_CLOSE = "//button[@id='popupSelectBtn']"
  SELECT_CLAIM_SUPPORT_FORMAT = (
    "//select[@id='igenyles.tamkat_kategoria[0].idTamogatasiForma']",
    "//select[@id='igenyles.tamkat_kategoria[1].idTamogatasiForma']",
    "//select[@id='igenyles.tamkat_kategoria[2].idTamogatasiForma']",
    "//select[@id='igenyles.tamkat_kategoria[3].idTamogatasiForma']",
    "//select[@id='igenyles.tamkat_kategoria[4].idTamogatasiForma']",
    "//select[@id='igenyles.tamkat_kategoria[5].idTamogatasiForma']"
  )
  SELECT_CLAIM_SUPPORT_REGIO = (
    "//select[@id='igenyles.tamkat_kategoria[0].idRegio']",
    "//select[@id='igenyles.tamkat_kategoria[1].idRegio']",
    "//select[@id='igenyles.tamkat_kategoria[2].idRegio']",
    "//select[@id='igenyles.tamkat_kategoria[3].idRegio']",
    "//select[@id='igenyles.tamkat_kategoria[4].idRegio']",
    "//select[@id='igenyles.tamkat_kategoria[5].idRegio']"
  )
  INPUT_CLAIM_SUPPORT_AMOUNT = (
    "//input[@id='igenyles.tamkat_kategoria[0].tamogatasTartalom']",
    "//input[@id='igenyles.tamkat_kategoria[1].tamogatasTartalom']",
    "//input[@id='igenyles.tamkat_kategoria[2].tamogatasTartalom']",
    "//input[@id='igenyles.tamkat_kategoria[3].tamogatasTartalom']",
    "//input[@id='igenyles.tamkat_kategoria[4].tamogatasTartalom']",
    "//input[@id='igenyles.tamkat_kategoria[5].tamogatasTartalom']",
  )  


class SubmissionService:
  def __init__(self, browser):
    self._browser = browser
    self._logger = logging.getLogger()
  
  def __enter__(self):
    return self
 
  def __exit__(self, *args):
    self._logger.debug("The submission has been filled")
  
  def fillClaimingBasicTab(self, master): 
    self._browser.clickElement(By.XPATH, ConstantSubmission.RADIO_CLASSIFICATIONS.value[0]) 
    self._browser.clickElement(By.XPATH, ConstantSubmission.POPUP_SEARCH_FOR_TAX.value)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.POPUP_INPUT_SEARCH_TAX.value, master.regid)
    self._browser.clickElement(By.XPATH, ConstantSubmission.POPUP_BUTTON_SEARCH.value)
    self._browser.clickElement(By.XPATH, ConstantSubmission.POPUP_GRID_CLICK.value)
    self._browser.clickElement(By.XPATH, ConstantSubmission.POPUP_BUTTON_SELECT.value) 
  
  def fillClaimBasicTab(self, supporter:str, master: Master, denomination: Denomination, deadline: Deadline, amount: Amount):    
    self._browser.clickElement(By.XPATH, ConstantSubmission.SEARCH_FOR_KID.value)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_KID.value, master.kid)
    self._browser.clickElement(By.XPATH, ConstantSubmission.BUTTON_SERACH_KID.value)
    self._browser.clickElement(By.XPATH, ConstantSubmission.GRID_CLICK_KID.value)
    self._browser.clickElement(By.XPATH, ConstantSubmission.BUTTON_SELECT_KID.value)

    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_SOURCE.value, denomination.claim_source_name[0:50])
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_SCOPE.value, master.activity) 
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_NAME.value, denomination.claim_name)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_DATE.value, deadline.claim_submission_date)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_SUMMARY.value, denomination.claim_summary)
    # self._browser.selectOption(By.XPATH, ConstantSubmission.SELECT_CLAIM_SUPPORTER.value, ConstantSubmission.SUPPORTER_BM.value if supporter == 'BM' else ConstantSubmission.SUPPORTER_KTM.value)     
    self._browser.selectOption(By.XPATH, ConstantSubmission.SELECT_CLAIM_SUPPORTER.value, ConstantSubmission.SUPPORTER.value[supporter]) 
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_AMOUNT.value, amount.claim_sum)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_GOAL.value, denomination.claim_goal)
  
  def fillClaimPlaceOfUseTab(self, address: Address):
    if(self._browser.is_checked(ConstantSubmission.CHECKBOX_CLAIM_COUNTRY_ID.value)):
      self._browser.clickElement(By.XPATH, ConstantSubmission.CHECKBOX_CLAIM_COUNTRY.value)        
    self._browser.clickElement(By.XPATH, ConstantSubmission.CHECKBOX_CLAIM_PLACE.value)
    self._browser.clickElement(By.XPATH, ConstantSubmission.BUTTON_CLAIM_PLACE_NEW.value)
    if("Budapest" in address.city):
      self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_ADDRESS_IRSZ.value, address.postal_code) 
    else:    
      self._browser.selectBySendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_ADDRESS_COUNCIL.value, address.city)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_ADDRESS_STREET.value, address.street)
    self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_ADDRESS_HOUSE.value, address.house_number)
  
  def fillClaimSupportCategoriesTab(self, master: Master, address: Address, amount: Amount):
    cat_list = [x.strip() for x in master.category.split(";") if x.strip()]
    for i, cats in enumerate(cat_list):
      self._browser.clickElement(By.XPATH, ConstantSubmission.BUTTON_CLAIM_SUPPORT_NEW.value)
      self._browser.clickElement(By.XPATH, ConstantSubmission.SEARCH_CLAIM_CATEGORY_OPEN.value[i])
      for index, c in enumerate(self.__split_by_dots(cats)):
        self._browser.selectOption(By.XPATH, ConstantSubmission.SEARCH_CLAIM_CATEGORY_INPUT.value[index], Categories.CAT_TITLES.value[c])
      self._browser.clickElement(By.XPATH, ConstantSubmission.SEARCH_CLAIM_CATEGORY_CLOSE.value)
      self._browser.selectOption(By.XPATH, ConstantSubmission.SELECT_CLAIM_SUPPORT_FORMAT.value[i], master.form)
      self._browser.selectOption(By.XPATH, ConstantSubmission.SELECT_CLAIM_SUPPORT_REGIO.value[i], address.region)
      self._browser.sendKeys(By.XPATH, ConstantSubmission.INPUT_CLAIM_SUPPORT_AMOUNT.value[i], amount.claim_sum_content)
  
  def __split_by_dots(self, s):
    res = []
    for i in range(len(s)):
      if s[i] == ".":
        res.append(s[:i+1])
    return tuple(res)