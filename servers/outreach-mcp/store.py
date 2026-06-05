"""SQLite connection + schema bootstrap. Shared by state.py and credits.py."""
import os
import sqlite3

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db", "schema.sql")


def connect(path):
    """Open (and initialize) the outreach DB. Pass ':memory:' for tests."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def connect_default():
    """Open the DB at $DATA_DIR/job-hunter.db (runtime path from the plugin env)."""
    data_dir = os.environ.get("DATA_DIR") or os.path.expanduser("~/.config/job-hunter")
    os.makedirs(data_dir, exist_ok=True)
    return connect(os.path.join(data_dir, "job-hunter.db"))
