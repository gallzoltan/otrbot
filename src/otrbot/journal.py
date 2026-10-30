import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

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
    """The OTR id captured after the submission round, if any."""
    row = self._conn.execute("SELECT otrid FROM items WHERE rowid = ? AND round = 1", (str(rowid),)).fetchone()
    return row[0] if row and row[0] else None

  def start(self, rowid, round: int):
    """Registers an attempt; the item stays pending until it is marked."""
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

  def export(self, excel_file_path: str, sheet_name: str, out_path: Optional[str] = None) -> str:
    """Writes the input rows extended with the status, error and OTR id of every round."""
    out_path = out_path or str(Path(excel_file_path).with_name(f"{Path(excel_file_path).stem}_eredmeny.xlsx"))
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name, skiprows=1)
    items = pd.read_sql_query("SELECT rowid, round, status, otrid, attempts, error FROM items", self._conn)
    df["_key"] = df["rowid"].astype(str)
    for round, name in ROUND_NAMES.items():
      part = items[items["round"] == round]
      if part.empty:
        continue
      part = part.rename(columns={
        "status": f"{name}_status", "attempts": f"{name}_probalkozas", "error": f"{name}_hiba", "otrid": f"{name}_otrid"
      }).drop(columns=["round"])
      if round != 1:
        part = part.drop(columns=[f"{name}_otrid"])
      df = df.merge(part, how="left", left_on="_key", right_on="rowid", suffixes=("", "_journal")).drop(columns=["rowid_journal"])
    df.drop(columns=["_key"]).to_excel(out_path, index=False)
    return out_path

  @staticmethod
  def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
