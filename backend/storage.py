"""
SQLite persistence for incidents. Keeps observed_at for time-window reports.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "crisis_compass.db")


def get_db_path() -> str:
    raw = os.environ.get("CRISIS_COMPASS_DB_PATH", "").strip()
    if raw:
        return raw
    return DEFAULT_DB_PATH


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def _dedupe_key_from_incident(inc: Dict[str, Any]) -> str:
    url = (inc.get("url") or "").strip()
    if url:
        return "url|" + url.split("?")[0].strip().lower()
    title = (inc.get("title") or "").strip().lower()[:120]
    loc = (inc.get("location") or "").strip().lower()[:80]
    return "hash|" + f"{title}|{loc}"


def parse_observed_at(inc: Dict[str, Any]) -> float:
    """Unix timestamp for reporting; falls back to now."""
    ts = inc.get("observed_at")
    if isinstance(ts, (int, float)) and ts > 0:
        return float(ts)
    s = (inc.get("timestamp") or "").strip()
    if not s:
        return time.time()
    trials = [
        (s, "%Y-%m-%d %I:%M %p"),
        (s, "%Y-%m-%d %H:%M:%S"),
        (s.replace("Z", "")[:19], "%Y-%m-%dT%H:%M:%S"),
        (s[:10], "%Y-%m-%d"),
    ]
    for text, fmt in trials:
        try:
            return datetime.strptime(text, fmt).timestamp()
        except ValueError:
            continue
    return time.time()


def connect() -> sqlite3.Connection:
    path = get_db_path()
    _ensure_dir(path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY,
            dedupe_key TEXT NOT NULL UNIQUE,
            observed_at REAL NOT NULL,
            data_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_observed_at ON incidents(observed_at)")
    conn.commit()


def row_to_incident(row: sqlite3.Row) -> Dict[str, Any]:
    data = json.loads(row["data_json"])
    data["id"] = row["id"]
    data.setdefault("observed_at", row["observed_at"])
    return data


def upsert_incident(conn: sqlite3.Connection, inc: Dict[str, Any]) -> Dict[str, Any]:
    """Insert or replace by dedupe_key; preserves id if row exists."""
    dedupe = _dedupe_key_from_incident(inc)
    observed = parse_observed_at(inc)
    inc_copy = dict(inc)
    inc_copy["observed_at"] = observed
    cur = conn.execute("SELECT id FROM incidents WHERE dedupe_key = ?", (dedupe,))
    existing = cur.fetchone()
    if existing:
        iid = int(existing["id"])
    else:
        cur = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM incidents")
        iid = int(cur.fetchone()["n"])
    inc_copy["id"] = iid
    payload = json.dumps(inc_copy, default=str)
    conn.execute(
        """
        INSERT INTO incidents (id, dedupe_key, observed_at, data_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(dedupe_key) DO UPDATE SET
            observed_at = excluded.observed_at,
            data_json = excluded.data_json
        """,
        (iid, dedupe, observed, payload),
    )
    conn.commit()
    return inc_copy


def load_all_incidents(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.execute("SELECT id, dedupe_key, observed_at, data_json FROM incidents ORDER BY id ASC")
    return [row_to_incident(r) for r in cur.fetchall()]


def list_incidents_since(
    conn: sqlite3.Connection,
    since_ts: Optional[float] = None,
    until_ts: Optional[float] = None,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    q = "SELECT id, dedupe_key, observed_at, data_json FROM incidents WHERE 1=1"
    args: List[Any] = []
    if since_ts is not None:
        q += " AND observed_at >= ?"
        args.append(since_ts)
    if until_ts is not None:
        q += " AND observed_at < ?"
        args.append(until_ts)
    q += " ORDER BY observed_at DESC LIMIT ?"
    args.append(limit)
    cur = conn.execute(q, args)
    return [row_to_incident(r) for r in cur.fetchall()]
