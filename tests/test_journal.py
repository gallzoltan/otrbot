import sqlite3
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

def test_otrid_captured_by_a_later_round(journal):
  journal.mark(1, 1, OK)
  journal.mark(1, 2, OK, otrid="14846/02/2026")
  assert journal.otrid(1) == "14846/02/2026"

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

def view(journal):
  cursor = journal._conn.execute("SELECT * FROM eredmeny")
  names = [column[0] for column in cursor.description]
  return [dict(zip(names, row)) for row in cursor.fetchall()]

def test_eredmeny_view(journal):
  journal.start(2, 1, city="Gyula", regid="15725030-2-04")
  journal.mark(2, 1, FAILED, error="nem található")
  journal.start(1, 1, city="Békéscsaba", regid="15725009-2-04")
  journal.mark(1, 1, OK)
  journal.start(1, 2)
  journal.mark(1, 2, OK, otrid="OTR-1")
  first, second = view(journal)
  assert (first["rowid"], first["telepules"], first["adoszam"], first["otr_azonosito"]) == ("1", "Békéscsaba", "15725009-2-04", "OTR-1")
  assert (first["benyujtas_status"], first["dontes_status"], first["dontes_probalkozas"]) == (OK, OK, 1)
  assert first["szerzodes_status"] is None
  assert (second["telepules"], second["benyujtas_status"], second["benyujtas_hiba"], second["otr_azonosito"]) == ("Gyula", FAILED, "nem található", None)

def test_rowids_are_ordered_numerically(journal):
  for rowid in (10, 9, 2):
    journal.mark(rowid, 1, OK)
  assert [row["rowid"] for row in view(journal)] == ["2", "9", "10"]

def test_failed_lists_not_ok_items(journal):
  journal.start(1, 1, city="Békéscsaba")
  journal.mark(1, 1, OK)
  journal.start(2, 1, city="Gyula")
  journal.mark(2, 1, FAILED, error="boom")
  journal.start(3, 1)
  assert journal.failed(1) == [("2", "Gyula", "boom"), ("3", None, None)]
  assert journal.failed(2) == []

def test_old_journal_gets_applicants_table(tmp_path):
  path = str(tmp_path / "old.journal.sqlite")
  conn = sqlite3.connect(path)
  conn.execute("""CREATE TABLE items (rowid TEXT NOT NULL, round INTEGER NOT NULL, status TEXT NOT NULL, otrid TEXT,
    attempts INTEGER NOT NULL DEFAULT 0, duration REAL, error TEXT, updated_at TEXT NOT NULL, PRIMARY KEY (rowid, round))""")
  conn.execute("INSERT INTO items VALUES ('5', 1, 'ok', NULL, 1, 1.0, NULL, '2026-10-30T10:00:00')")
  conn.commit()
  conn.close()
  journal = Journal(path)
  assert view(journal)[0]["benyujtas_status"] == OK
  assert view(journal)[0]["telepules"] is None
  journal.start(5, 2, city="Gyula")
  assert view(journal)[0]["telepules"] == "Gyula"
  journal.close()
