"""Self-evolving layer — learnings store."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import learnings  # noqa: E402


def fresh():
    return store.connect(":memory:")


def test_record_and_get():
    conn = fresh()
    learnings.record(conn, "voice", "user prefers no humor close in formal emails", source="review-edit")
    rows = learnings.get(conn, "voice")
    assert len(rows) == 1 and "no humor" in rows[0]["insight"]


def test_reinforce_accumulates_weight():
    conn = fresh()
    learnings.record(conn, "targeting", "skip companies under 10 people", source="rejection")
    learnings.record(conn, "targeting", "skip companies under 10 people", source="rejection")
    rows = learnings.get(conn, "targeting")
    assert len(rows) == 1 and rows[0]["weight"] == 2.0  # deduped, reinforced


def test_get_orders_by_weight():
    conn = fresh()
    learnings.record(conn, "voice", "weak insight")
    learnings.record(conn, "voice", "strong insight", weight=3.0)
    assert learnings.get(conn, "voice")[0]["insight"] == "strong insight"


def test_as_context_groups_by_category():
    conn = fresh()
    learnings.record(conn, "voice", "lead with the war story")
    learnings.record(conn, "targeting", "prefer research labs")
    ctx = learnings.as_context(conn)
    assert "voice" in ctx and "targeting" in ctx and "war story" in ctx


def test_as_context_empty():
    assert learnings.as_context(fresh()) == ""


def test_forget():
    conn = fresh()
    learnings.record(conn, "general", "x")
    lid = learnings.get(conn)[0]["id"]
    learnings.forget(conn, lid)
    assert learnings.get(conn) == []
