"""Enrichment orchestration — the credit-gated fallback chain (Hunter → Apollo →
ContactOut). Pre-flight credit-checks each provider so it never fires a doomed
call, gates acceptance on a VERIFIED email, and never returns a guessed address as
final. Returns the result to the caller (the model writes it into the company
file) — no DB. Provider adapters live in `_ADAPTERS` so tests swap them sans HTTP."""
import sys

import usage

ACCEPT_SCORE = 70  # Hunter confidence threshold for "verified enough"
COST = {"hunter": 1, "apollo": 1, "contactout": 1}


def _split_name(name):
    parts = (name or "").split()
    return (parts[0] if parts else ""), (parts[-1] if len(parts) > 1 else "")


def _adapt_hunter(contact, domain):
    from integrations import hunter
    first, last = _split_name(contact["name"])
    res = hunter.email_finder(domain, first, last)
    if not res:
        return None
    verified = res["status"] == "valid" or res["score"] >= ACCEPT_SCORE
    return {"email": res["email"], "phone": None, "score": res["score"],
            "email_status": "verified" if verified else "guessed",
            "verified": verified, "source": "hunter"}


def _adapt_apollo(contact, domain):
    from integrations import apollo
    first, last = _split_name(contact["name"])
    res = apollo.people_match(first, last, domain, reveal_phone=True)
    if not res.get("email"):
        return None
    verified = res["email_status"] == "verified"
    return {"email": res["email"], "phone": res.get("phone"), "score": None,
            "email_status": res["email_status"], "verified": verified, "source": "apollo"}


def _adapt_contactout(contact, domain):
    from integrations import contactout
    if not contact.get("linkedin_url"):
        return None
    res = contactout.linkedin_enrich(contact["linkedin_url"])
    if not res:
        return None
    return {"email": res["email"], "phone": res.get("phone"), "score": None,
            "email_status": "guessed", "verified": False, "source": "contactout"}


_ADAPTERS = {"hunter": _adapt_hunter, "apollo": _adapt_apollo, "contactout": _adapt_contactout}


def enrich(contact, domain):
    """Resolve a verified email (+phone if available) for one contact via the chain.
    Returns one of:
      {status:'verified', email, phone, source}
      {status:'unverified', email, source}   # best guess, never treated as verified
      {status:'needs_credits', detail}
      {status:'no_match'}
    """
    from integrations import CreditError

    best_guess = None
    ran_any = False
    any_credits = False
    for service, _ in usage.CHAINS["email_find"]:
        if service not in _ADAPTERS:
            continue
        cost = COST.get(service, 1)
        if not usage.usable(service, cost):
            continue
        any_credits = True
        try:
            result = _ADAPTERS[service](contact, domain)
        except CreditError:
            usage.mark_exhausted(service)
            continue
        except Exception as e:  # noqa: BLE001
            print(f"[job-hunter] enrich via {service} failed: {e!r}", file=sys.stderr)
            continue
        ran_any = True
        usage.record(service, cost)
        if result is None:
            continue
        if result["verified"]:
            return {"status": "verified", "email": result["email"],
                    "phone": result.get("phone"), "source": result["source"]}
        best_guess = best_guess or result

    if best_guess:
        return {"status": "unverified", "email": best_guess["email"],
                "source": best_guess["source"]}
    if not any_credits:
        return {"status": "needs_credits",
                "detail": "all enrichment providers exhausted or uncredited"}
    if ran_any:
        return {"status": "no_match"}
    return {"status": "needs_credits", "detail": "no usable provider"}
