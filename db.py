from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'DB' / 'sampe1.db'


def connect() -> sqlite3.Connection:
    """Create a fresh SQLite connection for a single operation."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def connection() -> Iterable[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...] | None:
    with connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchone()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with connection() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def execute_many(sql: str, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    with connection() as conn:
        conn.executemany(sql, rows)
        conn.commit()
