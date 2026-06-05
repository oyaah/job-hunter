"""U5 — enrichment fallback chain. Providers mocked via enrichment._ADAPTERS."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import credits  # noqa: E402
import enrichment  # noqa: E402

CONTACT = {"id": 1, "name": "Jane Doe", "linkedin_url": "https://linkedin.com/in/jane"}


def conn_with(**seeds):
    conn = store.connect(":memory:")
    for svc, kw in seeds.items():
        credits.seed(conn, svc, **kw)
    return conn


def patch(monkeypatch, **adapters):
    monkeypatch.setattr(enrichment, "_ADAPTERS", dict(enrichment._ADAPTERS, **adapters))


def test_hunter_verified_short_circuits(monkeypatch):
    called = {"apollo": False}

    def hunter(c, d):
        return {"email": "jane@acme.com", "verified": True, "email_status": "verified",
                "phone": None, "score": 95, "source": "hunter"}

    def apollo(c, d):
        called["apollo"] = True
        return None

    patch(monkeypatch, hunter=hunter, apollo=apollo)
    conn = conn_with(hunter=dict(remaining=50, monthly_quota=50),
                     apollo=dict(remaining=100, monthly_quota=100))
    res = enrichment.enrich(conn, CONTACT, "acme.com")
    assert res["status"] == "verified" and res["email"] == "jane@acme.com"
    assert called["apollo"] is False  # never reached Apollo
    assert credits.check(conn, "hunter")["remaining"] == 49  # 1 credit recorded


def test_hunter_miss_falls_through_to_apollo(monkeypatch):
    patch(monkeypatch,
          hunter=lambda c, d: None,
          apollo=lambda c, d: {"email": "jane@acme.com", "verified": True,
                               "email_status": "verified", "phone": "+1", "source": "apollo"})
    conn = conn_with(hunter=dict(remaining=50, monthly_quota=50),
                     apollo=dict(remaining=100, monthly_quota=100))
    res = enrichment.enrich(conn, CONTACT, "acme.com")
    assert res["source"] == "apollo" and res["status"] == "verified"
    assert credits.check(conn, "hunter")["remaining"] == 49  # hunter still charged for its attempt


def test_guessed_not_returned_as_verified(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: {
        "email": "j.doe@acme.com", "verified": False, "email_status": "guessed",
        "phone": None, "score": 40, "source": "hunter"})
    conn = conn_with(hunter=dict(remaining=50, monthly_quota=50))
    res = enrichment.enrich(conn, CONTACT, "acme.com")
    assert res["status"] == "unverified"  # surfaced as a guess, never 'verified'


def test_all_exhausted_needs_credits(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: {"email": "x", "verified": True})
    conn = conn_with(hunter=dict(remaining=0, status="exhausted"),
                     apollo=dict(remaining=0, status="exhausted"))
    assert enrichment.enrich(conn, CONTACT, "acme.com")["status"] == "needs_credits"


def test_credit_error_marks_exhausted_and_advances(monkeypatch):
    from integrations import CreditError

    def hunter(c, d):
        raise CreditError("429")

    patch(monkeypatch, hunter=hunter,
          apollo=lambda c, d: {"email": "jane@acme.com", "verified": True,
                               "email_status": "verified", "phone": None, "source": "apollo"})
    conn = conn_with(hunter=dict(remaining=50, monthly_quota=50),
                     apollo=dict(remaining=100, monthly_quota=100))
    res = enrichment.enrich(conn, CONTACT, "acme.com")
    assert res["source"] == "apollo"
    assert credits.check(conn, "hunter")["status"] == "exhausted"


def test_no_match_when_providers_run_but_find_nothing(monkeypatch):
    patch(monkeypatch, hunter=lambda c, d: None, apollo=lambda c, d: None)
    conn = conn_with(hunter=dict(remaining=50, monthly_quota=50),
                     apollo=dict(remaining=100, monthly_quota=100))
    assert enrichment.enrich(conn, CONTACT, "acme.com")["status"] == "no_match"
