"""Hunter.io v2 — the free-tier default enrichment provider (real API, balance
endpoint). Auth via ?api_key=. httpx imported lazily."""
import os

BASE = "https://api.hunter.io/v2"


class CreditError(Exception):
    """Provider signalled exhaustion (402/429)."""


def _key():
    k = os.environ.get("HUNTER_API_KEY")
    if not k:
        raise RuntimeError("HUNTER_API_KEY not set")
    return k


def _get(path, params):
    import httpx
    params = dict(params, api_key=_key())
    r = httpx.get(f"{BASE}{path}", params=params, timeout=20)
    if r.status_code in (402, 429):
        raise CreditError(f"hunter {r.status_code}")
    r.raise_for_status()
    return r.json().get("data", {})


def email_finder(domain, first_name, last_name):
    """Return {email, score, status} or None. score is 0-100 confidence."""
    data = _get("/email-finder",
                {"domain": domain, "first_name": first_name, "last_name": last_name})
    if not data.get("email"):
        return None
    return {
        "email": data["email"],
        "score": data.get("score", 0),
        "status": (data.get("verification") or {}).get("status", "unknown"),
        "source": "hunter",
    }


def email_verifier(email):
    data = _get("/email-verifier", {"email": email})
    return {"email": email, "status": data.get("status", "unknown"),
            "score": data.get("score", 0)}


def domain_search(domain):
    """Learn a company's email pattern once, then construct the rest to save credits."""
    data = _get("/domain-search", {"domain": domain})
    return {"pattern": data.get("pattern"),
            "emails": [e.get("value") for e in data.get("emails", [])]}


def account_balance():
    """Remaining credits — feeds the credit-lifecycle tracker."""
    data = _get("/account", {})
    calls = data.get("requests", {}).get("searches", {})
    return {"remaining": calls.get("available", 0) - calls.get("used", 0),
            "quota": calls.get("available", 0)}
