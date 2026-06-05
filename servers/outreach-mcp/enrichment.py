"""Enrichment orchestration — the credit-gated fallback chain (KTD5, R3, R11).

Walks Hunter → Apollo → ContactOut, pre-flight credit-checking each so it never
fires a doomed call, gating acceptance on a VERIFIED email and never returning a
guessed address as final. Provider adapters live in `_ADAPTERS` so tests can
swap them without HTTP."""
import credits

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


def _usable_account(conn, service, cost):
    rows = conn.execute(
        "SELECT account_id, remaining, status FROM credits WHERE service=? "
        "ORDER BY (account_id='default') DESC, account_id ASC", (service,)).fetchall()
    for r in rows:
        if r["status"] != "exhausted" and r["remaining"] >= cost:
            return r["account_id"]
    return None


def enrich(conn, contact, domain):
    """Resolve a verified email (+phone if available) through the chain.

    Returns one of:
      {status:'verified', email, phone, source}
      {status:'unverified', email, source}   # best guess, no verified hit
      {status:'needs_credits', detail}       # every provider exhausted/uncredited
      {status:'no_match'}                    # providers ran but found nothing
    """
    from integrations.hunter import CreditError as HunterCE
    try:
        from integrations.apollo import CreditError as ApolloCE
    except Exception:
        ApolloCE = HunterCE

    best_guess = None
    ran_any = False
    any_credits = False
    for service, _ in credits.CHAINS["email_find"]:
        if service not in _ADAPTERS:
            continue
        cost = COST.get(service, 1)
        account = _usable_account(conn, service, cost)
        if account is None:
            continue
        any_credits = True
        try:
            result = _ADAPTERS[service](contact, domain)
        except (HunterCE, ApolloCE, Exception) as e:  # noqa: BLE001
            # CreditError → mark exhausted and advance; other errors → skip provider
            if e.__class__.__name__ == "CreditError":
                credits.mark_exhausted(conn, service, account)
            continue
        ran_any = True
        credits.record(conn, service, account, "email_find", cost, contact.get("id"))
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
