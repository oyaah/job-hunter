"""LinkedIn — READ-ONLY, OPT-IN acceptance detection only (KTD6).

This module NEVER sends connection requests or messages. The agent drafts and
queues; the user clicks Send by hand. The only thing here is an optional poll to
notice when a request the user sent has been accepted, so the prepared DM can
surface for review. It uses the unofficial Voyager endpoint with the user's own
session cookie, runs on a slow cadence, and is disabled by default. If you're
uncomfortable with the unofficial API, leave the poller off and use the manual
'I got connected with X' path instead — the workflow works fully without it."""
import os

VOYAGER = "https://www.linkedin.com/voyager/api"


def _cookie():
    c = os.environ.get("LINKEDIN_LI_AT")
    if not c:
        raise RuntimeError("LINKEDIN_LI_AT not set — poller disabled")
    return c


def get_accepted_connections():
    """Return a list of recently-accepted connections [{name, profile}], read-only.
    Best-effort against the unofficial Voyager API; returns [] on any failure rather
    than raising, since this is a non-critical convenience."""
    import httpx
    li_at = _cookie()
    headers = {
        "csrf-token": os.environ.get("LINKEDIN_CSRF", "ajax:0"),
        "cookie": f"li_at={li_at}; JSESSIONID=\"ajax:0\"",
        "accept": "application/json",
    }
    try:
        r = httpx.get(f"{VOYAGER}/relationships/connections",
                      params={"start": 0, "count": 20, "sortType": "RECENTLY_ADDED"},
                      headers=headers, timeout=20)
        r.raise_for_status()
        out = []
        for el in r.json().get("elements", []):
            mp = el.get("miniProfile", {})
            name = f"{mp.get('firstName','')} {mp.get('lastName','')}".strip()
            if name:
                out.append({"name": name, "profile": mp.get("publicIdentifier")})
        return out
    except Exception:
        return []
