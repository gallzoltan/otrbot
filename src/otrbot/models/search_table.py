class SupportSearchTable:
  """One row of the 'Támogatások listázása' result grid."""
  def __init__(self, collist: list):
    self.otrid = ""
    self.tax_number = ""
    for i in range(len(collist)):
      if(i==0): self.otrid = collist[i]["title"]
      if(i==1): self.support_name = collist[i]["title"]
      if(i==2): self.support_status = collist[i]["title"]
      if(i==3): self.decision_date = collist[i]["title"]
      if(i==4): self.claim_name = collist[i]["title"]
      if(i==5): self.tax_number = collist[i]["title"]
      if(i==6): self.construct_name = collist[i]["title"]
      if(i==7): self.exclusion = collist[i]["title"]
      if(i==8): self.id = collist[i]["id"]
