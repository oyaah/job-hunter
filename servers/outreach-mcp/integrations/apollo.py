"""Apollo.io — optional, PAID for programmatic enrichment. search→enrich is two
calls: api_search (no credits, IDs only) then people/match (costs credits, returns
email/phone). Gate sends on email_status == 'verified'. httpx lazy."""
import os

BASE = "https://api.apollo.io/api/v1"


class CreditError(Exception):
    pass


def _headers():
    k = os.environ.get("APOLLO_API_KEY")
    if not k:
        raise RuntimeError("APOLLO_API_KEY not set")
    return {"X-Api-Key": k, "Content-Type": "application/json"}


def _post(path, payload):
    import httpx
    r = httpx.post(f"{BASE}{path}", json=payload, headers=_headers(), timeout=25)
    if r.status_code in (402, 403, 429):
        raise CreditError(f"apollo {r.status_code}")
    r.raise_for_status()
    return r.json()


def api_search(person_titles, org_domains, per_page=10):
    """API-optimized people search. No credits, no emails — returns person metadata/IDs."""
    data = _post("/mixed_people/api_search", {
        "person_titles": person_titles,
        "q_organization_domains_list": org_domains,
        "per_page": per_page,
    })
    return data.get("people", [])


def people_match(first_name, last_name, domain, reveal_phone=False):
    """Enrichment — costs credits. Returns {email, email_status, phone}."""
    payload = {"first_name": first_name, "last_name": last_name,
               "domain": domain, "reveal_personal_emails": True}
    if reveal_phone:
        payload["reveal_phone_number"] = True
    data = _post("/people/match", payload)
    person = data.get("person") or {}
    return {
        "email": person.get("email"),
        "email_status": person.get("email_status", "unavailable"),
        "phone": (person.get("phone_numbers") or [{}])[0].get("raw_number"),
        "source": "apollo",
    }
