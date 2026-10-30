import logging
import unidecode
from enum import Enum
from otrbot.models import SupportSearchTable
from selenium.webdriver.common.by import By
from typing import List, Optional

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
  
  def selectCouncilOnSearchForm(self, kid, council, otrid, status, regid="") -> Optional[SupportSearchTable]:
    """
    Searches by OTR id, or - when it is not known yet - by construction id and tax number,
    then opens the matching row. Returns the opened row (its otrid is the OTR id) or None.
    """
    if otrid:
      self._browser.sendKeys(By.XPATH, FillSupportList.INPUT_TAZ.value, otrid)
    else:
      self._browser.sendKeys(By.XPATH, FillSupportList.INPUT_KID.value, kid)
      self._browser.sendKeys(By.XPATH, FillSupportList.INPUT_TAX.value, regid)
    self._browser.clickElement(By.XPATH, FillSupportList.BUTTON_SEARCH.value)   
    rows = self._browser.readGrid()
    if not rows:
      self._logger.error(f"{council} : empty search result for otrid:{otrid} kid:{kid} regid:{regid}")
      return None
    rowlist = [SupportSearchTable(collist=collist) for collist in rows]
    row = self._findRow(rows=rowlist, council=council, status=FillSupportList.STATUS.value[status], regid=regid)
    self._logger.debug(f"{council} : {FillSupportList.STATUS.value[status]}")
    if(row):
      self._browser.clickElement(By.XPATH, FillSupportList.CLICK_ID.value.format(clickId=row.id))
      self._logger.debug(f"{council} : {row.id} otrid:{row.otrid}")
      return row
    return None
  
  def _getClickId(self, rows: List[SupportSearchTable], council: str, status: str):
    row = self._findRow(rows=rows, council=council, status=status)
    return row.id if row else None

  def _findRow(self, rows: List[SupportSearchTable], council: str, status: str, regid: str = "") -> Optional[SupportSearchTable]:
    council_accentless = unidecode.unidecode(council.lower()).split(' ')
    tax_prefix = self._digits(regid)[:8]
    for row in rows:
      claimname_accentlesses = unidecode.unidecode(row.claim_name.lower()).split(' ')
      self._logger.debug(f"extracted name: {council_accentless} from {claimname_accentlesses}")
      if tax_prefix and not self._digits(row.tax_number).startswith(tax_prefix):
        continue
      if (council_accentless[0] in claimname_accentlesses and row.support_status.lower() == status.lower()):                
        return row
    return None

  @staticmethod
  def _digits(value) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())
