import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

OK = "ok"
FAILED = "failed"
PENDING = "pending"

ROUND_NAMES = {1: "benyujtas", 2: "dontes", 3: "szerzodes", 4: "lezaras"}


class Journal:
  """
  Persists the outcome of every (row, round) pair in an SQLite file next to the Excel file,
  so an interrupted run can be restarted and continues with the unfinished items.
  """

  def __init__(self, path: str):
    self.path = path
    self._conn = sqlite3.connect(path)
    self._conn.execute("""
      CREATE TABLE IF NOT EXISTS items (
        rowid TEXT NOT NULL,
        round INTEGER NOT NULL,
        status TEXT NOT NULL,
        otrid TEXT,
        attempts INTEGER NOT NULL DEFAULT 0,
        duration REAL,
        error TEXT,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (rowid, round)
      )""")
    self._conn.execute("""
      CREATE TABLE IF NOT EXISTS applicants (
        rowid TEXT PRIMARY KEY,
        city TEXT,
        regid TEXT
      )""")
    self._conn.execute("DROP VIEW IF EXISTS eredmeny")
    self._conn.execute(self._result_view_sql())
    self._conn.commit()

  @classmethod
  def for_excel(cls, excel_file_path: str) -> 'Journal':
    return cls(str(Path(excel_file_path).with_suffix(".journal.sqlite")))

  def close(self):
    self._conn.close()

  def status(self, rowid, round: int) -> Optional[str]:
    row = self._conn.execute("SELECT status FROM items WHERE rowid = ? AND round = ?", (str(rowid), round)).fetchone()
    return row[0] if row else None

  def is_done(self, rowid, round: int) -> bool:
    return self.status(rowid, round) == OK

  def otrid(self, rowid) -> Optional[str]:
    """The OTR id captured by any round (it is read from the search grid), if any."""
    row = self._conn.execute("SELECT otrid FROM items WHERE rowid = ? AND otrid IS NOT NULL AND otrid != '' ORDER BY round LIMIT 1", (str(rowid),)).fetchone()
    return row[0] if row and row[0] else None

  def start(self, rowid, round: int, city: Optional[str] = None, regid: Optional[str] = None):
    """Registers an attempt; the item stays pending until it is marked. City and tax number make the journal readable on its own."""
    if city is not None or regid is not None:
      self._conn.execute("""
        INSERT INTO applicants (rowid, city, regid) VALUES (?, ?, ?)
        ON CONFLICT (rowid) DO UPDATE SET city = COALESCE(excluded.city, city), regid = COALESCE(excluded.regid, regid)""",
        (str(rowid), city, None if regid is None else str(regid)))
    self._conn.execute("""
      INSERT INTO items (rowid, round, status, attempts, updated_at) VALUES (?, ?, ?, 1, ?)
      ON CONFLICT (rowid, round) DO UPDATE SET status = ?, attempts = attempts + 1, updated_at = ?""",
      (str(rowid), round, PENDING, self._now(), PENDING, self._now()))
    self._conn.commit()

  def mark(self, rowid, round: int, status: str, otrid: Optional[str] = None, error: Optional[str] = None, duration: Optional[float] = None):
    self._conn.execute("""
      INSERT INTO items (rowid, round, status, otrid, duration, error, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT (rowid, round) DO UPDATE SET status = excluded.status, otrid = COALESCE(excluded.otrid, otrid),
        duration = excluded.duration, error = excluded.error, updated_at = excluded.updated_at""",
      (str(rowid), round, status, otrid, duration, error, self._now()))
    self._conn.commit()

  def counts(self, round: int) -> Dict[str, int]:
    rows = self._conn.execute("SELECT status, COUNT(*) FROM items WHERE round = ? GROUP BY status", (round,)).fetchall()
    return dict(rows)

  def failed(self, round: int) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """(rowid, city, error) of the items that are not ok in the round."""
    return self._conn.execute("""
      SELECT items.rowid, applicants.city, items.error FROM items LEFT JOIN applicants USING (rowid)
      WHERE items.round = ? AND items.status != ? ORDER BY CAST(items.rowid AS INTEGER)""", (round, OK)).fetchall()

  @staticmethod
  def _result_view_sql() -> str:
    """One row per item: city, tax number, OTR id and the status, attempts and error of every round."""
    columns = []
    for round, name in ROUND_NAMES.items():
      for column, alias in (("status", "status"), ("attempts", "probalkozas"), ("error", "hiba")):
        columns.append(f"MAX(CASE WHEN items.round = {round} THEN items.{column} END) AS {name}_{alias}")
    return f"""
      CREATE VIEW eredmeny AS
      SELECT items.rowid AS rowid, applicants.city AS telepules, applicants.regid AS adoszam,
        (SELECT o.otrid FROM items o WHERE o.rowid = items.rowid AND o.otrid IS NOT NULL AND o.otrid != '' ORDER BY o.round LIMIT 1) AS otr_azonosito,
        {", ".join(columns)}
      FROM items LEFT JOIN applicants USING (rowid)
      GROUP BY items.rowid
      ORDER BY CAST(items.rowid AS INTEGER)"""

  @staticmethod
  def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
