from dataclasses import dataclass

@dataclass
class Amount:
  """
  Represents the amount datas.

  Attributes:
    claim_sum (str): Igényelt támogatás öszege (HUF)
    claim_sum_content (str): Igényelt támogatás támogatástartalma (HUF)
    decision_all_cost (str): A felhasználni tervezett összes költség (HUF)
    decision_cost (str): Összes elszámolható költség (HUF)
    decision_awarded_sum (str): A Támogató által odaítélt teljes támogatási összeg (HUF)
    decision_own_source (str): A vállalt saját forrás teljes összege (HUF)
    decision_other_sum (str): Más támogatók által biztosított támogatás teljes összege (HUF)
    decision_sum_content (str): Biztosított támogatás támogatástartalma (HUF)
  """

  claim_sum: str
  claim_sum_content: str
  decision_all_cost: str
  decision_cost: str
  decision_awarded_sum: str
  decision_own_source: str
  decision_other_sum: str
  decision_sum_content: str