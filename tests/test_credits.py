"""U2 — credit ledger + fallback-chain selection. Written test-first (Execution note)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import credits  # noqa: E402


def fresh_conn():
    return store.connect(":memory:")


def test_record_decrements_remaining():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=50, monthly_quota=50)
    credits.record(conn, "hunter", "default", op="email_find", cost=1, contact_id=None)
    assert credits.check(conn, "hunter", "default")["remaining"] == 49


def test_pick_provider_returns_first_usable_in_chain():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=50, monthly_quota=50)
    credits.seed(conn, "apollo", "default", remaining=100, monthly_quota=100)
    # hunter is first in the enrichment chain and has credits → picked
    assert credits.pick_provider(conn, "enrich") == ("hunter", "default")


def test_pick_provider_skips_exhausted():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=0, monthly_quota=50, status="exhausted")
    credits.seed(conn, "apollo", "default", remaining=100, monthly_quota=100)
    assert credits.pick_provider(conn, "enrich") == ("apollo", "default")


def test_pick_provider_skips_when_remaining_below_cost():
    conn = fresh_conn()
    # apollo phone enrich costs 8; hunter can't do phone → apollo only, but it has 3 left
    credits.seed(conn, "apollo", "default", remaining=3, monthly_quota=100)
    assert credits.pick_provider(conn, "phone") is None


def test_pick_provider_none_when_all_exhausted():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=0, status="exhausted")
    credits.seed(conn, "apollo", "default", remaining=0, status="exhausted")
    assert credits.pick_provider(conn, "enrich") is None


def test_mark_exhausted_on_402():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=5, monthly_quota=50)
    credits.mark_exhausted(conn, "hunter", "default", reset_at="2026-07-01")
    row = credits.check(conn, "hunter", "default")
    assert row["status"] == "exhausted"
    assert row["reset_at"] == "2026-07-01"


def test_low_status_when_below_threshold():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=50, monthly_quota=50)
    # drain to < 10% (4 left of 50)
    for _ in range(46):
        credits.record(conn, "hunter", "default", op="email_find", cost=1, contact_id=None)
    assert credits.check(conn, "hunter", "default")["status"] == "low"


def test_rotation_picks_next_account_same_service():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "acct1", remaining=0, status="exhausted")
    credits.seed(conn, "hunter", "acct2", remaining=50, monthly_quota=50)
    assert credits.pick_provider(conn, "enrich") == ("hunter", "acct2")


def test_balances_summary_lists_all():
    conn = fresh_conn()
    credits.seed(conn, "hunter", "default", remaining=12, monthly_quota=50)
    credits.seed(conn, "apollo", "default", remaining=0, status="exhausted")
    summary = credits.balances(conn)
    by_service = {(r["service"], r["account_id"]): r for r in summary}
    assert by_service[("hunter", "default")]["remaining"] == 12
    assert by_service[("apollo", "default")]["status"] == "exhausted"
