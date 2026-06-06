"""kvstore (atomic JSON) + the file-backed LinkedIn rate guard."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import kvstore  # noqa: E402
import guard  # noqa: E402
import usage  # noqa: E402


def setup_function():
    os.environ["DATA_DIR"] = tempfile.mkdtemp()


def test_kvstore_roundtrip_and_persist():
    kvstore.save("t.json", {"a": 1})
    assert kvstore.load("t.json") == {"a": 1}


def test_kvstore_missing_file_is_empty():
    assert kvstore.load("nope.json") == {}


def test_guard_allows_then_blocks(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "2")
    assert guard.guard("connect")["ok"] is True
    guard.record("connect")
    guard.record("connect")
    g = guard.guard("connect")
    assert g["ok"] is False and "cap reached" in g["reason"]


def test_guard_counts_actions_separately(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "5")
    guard.record("connect")
    assert guard.used_today("message") == 0


def test_guard_persists_across_reload(monkeypatch):
    monkeypatch.setenv("LINKEDIN_DAILY_CAP", "5")
    guard.record("connect")
    assert guard.used_today("connect") == 1  # read back from file


def test_default_cap_generous(monkeypatch):
    monkeypatch.delenv("LINKEDIN_DAILY_CAP", raising=False)
    assert guard.daily_cap() == 40


def test_usage_record_and_pick():
    usage.seed("hunter", remaining=50, quota=50)
    usage.record("hunter", 1)
    assert usage.check("hunter")["remaining"] == 49
    assert usage.pick("email_find") == "hunter"
    usage.seed("hunter", remaining=0)
    assert usage.pick("email_find") is None  # exhausted, no other provider seeded
