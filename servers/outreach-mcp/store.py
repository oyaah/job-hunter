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
    _migrate(conn)
    conn.commit()
    return conn


def _migrate(conn):
    """Defensive column adds for DBs created before a schema bump (CREATE IF NOT
    EXISTS won't alter an existing table). Each guarded — ignore 'duplicate column'."""
    for table, col, decl in [("learnings", "distilled_at", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise  # already migrated is fine; locked/disk/real errors must surface


def connect_default():
    """Open the DB at $DATA_DIR/job-hunter.db (runtime path from the plugin env)."""
    data_dir = os.environ.get("DATA_DIR") or os.path.expanduser("~/.config/job-hunter")
    os.makedirs(data_dir, exist_ok=True)
    return connect(os.path.join(data_dir, "job-hunter.db"))
