"""U6 — LinkedIn rate guard + daily counter."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import linkedin_adapter as la  # noqa: E402


def fresh():
    return store.connect(":memory:")


def test_guard_allows_under_cap(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "5")
    conn = fresh()
    g = la.guard(conn, "connect")
    assert g["ok"] and g["remaining"] == 5


def test_record_increments_and_counts(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "5")
    conn = fresh()
    la.record(conn, "connect")
    la.record(conn, "connect")
    assert la.used_today(conn, "connect") == 2
    assert la.guard(conn, "connect")["remaining"] == 3


def test_guard_blocks_at_cap(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "2")
    conn = fresh()
    la.record(conn, "connect")
    la.record(conn, "connect")
    g = la.guard(conn, "connect")
    assert g["ok"] is False and "cap reached" in g["reason"]


def test_cap_zero_blocks_everything(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "0")
    assert la.guard(fresh(), "connect")["ok"] is False


def test_connect_and_message_counted_separately(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "5")
    conn = fresh()
    la.record(conn, "connect")
    assert la.used_today(conn, "message") == 0  # independent counters


def test_default_cap_is_generous(monkeypatch):
    monkeypatch.delenv("LINKEDIN_DAILY_CAP", raising=False)
    assert la.daily_cap() == 40
