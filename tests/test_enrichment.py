"""Enrichment fallback chain (file-backed usage). Providers mocked via _ADAPTERS."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import enrichment  # noqa: E402
import usage  # noqa: E402

CONTACT = {"name": "Jane Doe", "linkedin_url": "https://linkedin.com/in/jane"}


def setup_function():
    os.environ["DATA_DIR"] = tempfile.mkdtemp()  # isolate usage.json per test


def patch(monkeypatch, **adapters):
    monkeypatch.setattr(enrichment, "_ADAPTERS", dict(enrichment._ADAPTERS, **adapters))


def test_hunter_verified_short_circuits(monkeypatch):
    called = {"apollo": False}
    patch(monkeypatch,
          hunter=lambda c, d: {"email": "jane@acme.com", "verified": True,
                               "email_status": "verified", "phone": None, "source": "hunter"},
          apollo=lambda c, d: called.__setitem__("apollo", True))
    usage.seed("hunter", remaining=50, quota=50)
    usage.seed("apollo", remaining=100, quota=100)
    res = enrichment.enrich(CONTACT, "acme.com")
    assert res["status"] == "verified" and res["email"] == "jane@acme.com"
    assert called["apollo"] is False
    assert usage.check("hunter")["remaining"] == 49


def test_hunter_miss_falls_through_to_apollo(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: None,
          apollo=lambda c, d: {"email": "jane@acme.com", "verified": True,
                               "email_status": "verified", "phone": "+1", "source": "apollo"})
    usage.seed("hunter", remaining=50, quota=50)
    usage.seed("apollo", remaining=100, quota=100)
    assert enrichment.enrich(CONTACT, "acme.com")["source"] == "apollo"


def test_guessed_not_returned_as_verified(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: {"email": "j.doe@acme.com", "verified": False,
                                            "email_status": "guessed", "source": "hunter"})
    usage.seed("hunter", remaining=50, quota=50)
    assert enrichment.enrich(CONTACT, "acme.com")["status"] == "unverified"


def test_all_exhausted_needs_credits(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: {"email": "x", "verified": True})
    usage.seed("hunter", remaining=0)
    usage.seed("apollo", remaining=0)
    assert enrichment.enrich(CONTACT, "acme.com")["status"] == "needs_credits"


def test_credit_error_marks_exhausted_and_advances(monkeypatch):
    from integrations import CreditError
    patch(monkeypatch,
          hunter=lambda c, d: (_ for _ in ()).throw(CreditError("429")),
          apollo=lambda c, d: {"email": "jane@acme.com", "verified": True,
                               "email_status": "verified", "phone": None, "source": "apollo"})
    usage.seed("hunter", remaining=50, quota=50)
    usage.seed("apollo", remaining=100, quota=100)
    res = enrichment.enrich(CONTACT, "acme.com")
    assert res["source"] == "apollo"
    assert usage.check("hunter")["status"] == "exhausted"


def test_no_match(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: None, apollo=lambda c, d: None)
    usage.seed("hunter", remaining=50, quota=50)
    usage.seed("apollo", remaining=100, quota=100)
    assert enrichment.enrich(CONTACT, "acme.com")["status"] == "no_match"
