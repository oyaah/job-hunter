"""SQLite connection + schema bootstrap. Shared by state.py and credits.py."""
import os
import sqlite3
import threading

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db", "schema.sql")


def connect(path):
    """Open (and initialize) the outreach DB. Pass ':memory:' for tests.

    check_same_thread=False: FastMCP may dispatch tools on worker threads, so the
    single process connection must be usable across threads. CPython's sqlite3 is
    built in serialized threadsafe mode (SQLITE_THREADSAFE=1), which mutexes the
    connection — concurrent calls are serialized safely rather than crashing on the
    same-thread guard. busy_timeout covers WAL writer contention."""
    conn = sqlite3.connect(path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
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


def _default_path():
    data_dir = os.environ.get("DATA_DIR") or os.path.expanduser("~/.config/job-hunter")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "job-hunter.db")


def connect_default():
    """Open the DB at $DATA_DIR/job-hunter.db (runtime path from the plugin env)."""
    return connect(_default_path())


class _ThreadLocalConn:
    """A connection-shaped proxy that hands each thread its OWN sqlite connection
    to the same WAL database. This is the correct concurrency model for SQLite —
    one connection per thread, WAL for reader/writer coexistence — and it lets the
    35 MCP tools keep using a single `_conn` object with no changes. Attribute
    access (execute, commit, row_factory, ...) forwards to the calling thread's
    connection, opened lazily on first use."""

    def __init__(self, path):
        self._path = path
        self._local = threading.local()

    def _conn(self):
        c = getattr(self._local, "c", None)
        if c is None:
            c = self._local.c = connect(self._path)
        return c

    def __getattr__(self, name):
        return getattr(self._conn(), name)


def thread_local_default():
    """Process-wide connection object safe for FastMCP's worker-thread dispatch."""
    return _ThreadLocalConn(_default_path())
