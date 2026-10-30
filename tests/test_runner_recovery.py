import pytest
from otrbot.journal import Journal, OK, FAILED
from otrbot.models import Master, Address, Denomination, Deadline, Amount, Stack
from otrbot.runner import ModuleRunner, FinalSubmitError, SubmittedUncertain
from otrbot.services.webdriver_service import StepFailed, StepTimings


class FakeBrowser:
  def __init__(self, notice=""):
    self.strict = True
    self.timings = StepTimings()
    self.notice = notice
    self.clicked = []

  def disableAnimations(self):
    pass

  def waitForPageIdle(self):
    return True

  def clickElement(self, how, what):
    self.clicked.append(what)
    return True

  def catchError(self, how, what):
    return self.notice


def make_stack(rowids):
  n = len(rowids)
  return Stack(
    masters=[Master(rowid=r, kid="K", regid="R", otrid=f"X{r}", aht="A", category="4.") for r in rowids],
    addresses=[Address(postal_code="1", city=f"City{r}", street="s", house_number="1", region="r") for r in rowids],
    denominations=[Denomination(claim_name="n", claim_source_name="s", claim_summary="s", claim_goal="g")] * n,
    deadlines=[Deadline(claim_submission_date="", decision_date="", decision_support_begin="", decision_support_finish="", contract_entry_date="")] * n,
    amounts=[Amount(claim_sum="", claim_sum_content="", decision_all_cost="", decision_cost="", decision_awarded_sum="", decision_own_source="", decision_other_sum="", decision_sum_content="")] * n,
  )


@pytest.fixture
def journal(tmp_path):
  j = Journal(str(tmp_path / "data.journal.sqlite"))
  yield j
  j.close()


def make_runner(journal, rowids, step, begin=None, end=None, **kwargs):
  runner = ModuleRunner(supporter="BM", journal=journal, **kwargs)
  runner.datas = make_stack(rowids)
  runner._begin, runner._end = begin, end
  runner.browser = FakeBrowser()
  runner.recovered = []
  runner._recover = lambda round, item, attempt: runner.recovered.append((item.master.rowid, attempt))
  runner._rounds[1] = step
  return runner


def test_failed_item_does_not_stop_the_run(journal):
  def step(item):
    if item.master.rowid == 2:
      raise StepFailed("element not found")
    return f"OTR-{item.master.rowid}"
  runner = make_runner(journal, [1, 2, 3], step)
  assert runner.run(1) is False
  assert journal.status(1, 1) == OK and journal.status(3, 1) == OK
  assert journal.status(2, 1) == FAILED
  assert journal.otrid(3) == "OTR-3"
  assert runner.recovered == [(2, 1), (2, 2)]

def test_retry_succeeds(journal):
  calls = []
  def step(item):
    calls.append(item.master.rowid)
    if len(calls) == 1:
      raise StepFailed("timeout")
  runner = make_runner(journal, [1], step)
  assert runner.run(1) is True
  assert calls == [1, 1]
  assert journal.is_done(1, 1)

def test_resume_skips_done_items(journal):
  journal.mark(1, 1, OK)
  processed = []
  runner = make_runner(journal, [1, 2], lambda item: processed.append(item.master.rowid))
  assert runner.run(1) is True
  assert processed == [2]

def test_begin_end_filter_on_rowid(journal):
  processed = []
  runner = make_runner(journal, [1, 2, 3, 4], lambda item: processed.append(item.master.rowid), begin=2, end=3)
  runner.run(1)
  assert processed == [2, 3]

def test_final_submit_error_is_not_retried(journal):
  calls = []
  def step(item):
    calls.append(item.master.rowid)
    raise SubmittedUncertain("RogzitesKesz: no result message after confirming")
  runner = make_runner(journal, [1], step)
  runner.run(1)
  assert calls == [1]
  assert journal.status(1, 1) == FAILED

def test_stops_after_consecutive_failures(journal):
  def step(item):
    raise StepFailed("OTR down")
  runner = make_runner(journal, [1, 2, 3, 4], step, max_attempts=1, max_consecutive_failures=2)
  runner.run(1)
  assert journal.status(2, 1) == FAILED
  assert journal.status(3, 1) is None

def test_menu_is_opened_again_after_recovery(journal):
  def step(item):
    if item.master.rowid == 1:
      raise StepFailed("boom")
  runner = make_runner(journal, [1, 2], step, max_attempts=1)
  runner._recover = lambda round, item, attempt: setattr(runner, "_needs_menu", True)
  runner.run(1)
  from otrbot.constants import Navigate
  assert runner.browser.clicked.count(Navigate.MENU_TAMOGATASOK.value) == 2

@pytest.mark.parametrize("notice, expected", [
  ("A rögzítés sikeresen megtörtént.", None),
  ("Hiba: hiányzó mező", FinalSubmitError),
  ("", SubmittedUncertain),
])
def test_fixing_form(journal, notice, expected):
  runner = make_runner(journal, [], lambda item: None)
  runner.browser.notice = notice
  if expected is None:
    assert runner._fixingForm("RogzitesKesz") is True
  else:
    with pytest.raises(expected):
      runner._fixingForm("RogzitesKesz")

def test_otrid_prefers_journal(journal):
  runner = make_runner(journal, [1, 2], lambda item: None)
  journal.mark(1, 1, OK, otrid="OTR-1")
  items = list(runner._items())
  assert runner._otrid(items[0]) == "OTR-1"
  assert runner._otrid(items[1]) == "X2"
