from dataclasses import dataclass
from typing import List
from . import Master
from . import Address
from . import Denomination
from . import Deadline
from . import Amount

@dataclass
class Stack:
  """
  Represents a stack data structure.
  
  Attributes:
    masters (List[Master]): Törzs adatok.
    addresses (List[Address]): Cím adatok.
    denominations (List[Denomination]): Elnevezések az űrlapokon.
    deadlines (List[Deadline]): Határidők.
    amounts (List[Amount]): Összegek.
  """
  
  masters: List[Master]
  addresses: List[Address]
  denominations: List[Denomination]
  deadlines: List[Deadline]
  amounts: List[Amount]