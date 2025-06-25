import logging
import unidecode
from enum import Enum
from otrbot.models import SupportSearchTable
from selenium.webdriver.common.by import By
from typing import List

class FillSupportList(Enum):
  INPUT_KID = "//input[@id='konstrukcio_azonosito']"
  INPUT_TAX = "//input[@id='igenylo_adoszam']"
  INPUT_TAZ = "//input[@id='tamogatas_azonosito']"
  SELECT_STATUS = "//select[@id='statusz']"
  # SELECT_STATUS = f"//select[@id='statusz']/option[{i}]"
  # SELECT_STATUS = f"/html/body/div[7]/div[3]/div/form/div/div/div/div/div/div/div/ui-view/ng-form/div/div[2]/fieldset/div[1]/div/select/option[{i}]"
  BUTTON_SEARCH = "//button[@id='keresesBtn']"
  GRID = "//div[@role='grid']/div[2]/div"
  ITEMS_PER_PAGE = "//select[@id='itemsPerPage']"
  ITEMS_PER_PAGE_VALUE = "//select[@id='itemsPerPage']/option[4]"
  CLICK_ID = "//*[@id='{clickId}']/div/span[2]/span/ng-transclude/i"
  STATUS = (
    "Vázlat",
    "Benyújtott",
    "Döntött",
    "Szerződött",
    "Lezárt - teljesült",
    "Lezárt - nem teljesült",
    "Technikai törölt",
    "Technikai lezárt"
  )  


class SupportListService:
  def __init__(self, browser):
    self._browser = browser
    self._logger = logging.getLogger()

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self._logger.debug("The support list search is done")
  
  def selectCouncilOnSearchForm(self, kid, council, otrid, status) -> bool:
    self._browser.sendKeys(By.XPATH, FillSupportList.INPUT_TAZ.value, otrid)
    self._browser.clickElement(By.XPATH, FillSupportList.BUTTON_SEARCH.value)   
    rows = self._browser.findGridElementRows()
    rowlist = []
    for row in rows:
      cols = row.find_elements(By.XPATH, ".//div[@role='gridcell']")
      collist = [{
        'id': col.get_attribute('id'),
        'title': col.find_element(By.XPATH, ".//div").text
      } for col in cols]            
      rowlist.append(SupportSearchTable(collist=collist))
    clickId = self._getClickId(rows=rowlist, council=council, status=FillSupportList.STATUS.value[status])
    self._logger.debug(f"{council} : {FillSupportList.STATUS.value[status]}")
    if(clickId):
      self._browser.clickElement(By.XPATH, FillSupportList.CLICK_ID.value.format(clickId=clickId))
      self._logger.debug(f"{council} : {clickId}")
      return True
    return False
  
  def _getClickId(self, rows: List[SupportSearchTable], council: str, status: str):
    for row in rows:
      council_accentless = unidecode.unidecode(council.lower()).split(' ')
      claimname_accentlesses = unidecode.unidecode(row.claim_name.lower()).split(' ')
      self._logger.debug(f"extracted name: {council_accentless} from {claimname_accentlesses}")
      if (council_accentless[0] in claimname_accentlesses and row.support_status.lower() == status.lower()):                
        return row.id
    return None