import pytest
from otrbot.services.decision_service import DecisionService

@pytest.fixture
def service():
  return DecisionService(browser=None)

@pytest.mark.parametrize("cat_list, expected_result", [
  ("4.1.1.", ('4.', '4.1.', '4.1.1.')),
  ("4.1.1. Általános csekély összegű (de minimis) támogatás nem közúti árufuvarozó részére", ('4.', '4.1.', '4.1.1.')),
  ("9.2.", ('9.', '9.2.')),
  ("9.4.", ('9.', '9.4.')),
  ("18. Nem állami támogatás", ('18.',)),
  ("18.", ('18.',)),
])

def test_split_by_dots(service, cat_list, expected_result):
  '''
    Test the _split_by_dots() method
    master.category = "4.1.1.; 9.2.; 9.4.;18."
    cat_list = [x.strip() for x in master.category.split(";") if x.strip()]
  '''
  assert service._split_by_dots(cat_list) == expected_result  