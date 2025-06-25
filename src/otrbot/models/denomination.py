from dataclasses import dataclass

@dataclass
class Denomination:
  """
  Represents a denomination with a name.

  Attributes:
    claim_name (str): Támogatás/projekt megnevezése.
    claim_source_name (str): A támogatás forrásának megnevezése.
    claim_summary (str): Támogatás/Projekt rövid összefoglalója.
    claim_goal (str): Támogatási igény célja.
  """
  
  claim_name: str
  claim_source_name: str
  claim_summary: str
  claim_goal: str
