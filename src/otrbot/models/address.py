from dataclasses import dataclass

@dataclass
class Address:
  """
  Represents a physical address.

  Attributes:
    postal_code (str): The postal code of the address.
    city (str): The city of the address.
    street (str): The street of the address.
    house_number (str): The house number of the address.
    region (str): The region of the address.
  """
  postal_code: str
  city: str  
  street: str
  house_number: str
  region: str
