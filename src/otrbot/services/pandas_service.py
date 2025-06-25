import pandas as pd
import logging
from otrbot.models import Master
from otrbot.models import Address
from otrbot.models import Denomination
from otrbot.models import Deadline
from otrbot.models import Amount
from otrbot.models import Stack

logger = logging.getLogger()

def read_excel_file(excel_file, sheet_name) -> Stack:
  """
  Reads an Excel file and returns a Stack object containing Master objects.

  Parameters:
  excel_file (str): The path to the Excel file.
  sheet_name (str): The name of the sheet to read from.

  Returns:
  Stack: A Stack object containing Master objects.

  """

  masters = []
  addresses = []
  denominations = []
  deadlines = []
  amounts = []
  df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=1) 
  df = df.fillna('') 
  df = df.astype({
    'kid':'string', 
    'regid':'string',
    'otrid':'string',
    'postal_code':'string',  
    'house_number':'string',
    'aht':'string',
    'claim_submission_date':'string',
    'decision_date':'string',
    'decision_support_begin':'string',
    'decision_support_finish':'string',
    'contract_entry_date':'string',    
    'claim_sum': 'string',
    'claim_sum_content': 'string',
    'decision_all_cost':'string',
    'decision_cost':'string',
    'decision_awarded_sum':'string',
    'decision_own_source':'string',
    'decision_other_sum':'string',
    'decision_sum_content':'string'               
  })
  for row in df.itertuples(index=False):
    master = Master(rowid=row.rowid, kid=row.kid, regid=row.regid, otrid=row.otrid, aht=row.aht, form=row.form, category=row.category)
    address = Address(postal_code=row.postal_code, city=row.city, street=row.street, house_number=row.house_number, region=row.region)
    denomination = Denomination(claim_name=row.claim_name, claim_source_name=row.claim_source_name, claim_summary=row.claim_summary, claim_goal=row.claim_goal)
    deadline = Deadline(claim_submission_date=row.claim_submission_date, decision_date=row.decision_date, decision_support_begin=row.decision_support_begin, decision_support_finish=row.decision_support_finish, contract_entry_date=row.contract_entry_date)
    amount = Amount(claim_sum=row.claim_sum, claim_sum_content=row.claim_sum_content, decision_all_cost=row.decision_all_cost, decision_cost=row.decision_cost, decision_awarded_sum=row.decision_awarded_sum, decision_own_source=row.decision_own_source, decision_other_sum=row.decision_other_sum, decision_sum_content=row.decision_sum_content)
    masters.append(master)
    addresses.append(address)
    denominations.append(denomination)
    deadlines.append(deadline)
    amounts.append(amount)
  return Stack(masters, addresses, denominations, deadlines, amounts)