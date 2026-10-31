import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

OK = "ok"
FAILED = "failed"
PENDING = "pending"

ROUND_NAMES = {1: "benyujtas", 2: "dontes", 3: "szerzodes", 4: "lezaras"}


class Journal:
  """
  Persists the outcome of every (row, round) pair in an SQLite file next to the Excel file,
  so an interrupted run can be restarted and continues with the unfinished items.
  """

  ITEMS_SQL = """
    CREATE TABLE IF NOT EXISTS {name} (
      rowid INTEGER NOT NULL,
      round INTEGER NOT NULL,
      status TEXT NOT NULL,
      otrid TEXT,
      attempts INTEGER NOT NULL DEFAULT 0,
      duration REAL,
      error TEXT,
      updated_at TEXT NOT NULL,
      PRIMARY KEY (rowid, round)
    )"""
  APPLICANTS_SQL = """
    CREATE TABLE IF NOT EXISTS {name} (
      rowid INTEGER PRIMARY KEY,
      city TEXT,
      regid TEXT
    )"""

  def __init__(self, path: str):
    self.path = path
    self._conn = sqlite3.connect(path)
    self._conn.execute("DROP VIEW IF EXISTS eredmeny")
    self._migrate("items", self.ITEMS_SQL)
    self._migrate("applicants", self.APPLICANTS_SQL)
    self._conn.execute(self.ITEMS_SQL.format(name="items"))
    self._conn.execute(self.APPLICANTS_SQL.format(name="applicants"))
    self._conn.execute(self._result_view_sql())
    self._conn.commit()

  def _migrate(self, table: str, create_sql: str):
    """Older journals stored rowid as TEXT; rebuilds the table with an INTEGER rowid, keeping the data."""
    columns = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
    rowid_type = next((column[2] for column in columns if column[1] == "rowid"), None)
    if rowid_type is None or rowid_type.upper() == "INTEGER":
      return
    names = ", ".join(column[1] for column in columns)
    values = ", ".join("CAST(rowid AS INTEGER)" if column[1] == "rowid" else column[1] for column in columns)
    with self._conn:
      self._conn.execute(create_sql.format(name=f"{table}_new"))
      self._conn.execute(f"INSERT INTO {table}_new ({names}) SELECT {values} FROM {table}")
      self._conn.execute(f"DROP TABLE {table}")
      self._conn.execute(f"ALTER TABLE {table}_new RENAME TO {table}")

  @classmethod
  def for_excel(cls, excel_file_path: str) -> 'Journal':
    return cls(str(Path(excel_file_path).with_suffix(".journal.sqlite")))

  def close(self):
    self._conn.close()

  def status(self, rowid, round: int) -> Optional[str]:
    row = self._conn.execute("SELECT status FROM items WHERE rowid = ? AND round = ?", (int(rowid), round)).fetchone()
    return row[0] if row else None

  def is_done(self, rowid, round: int) -> bool:
    return self.status(rowid, round) == OK

  def otrid(self, rowid) -> Optional[str]:
    """The OTR id captured by any round (it is read from the search grid), if any."""
    row = self._conn.execute("SELECT otrid FROM items WHERE rowid = ? AND otrid IS NOT NULL AND otrid != '' ORDER BY round LIMIT 1", (int(rowid),)).fetchone()
    return row[0] if row and row[0] else None

  def load_applicants(self, rows: Iterable[Tuple[int, Optional[str], Optional[str]]]):
    """Stores (rowid, city, tax number) of every input row, so the journal is readable on its own. The input file wins over older values."""
    self._conn.executemany("""
      INSERT INTO applicants (rowid, city, regid) VALUES (?, ?, ?)
      ON CONFLICT (rowid) DO UPDATE SET city = excluded.city, regid = excluded.regid""",
      [(int(rowid), city, None if regid is None else str(regid)) for rowid, city, regid in rows])
    self._conn.commit()

  def start(self, rowid, round: int):
    """Registers an attempt; the item stays pending until it is marked."""
    self._conn.execute("""
      INSERT INTO items (rowid, round, status, attempts, updated_at) VALUES (?, ?, ?, 1, ?)
      ON CONFLICT (rowid, round) DO UPDATE SET status = ?, attempts = attempts + 1, updated_at = ?""",
      (int(rowid), round, PENDING, self._now(), PENDING, self._now()))
    self._conn.commit()

  def mark(self, rowid, round: int, status: str, otrid: Optional[str] = None, error: Optional[str] = None, duration: Optional[float] = None):
    self._conn.execute("""
      INSERT INTO items (rowid, round, status, otrid, duration, error, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT (rowid, round) DO UPDATE SET status = excluded.status, otrid = COALESCE(excluded.otrid, otrid),
        duration = excluded.duration, error = excluded.error, updated_at = excluded.updated_at""",
      (int(rowid), round, status, otrid, duration, error, self._now()))
    self._conn.commit()

  def counts(self, round: int) -> Dict[str, int]:
    rows = self._conn.execute("SELECT status, COUNT(*) FROM items WHERE round = ? GROUP BY status", (round,)).fetchall()
    return dict(rows)

  def failed(self, round: int) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """(rowid, city, error) of the items that are not ok in the round."""
    return self._conn.execute("""
      SELECT items.rowid, applicants.city, items.error FROM items LEFT JOIN applicants USING (rowid)
      WHERE items.round = ? AND items.status != ? ORDER BY items.rowid""", (round, OK)).fetchall()

  @staticmethod
  def _result_view_sql() -> str:
    """One row per input row (and per journal item): city, tax number, OTR id and the status, attempts and error of every round."""
    columns = []
    for round, name in ROUND_NAMES.items():
      for column, alias in (("status", "status"), ("attempts", "probalkozas"), ("error", "hiba")):
        columns.append(f"MAX(CASE WHEN items.round = {round} THEN items.{column} END) AS {name}_{alias}")
    return f"""
      CREATE VIEW eredmeny AS
      SELECT ids.rowid AS rowid, applicants.city AS telepules, applicants.regid AS adoszam,
        (SELECT o.otrid FROM items o WHERE o.rowid = ids.rowid AND o.otrid IS NOT NULL AND o.otrid != '' ORDER BY o.round LIMIT 1) AS otr_azonosito,
        {", ".join(columns)}
      FROM (SELECT rowid FROM applicants UNION SELECT rowid FROM items) ids
      LEFT JOIN applicants ON applicants.rowid = ids.rowid
      LEFT JOIN items ON items.rowid = ids.rowid
      GROUP BY ids.rowid
      ORDER BY ids.rowid"""

  @staticmethod
  def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
