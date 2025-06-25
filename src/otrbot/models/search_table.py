class SupportSearchTable:
  def __init__(self, collist: list):
    for i in range(len(collist)):
      if(i==8): self.id = collist[i]["id"]
      if(i==1): self.support_name = collist[i]["title"] 
      if(i==2): self.support_status = collist[i]["title"]
      if(i==3): self.decision_date = collist[i]["title"]
      if(i==4): self.claim_name = collist[i]["title"]
      if(i==5): self.constuct_name = collist[i]["title"]
      if(i==6): self.exclusion = collist[i]["title"]