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