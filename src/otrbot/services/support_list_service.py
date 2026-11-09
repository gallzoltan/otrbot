import logging
import re
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
    row = self._findRow(rows=rowlist, council=council, status=FillSupportList.STATUS.value[status], regid=regid, otrid=otrid)
    self._logger.debug(f"{council} : {FillSupportList.STATUS.value[status]}")
    if(row):
      self._browser.clickElement(By.XPATH, FillSupportList.CLICK_ID.value.format(clickId=row.id))
      self._logger.debug(f"{council} : {row.id} otrid:{row.otrid}")
      return row
    return None
  
  def _getClickId(self, rows: List[SupportSearchTable], council: str, status: str):
    row = self._findRow(rows=rows, council=council, status=status)
    return row.id if row else None

  def _findRow(self, rows: List[SupportSearchTable], council: str, status: str, regid: str = "", otrid: str = "") -> Optional[SupportSearchTable]:
    """
    Picks the grid row of the item. The tax number / OTR id and the status decide; the applicant name
    (e.g. 'Sarudi Községi Önkormányzat' for Sarud) is only used to choose between several candidates.
    """
    tax_prefix = self._digits(regid)[:8]
    otrid = str(otrid or "").strip()
    candidates = []
    for row in rows:
      self._logger.debug(f"{council} : candidate {row.otrid} '{row.claim_name}' {row.support_status} {row.tax_number}")
      if row.support_status.lower() != status.lower():
        continue
      if tax_prefix and not self._digits(row.tax_number).startswith(tax_prefix):
        continue
      if otrid and str(row.otrid).strip() != otrid:
        continue
      candidates.append(row)
    if not candidates:
      return None
    for row in candidates:
      if self._nameMatches(council, row.claim_name):
        return row
    if len(candidates) == 1 and (tax_prefix or otrid):
      row = candidates[0]
      self._logger.warning(f"{council}: az OTR-beli igénylő neve eltér: '{row.claim_name}', elfogadva adószám/OTR azonosító alapján")
      return row
    self._logger.error(f"{council}: {len(candidates)} találat, egyik igénylő neve sem illik a településhez")
    return None

  @staticmethod
  def _tokens(text) -> List[str]:
    return re.findall(r"[a-z0-9]+", unidecode.unidecode(str(text or "")).lower())

  @classmethod
  def _nameMatches(cls, council: str, name: str) -> bool:
    """True if the first word of the council is a word of the name, allowing an adjective suffix (Sarud -> Sarudi)."""
    council_tokens = cls._tokens(council)
    if not council_tokens:
      return False
    first = council_tokens[0]
    return any(token.startswith(first) and len(token) - len(first) <= 2 for token in cls._tokens(name))

  @staticmethod
  def _digits(value) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())
