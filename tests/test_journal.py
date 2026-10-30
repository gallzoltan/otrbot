import pandas as pd
import pytest
from otrbot.journal import Journal, OK, FAILED, PENDING

@pytest.fixture
def journal(tmp_path):
  j = Journal(str(tmp_path / "data.journal.sqlite"))
  yield j
  j.close()

def test_unknown_item_is_not_done(journal):
  assert journal.status(1, 1) is None
  assert not journal.is_done(1, 1)

def test_start_then_mark_ok(journal):
  journal.start(1, 1)
  assert journal.status(1, 1) == PENDING
  journal.mark(1, 1, OK, otrid="OTR-123", duration=12.5)
  assert journal.is_done(1, 1)
  assert journal.otrid(1) == "OTR-123"

def test_attempts_are_counted_and_otrid_is_kept(journal):
  journal.start(1, 1)
  journal.mark(1, 1, OK, otrid="OTR-123")
  journal.start(1, 1)
  journal.mark(1, 1, FAILED, error="boom")
  row = journal._conn.execute("SELECT attempts, otrid, error FROM items WHERE rowid = '1' AND round = 1").fetchone()
  assert row == (2, "OTR-123", "boom")

def test_rounds_are_independent(journal):
  journal.mark(1, 1, OK)
  assert not journal.is_done(1, 2)
  assert journal.otrid(1) is None

def test_persists_between_runs(tmp_path):
  path = str(tmp_path / "data.journal.sqlite")
  first = Journal(path)
  first.mark(7, 2, OK)
  first.close()
  second = Journal(path)
  assert second.is_done(7, 2)
  second.close()

def test_counts(journal):
  journal.mark(1, 1, OK)
  journal.mark(2, 1, OK)
  journal.mark(3, 1, FAILED)
  assert journal.counts(1) == {OK: 2, FAILED: 1}

def test_for_excel_path():
  assert Journal.for_excel("data/04_ukran.xlsx").path.replace("\\", "/") == "data/04_ukran.journal.sqlite"

def test_export(tmp_path, journal):
  excel = tmp_path / "data.xlsx"
  with pd.ExcelWriter(excel) as writer:
    pd.DataFrame([["fejléc", ""], ["rowid", "city"], [1, "Békéscsaba"], [2, "Gyula"]]).to_excel(writer, sheet_name="betolt", index=False, header=False)
  journal.mark(1, 1, OK, otrid="OTR-1")
  journal.mark(2, 1, FAILED, error="nem található")
  journal.mark(1, 2, OK)
  out = journal.export(str(excel), sheet_name="betolt")
  df = pd.read_excel(out)
  assert list(df["city"]) == ["Békéscsaba", "Gyula"]
  assert list(df["benyujtas_status"]) == [OK, FAILED]
  assert df["benyujtas_otrid"][0] == "OTR-1"
  assert df["benyujtas_hiba"][1] == "nem található"
  assert df["dontes_status"][0] == OK
  assert "szerzodes_status" not in df.columns
