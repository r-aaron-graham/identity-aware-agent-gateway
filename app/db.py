import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from app.config import AUTO_INIT_DB, DB_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "sql" / "schema.sql"


def ensure_parent_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_parent_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    ensure_parent_dir()
    with connect() as conn:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()


def maybe_init_db() -> None:
    if AUTO_INIT_DB:
        init_db()


@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def fetch_one(query: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def execute(query: str, params: Iterable[Any] = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid


def execute_many(query: str, rows: Iterable[Iterable[Any]]) -> None:
    with get_conn() as conn:
        conn.executemany(query, rows)
        conn.commit()


def write_audit(trace_id: str, event_type: str, details: dict) -> None:
    execute(
        """
        INSERT INTO audit_events (trace_id, event_type, details_json, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (trace_id, event_type, json.dumps(details, separators=(",", ":"))),
    )
