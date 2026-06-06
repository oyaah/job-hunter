"""send_email gate + voice lint at the server boundary (safety rails)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

os.environ["DATA_DIR"] = tempfile.mkdtemp()
import server  # noqa: E402

CLEAN = "Hi Jane, saw your work on the fraud pipeline. Quick question. Thanks!"


def test_unapproved_send_blocked():
    res = server.send_email("jane@acme.com", "hi", CLEAN, approved=False)
    assert "approved is false" in res["error"]


def test_no_recipient_blocked():
    assert "no recipient" in server.send_email("", "hi", CLEAN, approved=True)["error"]


def test_voice_lint_blocks_send():
    res = server.send_email("jane@acme.com", "hi", "I build systems — and ship them.",
                            approved=True)
    assert "violations" in res  # em-dash blocked before any send


def test_approved_clean_sends(monkeypatch):
    monkeypatch.setattr(server, "_send_via", lambda ch, to, s, b: "smtp")
    res = server.send_email("jane@acme.com", "hi", CLEAN, approved=True)
    assert res["status"] == "sent" and res["channel"] == "smtp"


def test_voice_lint_tool():
    assert server.voice_lint(CLEAN)["clean"] is True
    assert server.voice_lint("I am writing to express my interest.")["clean"] is False
