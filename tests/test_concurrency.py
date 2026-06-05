"""U2 — the DB connection must be safe under concurrent cross-thread tool calls
(FastMCP dispatches tools on worker threads). Before the fix this raised
sqlite3.ProgrammingError (same-thread guard)."""
import os
import sys
import threading
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import state  # noqa: E402


def _proxy(path):
    # Mirror the production object: a thread-local proxy over a file-backed WAL DB.
    return store._ThreadLocalConn(path)


def test_cross_thread_use_does_not_crash():
    conn = _proxy(os.path.join(tempfile.mkdtemp(), "c.db"))
    err = {}

    def worker():
        try:
            state.upsert_company(conn, "acme", "Acme")
            state.get_company(conn, "acme")
        except Exception as e:  # noqa: BLE001
            err["e"] = e

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    assert "e" not in err, f"cross-thread use raised: {err.get('e')!r}"


def test_concurrent_writes_all_persist():
    path = os.path.join(tempfile.mkdtemp(), "c.db")
    conn = _proxy(path)
    n = 20
    errs = []

    def writer(i):
        try:
            state.upsert_company(conn, f"co{i}", f"Co {i}")
        except Exception as e:  # noqa: BLE001
            errs.append(repr(e))

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errs, f"concurrent writes raised: {errs[:3]}"
    # read from the main thread's own connection — WAL sees all committed writes
    assert len(state.pipeline_board(conn)) == n
