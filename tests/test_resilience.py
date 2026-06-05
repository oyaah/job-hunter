"""U3 — retry/backoff + secret redaction."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import resilience  # noqa: E402


class FakeTimeout(Exception):
    pass


class CreditError(Exception):
    pass


class HTTPStatusError(Exception):
    def __init__(self, code):
        self.response = type("R", (), {"status_code": code})()


def test_retry_succeeds_after_transient(monkeypatch):
    monkeypatch.setattr(resilience.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise HTTPStatusError(503)
        return "ok"

    assert resilience.retry(flaky, attempts=3) == "ok"
    assert calls["n"] == 2


def test_retry_gives_up_after_attempts(monkeypatch):
    monkeypatch.setattr(resilience.time, "sleep", lambda s: None)

    def always_503():
        raise HTTPStatusError(503)

    try:
        resilience.retry(always_503, attempts=3)
        assert False, "should have raised"
    except HTTPStatusError:
        pass


def test_credit_error_not_retried():
    calls = {"n": 0}

    def out_of_credits():
        calls["n"] += 1
        raise CreditError("402")

    try:
        resilience.retry(out_of_credits, attempts=3)
    except CreditError:
        pass
    assert calls["n"] == 1  # terminal, no retry


def test_4xx_not_retried():
    calls = {"n": 0}

    def bad_request():
        calls["n"] += 1
        raise HTTPStatusError(400)

    try:
        resilience.retry(bad_request, attempts=3)
    except HTTPStatusError:
        pass
    assert calls["n"] == 1


def test_redaction_masks_secrets():
    assert "[REDACTED]" in resilience.redact("GET https://api.hunter.io/v2/account?api_key=abc123secret")
    assert "abc123secret" not in resilience.redact("api_key=abc123secret")
    assert "[REDACTED]" in resilience.redact('cookie: li_at=AQEDxyz; other=1')
    assert "[REDACTED]" in resilience.redact('{"app_password": "wxyz abcd efgh ijkl"}')
