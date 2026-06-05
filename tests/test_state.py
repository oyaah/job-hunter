"""U2 — per-company state store."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import state  # noqa: E402


def fresh_conn():
    return store.connect(":memory:")


def test_company_roundtrip_and_isolation():
    conn = fresh_conn()
    state.upsert_company(conn, "acme", "Acme Corp", status="targeted")
    state.upsert_company(conn, "globex", "Globex", status="new")
    state.add_contact(conn, "acme", "Jane Doe", role="CTO")
    rec = state.get_company(conn, "acme")
    assert rec["name"] == "Acme Corp"
    assert len(rec["contacts"]) == 1
    # isolation: acme's record carries no globex data
    assert all(c["company_slug"] == "acme" for c in rec["contacts"])
    assert "globex" not in str(rec)


def test_get_missing_company_returns_none():
    assert state.get_company(fresh_conn(), "nope") is None


def test_contact_update_and_get():
    conn = fresh_conn()
    state.upsert_company(conn, "acme", "Acme")
    cid = state.add_contact(conn, "acme", "Jane")
    state.update_contact(conn, cid, email="jane@acme.com", email_status="verified", email_score=92)
    c = state.get_contact(conn, cid)
    assert c["email"] == "jane@acme.com"
    assert c["email_status"] == "verified"
    # unknown fields are ignored, not crashed on
    state.update_contact(conn, cid, bogus="x")
    assert state.get_contact(conn, cid)["email"] == "jane@acme.com"


def test_message_lifecycle():
    conn = fresh_conn()
    state.upsert_company(conn, "acme", "Acme")
    cid = state.add_contact(conn, "acme", "Jane")
    mid = state.add_message(conn, cid, "email", "Hi Jane, ...", subject="quick q")
    pending = state.list_pending_messages(conn)
    assert len(pending) == 1 and pending[0]["contact_name"] == "Jane"
    state.set_message_status(conn, mid, "sent", sent=True)
    assert state.list_pending_messages(conn) == []


def test_linkedin_lifecycle_stamps():
    conn = fresh_conn()
    state.upsert_company(conn, "acme", "Acme")
    cid = state.add_contact(conn, "acme", "Jane")
    state.upsert_linkedin(conn, cid, note="hi", dm="thanks for connecting", status="DRAFTED")
    state.set_linkedin_status(conn, cid, "QUEUED")
    state.set_linkedin_status(conn, cid, "SENT")
    state.set_linkedin_status(conn, cid, "ACCEPTED")
    rec = state.get_company(conn, "acme")
    li = rec["contacts"][0]["linkedin"]
    assert li["status"] == "ACCEPTED"
    assert li["accepted_at"] is not None and li["queued_at"] is not None


def test_pipeline_board():
    conn = fresh_conn()
    assert state.pipeline_board(conn) == []
    state.upsert_company(conn, "acme", "Acme", status="sent")
    cid = state.add_contact(conn, "acme", "Jane")
    mid = state.add_message(conn, cid, "email", "body")
    state.set_message_status(conn, mid, "sent", sent=True)
    board = state.pipeline_board(conn)
    assert len(board) == 1
    assert board[0]["status"] == "sent"
    assert board[0]["contacts"] == 1 and board[0]["sent"] == 1


def test_cascade_delete_removes_contacts():
    conn = fresh_conn()
    state.upsert_company(conn, "acme", "Acme")
    state.add_contact(conn, "acme", "Jane")
    conn.execute("DELETE FROM companies WHERE slug='acme'")
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0] == 0
