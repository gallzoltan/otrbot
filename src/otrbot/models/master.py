from dataclasses import dataclass

@dataclass
class Master:
  """
  Represents a master object.

  Attributes:
    rowid (int): Sorszám.
    kid (str): Konstrukció azonosító.
    regid (str): Törzs szám (adószám).
    otrid (str): OTR azoonosító.
    aht (str): Államháztartási azonosító.
    category (str): Biztosított támogatás kategóriája.
    activity (str, optional): Tevékenység. Defaults to 'Általános közigazgatás'.
    form (str, optional): Támogatási forma. Defaults to 'Vissza nem térítendő pénzeszköz'.
  """

  rowid: int
  kid: str
  regid: str
  otrid: str
  aht: str
  category: str
  activity: str = 'Általános közigazgatás'
  form: str = 'Vissza nem térítendő pénzeszköz'