import pytest
from otrbot.services.support_list_service import SupportListService
from otrbot.models.search_table import SupportSearchTable

@pytest.fixture
def service():
  return SupportListService(browser=None)

def test_get_cell_id(service):
  row = [
    {"id": "0", "title": "title"},
    {"id": "1", "title": "support_name"},
    {"id": "2", "title": "Benyújtott"},
    {"id": "3", "title": "decision_date"},
    {"id": "4", "title": "Békéscsaba Megyei Jogú Város Önkormányzata"},
    {"id": "5", "title": "constuct_name"},
    {"id": "6", "title": "exclusion"},
    {"id": "7", "title": "title7"},
    {"id": "id1234", "title": "clickId"}
  ]
  rowlist = []
  rowlist.append(SupportSearchTable(collist=row))
  assert service._getClickId(rows=rowlist, council="Békéscsaba", status="Benyújtott") == "id1234"
def grid_row(otrid, name, status, tax):
  cells = [otrid, "A települési...", status, "", name, tax, "konstrukció", "Nem", ""]
  return SupportSearchTable(collist=[{"id": f"cell{i}" if i < 8 else f"click-{otrid}", "title": t} for i, t in enumerate(cells)])

def test_search_table_columns():
  row = grid_row("14846/02/2026", "Aba Város Önkormányzata", "Benyújtott", "15727361-2-07")
  assert row.otrid == "14846/02/2026"
  assert row.tax_number == "15727361-2-07"
  assert row.construct_name == "konstrukció"
  assert row.id == "click-14846/02/2026"

def test_find_row_by_tax_number(service):
  rows = [
    grid_row("1/2026", "Aba Város Önkormányzata", "Benyújtott", "11111111-2-07"),
    grid_row("2/2026", "Aba Város Önkormányzata", "Benyújtott", "15727361-2-07"),
  ]
  assert service._findRow(rows=rows, council="Aba", status="Benyújtott", regid="15727361").otrid == "2/2026"
  assert service._findRow(rows=rows, council="Aba", status="Döntött", regid="15727361") is None
  assert service._findRow(rows=rows, council="Aba", status="Benyújtott", regid="99999999") is None
