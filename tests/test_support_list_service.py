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

def test_find_row_adjective_name(service):
  rows = [grid_row("1/2026", "Sarudi Községi Önkormányzat", "Benyújtott", "15380573-2-10")]
  assert service._findRow(rows=rows, council="Sarud", status="Benyújtott", regid="15380573").otrid == "1/2026"
  assert service._findRow(rows=rows, council="Sarudi", status="Benyújtott", regid="15380573").otrid == "1/2026"
  assert service._getClickId(rows=rows, council="Sarud", status="Benyújtott") == "click-1/2026"

def test_name_matches():
  assert SupportListService._nameMatches("Tahitótfalu", "Tahitótfalui Közös Önkormányzati Hivatal")
  assert SupportListService._nameMatches("Pécs", "Pécs Megyei Jogú Város Önkormányzata")
  assert not SupportListService._nameMatches("Pécs", "Pécsudvardi Önkormányzat")
  assert not SupportListService._nameMatches("Aba", "Abaliget Község Önkormányzata")

def test_find_row_single_tax_match_with_other_name(service, caplog):
  rows = [grid_row("1/2026", "Egri Polgármesteri Hivatal", "Benyújtott", "15729000-2-10")]
  with caplog.at_level("WARNING"):
    assert service._findRow(rows=rows, council="Eger", status="Benyújtott", regid="15729000").otrid == "1/2026"
  assert "eltér" in caplog.text

def test_find_row_ambiguous_without_name_match(service):
  rows = [
    grid_row("1/2026", "'kehtj' tqw uv", "Benyújtott", "15333825-2-03"),
    grid_row("2/2026", "Másik Hivatal", "Benyújtott", "15333825-2-03"),
  ]
  assert service._findRow(rows=rows, council="Kátoly", status="Benyújtott", regid="15333825") is None
  assert service._findRow(rows=rows[:1], council="Kátoly", status="Benyújtott", regid="15333825").otrid == "1/2026"

def test_find_row_by_otrid(service):
  rows = [
    grid_row("16289/01971/00/2026", "Sarudi Községi Önkormányzat", "Döntött", "15380573-2-10"),
    grid_row("16289/01972/00/2026", "Sarudi Községi Önkormányzat", "Döntött", "15380573-2-10"),
  ]
  assert service._findRow(rows=rows, council="Sarud", status="Döntött", otrid="16289/01972/00/2026 ").otrid == "16289/01972/00/2026"
  assert service._findRow(rows=rows, council="Sarud", status="Döntött", otrid="16289/09999/00/2026") is None
