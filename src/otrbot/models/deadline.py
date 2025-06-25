from dataclasses import dataclass

@dataclass
class Deadline:
  """
  Represents a deadline for a specific process.

  Attributes:
    claim_submission_date (str): Igény benyújtásának dátuma.
    decision_date (str): Támogatási döntés dátuma
    decision_support_begin (str): A támogatás felhasználásának kezdete.
    decision_support_finish (str): A támogatás felhasználásának befejezése.
    contract_entry_date (str): A támogatási jogviszony hatálybalépésének dátuma.
  """

  claim_submission_date: str
  decision_date: str
  decision_support_begin: str
  decision_support_finish: str
  contract_entry_date: str