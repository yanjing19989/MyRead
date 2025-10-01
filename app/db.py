from __future__ import annotations
import aiosqlite
import os
from pathlib import Path

DB_PATH = os.path.abspath("myread.sqlite3")

SCHEMA_SQL = r"""
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=MEMORY;

CREATE TABLE IF NOT EXISTS albums (
  id INTEGER PRIMARY KEY,
  type TEXT NOT NULL CHECK(type IN ('zip','folder')),
  path TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  mtime INTEGER NOT NULL,
  size INTEGER NOT NULL,
  file_count INTEGER NOT NULL,
  added_at INTEGER NOT NULL,
  cover_path TEXT NULL,
  crop TEXT NULL
);

CREATE TABLE IF NOT EXISTS thumbs (
  id INTEGER PRIMARY KEY,
  album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  file_path TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  last_access INTEGER NOT NULL,
  UNIQUE(album_id, key)
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


async def init_db() -> None:
  """Initialize database schema and pragmas.

  Important: Use a short-lived connection so it closes cleanly on Windows.
  Keeping an unclosed connection during startup can hold a file lock and
  break uvicorn reload. This function intentionally does not return the
  connection.
  """
  async with aiosqlite.connect(DB_PATH) as db:
    # It's safe to run PRAGMAs and schema creation on a transient connection
    # to avoid lingering file locks on Windows during dev reload.
    await db.executescript(SCHEMA_SQL)
    await db.commit()
    # enable foreign keys for this connection as well (not strictly needed
    # for schema creation, but keeps behavior consistent if reused later)
    await db.execute("PRAGMA foreign_keys=ON;")
  # connection is closed here

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA foreign_keys=ON;")
    try:
        yield db
    finally:
        await db.close()
