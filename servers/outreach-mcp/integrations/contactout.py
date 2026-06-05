"""ContactOut — last-resort enrichment. PAID, no self-serve API key (request via
sales), and API match-rate is lower than its (un-automatable) browser extension.
Only used when the user has a seat. httpx lazy."""
import os

from ._base import CreditError  # noqa: F401

BASE = "https://api.contactout.com/v1"


def _headers():
    k = os.environ.get("CONTACTOUT_API_KEY")
    if not k:
        raise RuntimeError("CONTACTOUT_API_KEY not set")
    return {"token": k, "authorization": f"Basic {k}"}


def linkedin_enrich(linkedin_url):
    """Standard linkedin.com/in/ URL → {email, phone}. Rejects Sales Nav/Recruiter URLs."""
    import httpx
    if "/sales/" in linkedin_url or "/recruiter/" in linkedin_url:
        return None
    r = httpx.get(f"{BASE}/linkedin/enrich",
                  params={"profile": linkedin_url}, headers=_headers(), timeout=25)
    if r.status_code in (402, 403, 429):
        raise CreditError(f"contactout {r.status_code}")
    r.raise_for_status()
    data = r.json().get("profile", {})
    emails = data.get("email", []) or data.get("work_email", [])
    phones = data.get("phone", [])
    if not emails:
        return None
    return {"email": emails[0], "email_status": "guessed",
            "phone": phones[0] if phones else None, "source": "contactout"}
