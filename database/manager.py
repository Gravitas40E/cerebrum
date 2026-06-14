"""SQLite connection and schema management for Cerebrum."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from models.schema import DB_PATH

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS folders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL DEFAULT 'New Folder',
    parent_id   INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    is_expanded INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS notes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT    NOT NULL DEFAULT '',
    body           TEXT    NOT NULL DEFAULT '',
    plain          TEXT    NOT NULL DEFAULT '',
    folder_id      INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    is_pinned      INTEGER NOT NULL DEFAULT 0,
    is_archived    INTEGER NOT NULL DEFAULT 0,
    is_favorite    INTEGER NOT NULL DEFAULT 0,
    is_brain_vault INTEGER NOT NULL DEFAULT 0,
    daily_log_date TEXT,
    created_at     TEXT    NOT NULL,
    updated_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
    tag_id  INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

CREATE TABLE IF NOT EXISTS streaks (
    id        INTEGER PRIMARY KEY CHECK (id = 1),
    current   INTEGER NOT NULL DEFAULT 0,
    best      INTEGER NOT NULL DEFAULT 0,
    last_date TEXT
);

CREATE TABLE IF NOT EXISTS app_state (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_notes_daily_log ON notes(daily_log_date);
CREATE INDEX IF NOT EXISTS idx_notes_folder   ON notes(folder_id);
CREATE INDEX IF NOT EXISTS idx_notes_pinned   ON notes(is_pinned);
CREATE INDEX IF NOT EXISTS idx_notes_archived ON notes(is_archived);
CREATE INDEX IF NOT EXISTS idx_notes_fav      ON notes(is_favorite);
CREATE INDEX IF NOT EXISTS idx_notes_updated  ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_notes_vault    ON notes(is_brain_vault);
"""


class Database:
    """A small thread-safe wrapper around one SQLite connection."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else DB_PATH
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA_SQL)
            self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def execute(self, sql: str, params: tuple | list = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params)

    def executemany(self, sql: str, seq: list[tuple]) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, seq)

    def commit(self) -> None:
        with self._lock:
            self._conn.commit()

    def rollback(self) -> None:
        with self._lock:
            self._conn.rollback()

    @contextmanager
    def transaction(self):
        with self._lock:
            try:
                yield self
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
