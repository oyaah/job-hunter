"""U7 — the approval gate is a real safety boundary (CLAUDE.md rail #1).
Sends are blocked at the tool layer unless the message is 'approved'."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

os.environ["DATA_DIR"] = tempfile.mkdtemp()
import server  # noqa: E402  (imports after DATA_DIR set so the DB lands in tmp)
import state  # noqa: E402


def _make_message(status="draft"):
    state.upsert_company(server._conn, "acme", "Acme")
    cid = state.add_contact(server._conn, "acme", "Jane")
    state.update_contact(server._conn, cid, email="jane@acme.com")
    mid = state.add_message(server._conn, cid, "email", "Hi Jane", subject="hi")
    if status != "draft":
        state.set_message_status(server._conn, mid, status)
    return mid


def test_draft_message_is_blocked():
    mid = _make_message("draft")
    msg, err = server._require_approved(mid)
    assert msg is None
    assert "approved" in err["error"]


def test_rejected_message_is_blocked():
    mid = _make_message("rejected")
    _, err = server._require_approved(mid)
    assert err is not None


def test_approved_message_passes_gate():
    mid = _make_message("approved")
    msg, err = server._require_approved(mid)
    assert err is None
    assert msg["to_email"] == "jane@acme.com"


def test_missing_message():
    _, err = server._require_approved(99999)
    assert "no message" in err["error"]


def test_send_claim_is_atomic_single_winner():
    mid = _make_message("approved")
    first = server._claim_for_send(mid)
    assert first is not None  # first caller wins the claim (approved -> sending)
    second = server._claim_for_send(mid)
    assert second is None  # second caller blocked — no double-send


def test_add_message_rejects_ai_voice():
    state.upsert_company(server._conn, "acme", "Acme")
    cid = state.add_contact(server._conn, "acme", "Jane")
    res = server.add_message(cid, "email", "I build systems — and ship them.")
    assert "violations" in res  # em-dash blocked at the server, not just in a skill
    clean = server.add_message(cid, "email", "I build systems and ship them. Thanks!")
    assert clean.get("status") == "draft"
