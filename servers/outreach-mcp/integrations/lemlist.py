"""Lemlist — optional sequencing backend (KTD3). No free tier, so only used when
the user has a paid seat. Campaign authoring is UI-gated; the API injects leads
into a campaign the user already built. Basic auth: blank username, API key as
password. httpx lazy."""
import os

from ._base import CreditError  # noqa: F401

BASE = "https://api.lemlist.com/api"


def _auth():
    k = os.environ.get("LEMLIST_API_KEY")
    if not k:
        raise RuntimeError("LEMLIST_API_KEY not set")
    return ("", k)  # blank user, key as password


def list_campaigns():
    import httpx
    r = httpx.get(f"{BASE}/campaigns", auth=_auth(), timeout=20)
    r.raise_for_status()
    return r.json()


def add_lead(campaign_id, email, first_name=None, last_name=None,
             company_name=None, job_title=None, linkedin_url=None, phone=None):
    """Add (or create + insert) a lead into an existing campaign. Sender = campaign owner."""
    import httpx
    payload = {k: v for k, v in {
        "firstName": first_name, "lastName": last_name, "companyName": company_name,
        "jobTitle": job_title, "linkedinUrl": linkedin_url, "phone": phone,
    }.items() if v}
    r = httpx.post(f"{BASE}/campaigns/{campaign_id}/leads/{email}",
                   json=payload, auth=_auth(), timeout=25)
    if r.status_code in (402, 403, 429):
        raise CreditError(f"lemlist {r.status_code}")
    r.raise_for_status()
    return r.json()
