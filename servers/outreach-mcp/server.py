"""outreach-mcp — FastMCP server. All job-hunter state, credit, and (later)
integration tools live here. Thin skills + worker agents call these tools;
the heavy logic stays server-side to keep agent context lean (KTD1)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP  # noqa: E402

import store  # noqa: E402
import state  # noqa: E402
import credits  # noqa: E402
import enrichment  # noqa: E402
import learnings  # noqa: E402
import distill  # noqa: E402
import voice  # noqa: E402

mcp = FastMCP("outreach")

# One shared connection for the process. State lives in $DATA_DIR/job-hunter.db.
_conn = store.connect_default()


# ---------------------------------------------------------------- state tools
@mcp.tool()
def state_get(company_slug: str) -> dict:
    """Full nested record for ONE company (contacts + messages + LinkedIn).
    Load only the company you are working on — this is the context-isolation unit."""
    rec = state.get_company(_conn, company_slug)
    return rec or {"error": f"no company '{company_slug}'"}


@mcp.tool()
def upsert_company(slug: str, name: str, status: str = "", fit_score: float = 0.0,
                   notes: str = "") -> dict:
    """Create or update a company record."""
    state.upsert_company(_conn, slug, name, status=status or None,
                         fit_score=fit_score or None, notes=notes or None)
    return state.get_company(_conn, slug)


@mcp.tool()
def set_company_status(slug: str, status: str) -> dict:
    """Advance a company's lifecycle: new|targeted|enriched|researched|drafted|review|sent|done."""
    state.set_company_status(_conn, slug, status)
    return {"slug": slug, "status": status}


@mcp.tool()
def add_contact(company_slug: str, name: str, role: str = "", linkedin_url: str = "",
                hook: str = "") -> dict:
    """Add a target person to a company. Returns the new contact id."""
    cid = state.add_contact(_conn, company_slug, name, role=role or None,
                            linkedin_url=linkedin_url or None, hook=hook or None)
    return {"contact_id": cid}


@mcp.tool()
def update_contact(contact_id: int, email: str = "", email_status: str = "",
                   email_score: int = 0, phone: str = "", hook: str = "",
                   enrichment_source: str = "", research_digest: str = "") -> dict:
    """Patch contact fields (enrichment / research results). Empty args are ignored."""
    fields = {k: v for k, v in dict(
        email=email, email_status=email_status, email_score=email_score or None,
        phone=phone, hook=hook, enrichment_source=enrichment_source,
        research_digest=research_digest).items() if v}
    state.update_contact(_conn, contact_id, **fields)
    return state.get_contact(_conn, contact_id)


@mcp.tool()
def add_message(contact_id: int, channel: str, body: str, subject: str = "") -> dict:
    """Store a draft message (channel = email|li_note|li_dm). Status starts 'draft'.
    Safety rail: the anti-AI voice lint runs here — a body with em/en-dashes or banned
    AI cadence is rejected (not stored) so the rail can't be bypassed by skipping a skill."""
    violations = voice.lint(body)
    if violations:
        return {"error": "voice lint failed — rewrite before storing.",
                "violations": violations}
    mid = state.add_message(_conn, contact_id, channel, body, subject=subject or None)
    return {"message_id": mid, "status": "draft"}


@mcp.tool()
def set_message_status(message_id: int, status: str) -> dict:
    """draft|approved|rejected|sent. 'sent' stamps sent_at."""
    state.set_message_status(_conn, message_id, status, sent=(status == "sent"))
    return {"message_id": message_id, "status": status}


@mcp.tool()
def list_pending_messages() -> list:
    """All draft + approved-not-sent messages for the review gate."""
    return state.list_pending_messages(_conn)


@mcp.tool()
def upsert_linkedin(contact_id: int, note: str = "", dm: str = "",
                    status: str = "DRAFTED") -> dict:
    """Store the LinkedIn connection note + DM for a contact."""
    state.upsert_linkedin(_conn, contact_id, note=note or None, dm=dm or None, status=status)
    return {"contact_id": contact_id, "status": status}


@mcp.tool()
def set_linkedin_status(contact_id: int, status: str) -> dict:
    """DRAFTED|QUEUED|SENT|ACCEPTED|EXPIRED|DM_REVIEW|DM_SENT. Stamps timestamps on transitions."""
    state.set_linkedin_status(_conn, contact_id, status)
    return {"contact_id": contact_id, "status": status}


@mcp.tool()
def pipeline_board() -> list:
    """One row per company: status + contact/sent counts. For /job-hunter:status."""
    return state.pipeline_board(_conn)


# --------------------------------------------------------------- credit tools
@mcp.tool()
def credits_seed(service: str, account_id: str = "default", remaining: int = 0,
                 monthly_quota: int = 0, reset_at: str = "") -> dict:
    """Initialize/refresh a service+account credit row (from a balance-endpoint poll)."""
    credits.seed(_conn, service, account_id, remaining=remaining,
                 monthly_quota=monthly_quota or None, reset_at=reset_at or None)
    return credits.check(_conn, service, account_id)


@mcp.tool()
def credits_check(service: str, account_id: str = "default") -> dict:
    """Current cached balance/status for one service+account."""
    return credits.check(_conn, service, account_id) or {"error": "no such credit row"}


@mcp.tool()
def credits_record(service: str, account_id: str, op: str, cost: int,
                   contact_id: int = 0) -> dict:
    """Log a billable op and decrement the cached balance."""
    remaining = credits.record(_conn, service, account_id, op, cost,
                               contact_id=contact_id or None)
    return {"service": service, "account_id": account_id, "remaining": remaining}


@mcp.tool()
def credits_pick(op: str) -> dict:
    """Pick the first usable provider/account for an op (enrich|email_find|verify|phone|search),
    or signal exhaustion. Never returns a provider that would fail for lack of credits."""
    pick = credits.pick_provider(_conn, op)
    if pick is None:
        return {"provider": None, "reason": "all providers exhausted or under-credited"}
    return {"provider": pick[0], "account_id": pick[1]}


@mcp.tool()
def credits_mark_exhausted(service: str, account_id: str = "default", reset_at: str = "") -> dict:
    """Mark a service+account exhausted after catching a 402/403/429."""
    credits.mark_exhausted(_conn, service, account_id, reset_at=reset_at or None)
    return credits.check(_conn, service, account_id)


@mcp.tool()
def credits_balances() -> list:
    """All credit rows — for the status board and SessionStart summary."""
    return credits.balances(_conn)


# ----------------------------------------------------------- enrichment tools
@mcp.tool()
def enrich_contact(contact_id: int, domain: str) -> dict:
    """Resolve a verified email/phone for a contact via the credit-gated chain
    (Hunter→Apollo→ContactOut). `domain` is the company's email domain (e.g. acme.com).
    On a verified hit the contact row is updated. Never returns a guessed address as verified."""
    contact = state.get_contact(_conn, contact_id)
    if not contact:
        return {"error": f"no contact {contact_id}"}
    # Don't re-enrich (or downgrade) a contact that already has a verified email.
    if contact.get("email_status") == "verified":
        return {"status": "verified", "email": contact["email"],
                "phone": contact.get("phone"), "source": contact.get("enrichment_source"),
                "note": "already verified — skipped re-enrichment"}
    res = enrichment.enrich(_conn, contact, domain)
    if res["status"] in ("verified", "unverified"):
        state.update_contact(
            _conn, contact_id, email=res["email"],
            email_status=("verified" if res["status"] == "verified" else "guessed"),
            phone=res.get("phone") or "", enrichment_source=res.get("source") or "")
    return res


@mcp.tool()
def verify_email(email: str) -> dict:
    """Verify a single email's deliverability via Hunter (records 1 credit)."""
    from integrations import hunter
    pick = credits.pick_provider(_conn, "verify")
    if not pick:
        return {"status": "needs_credits"}
    service, account = pick
    try:
        res = hunter.email_verifier(email)
    except Exception as e:  # noqa: BLE001
        if e.__class__.__name__ == "CreditError":
            credits.mark_exhausted(_conn, service, account)
        return {"status": "error", "detail": str(e)}
    credits.record(_conn, service, account, "verify", 1)
    return res


# -------------------------------------------------------------- send tools
# Safety rail #1 (CLAUDE.md): nothing sends unless the message is 'approved'.
# Enforced here at the tool layer, not just in the review skill — defense in depth.
def _gmail_creds_path():
    return os.environ.get("GMAIL_CREDENTIALS_PATH") or \
        os.path.expanduser("~/.config/job-hunter/credentials.json")


def _require_approved(message_id):
    row = _conn.execute("SELECT m.*, ct.email AS to_email FROM messages m "
                        "JOIN contacts ct ON ct.id=m.contact_id WHERE m.id=?",
                        (message_id,)).fetchone()
    if not row:
        return None, {"error": f"no message {message_id}"}
    if row["status"] != "approved":
        return None, {"error": f"message {message_id} is '{row['status']}', not 'approved'. "
                               "Send blocked — it must clear the review gate first."}
    return dict(row), None


@mcp.tool()
def gmail_draft(message_id: int) -> dict:
    """Create a Gmail draft for an APPROVED message so the user sees the exact bytes
    before it sends. Returns the draft id."""
    msg, err = _require_approved(message_id)
    if err:
        return err
    if not msg["to_email"]:
        return {"error": f"message {message_id} has no contact email — enrich first."}
    try:
        from integrations import gmail
        draft_id = gmail.create_draft(msg["to_email"], msg["subject"] or "", msg["body"],
                                      _gmail_creds_path())
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "detail": str(e),
                "hint": "Gmail auth may have expired (Testing-mode ~weekly). Re-run /job-hunter:setup."}
    return {"message_id": message_id, "gmail_draft_id": draft_id}


def _claim_for_send(message_id):
    """Atomically transition approved -> sending so two concurrent calls can't both
    send (race) and a crash mid-send can't leave it resendable. Returns the row or None."""
    cur = _conn.execute(
        "UPDATE messages SET status='sending' WHERE id=? AND status='approved'", (message_id,))
    _conn.commit()
    if cur.rowcount == 0:
        return None
    row = _conn.execute("SELECT m.*, ct.email AS to_email FROM messages m "
                        "JOIN contacts ct ON ct.id=m.contact_id WHERE m.id=?",
                        (message_id,)).fetchone()
    return dict(row) if row else None


@mcp.tool()
def send_email(message_id: int, channel: str = "gmail") -> dict:
    """Send an APPROVED email. channel = gmail (default) | mailapp (local macOS Mail,
    zero-OAuth fallback). Atomically claims the message before sending so it can't
    double-send; marks 'sent' on success, reverts to 'approved' on failure."""
    msg = _claim_for_send(message_id)
    if msg is None:
        row = _conn.execute("SELECT status FROM messages WHERE id=?", (message_id,)).fetchone()
        cur = row["status"] if row else "missing"
        return {"error": f"message {message_id} not sendable (status='{cur}'). It must be "
                         f"'approved' and not already sending/sent."}
    if not msg["to_email"]:
        state.set_message_status(_conn, message_id, "approved")  # release claim
        return {"error": f"message {message_id} has no contact email — enrich first."}
    try:
        if channel == "mailapp":
            from integrations import mailapp
            mailapp.send(msg["to_email"], msg["subject"] or "", msg["body"])
        else:
            from integrations import gmail
            gmail.send_message(msg["to_email"], msg["subject"] or "", msg["body"],
                               _gmail_creds_path())
    except Exception as e:  # noqa: BLE001
        state.set_message_status(_conn, message_id, "approved")  # revert claim, allow retry
        return {"status": "error", "detail": str(e),
                "hint": "Gmail token may have expired (Testing-mode ~weekly). "
                        "Re-run /job-hunter:setup, or retry with channel='mailapp'."}
    state.set_message_status(_conn, message_id, "sent", sent=True)
    return {"message_id": message_id, "status": "sent", "channel": channel}


@mcp.tool()
def lemlist_push(message_id: int, campaign_id: str) -> dict:
    """Optional: push an APPROVED contact into an existing Lemlist campaign for sequenced
    follow-up (paid; user must have a seat)."""
    msg, err = _require_approved(message_id)
    if err:
        return err
    contact = state.get_contact(_conn, msg["contact_id"])
    from integrations import lemlist, CreditError
    try:
        lemlist.add_lead(campaign_id, contact["email"], first_name=contact["name"].split()[0],
                         job_title=contact.get("role"), linkedin_url=contact.get("linkedin_url"),
                         phone=contact.get("phone"))
    except CreditError:
        credits.mark_exhausted(_conn, "lemlist", "default")
        return {"status": "needs_credits", "detail": "Lemlist credits exhausted."}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "detail": str(e)}
    state.set_message_status(_conn, message_id, "sent", sent=True)
    return {"message_id": message_id, "pushed_to": campaign_id, "status": "sent"}


# ------------------------------------------------------------- LinkedIn (semi-auto)
# The agent prepares + queues; the USER sends by hand. No tool here ever connects
# or messages on LinkedIn (KTD6). These only track lifecycle + surface the DM.
@mcp.tool()
def linkedin_queue(contact_id: int, note: str = "", dm: str = "") -> dict:
    """Queue an approved LinkedIn connection note (+ prepared DM) for the user to send
    MANUALLY. Sets status QUEUED. Does not send anything."""
    if note or dm:
        state.upsert_linkedin(_conn, contact_id, note=note or None, dm=dm or None)
    state.set_linkedin_status(_conn, contact_id, "QUEUED")
    return {"contact_id": contact_id, "status": "QUEUED",
            "action_required": "User: send this connection request in LinkedIn by hand."}


@mcp.tool()
def linkedin_sent(contact_id: int) -> dict:
    """Mark that the USER has manually sent the queued connection request (QUEUED→SENT).
    Now we wait for acceptance (manual signal or the opt-in poller)."""
    state.set_linkedin_status(_conn, contact_id, "SENT")
    return {"contact_id": contact_id, "status": "SENT"}


@mcp.tool()
def linkedin_accepted(contact_id: int) -> dict:
    """Record that a connection was accepted (manual path or poller). Advances to
    DM_REVIEW and returns the prepared DM so it can go through the review gate.
    The user still sends the DM by hand."""
    state.set_linkedin_status(_conn, contact_id, "ACCEPTED")
    state.set_linkedin_status(_conn, contact_id, "DM_REVIEW")
    li = _conn.execute("SELECT dm FROM linkedin WHERE contact_id=?", (contact_id,)).fetchone()
    return {"contact_id": contact_id, "status": "DM_REVIEW",
            "prepared_dm": li["dm"] if li else None,
            "action_required": "Review the DM, then the user sends it in LinkedIn by hand."}


@mcp.tool()
def linkedin_awaiting() -> list:
    """Contacts whose connection request is SENT and awaiting acceptance."""
    rows = _conn.execute(
        "SELECT c.id, c.name, c.company_slug, l.sent_at FROM contacts c "
        "JOIN linkedin l ON l.contact_id=c.id WHERE l.status='SENT' ORDER BY l.sent_at").fetchall()
    return [dict(r) for r in rows]


# ----------------------------------------------------- self-evolving learnings
@mcp.tool()
def learning_record(category: str, insight: str, source: str = "explicit") -> dict:
    """Capture something learned about THIS user (category = voice|targeting|enrichment|
    outreach|general). Call this whenever the user edits a draft, rejects a target, or
    states a preference — the next run loads it. Repeats reinforce, they don't duplicate."""
    learnings.record(_conn, category, insight, source=source)
    return {"category": category, "insight": insight, "recorded": True}


@mcp.tool()
def learnings_get(category: str = "") -> list:
    """Load accumulated understanding of the user. Read this BEFORE targeting or drafting
    so the workflow applies what it already knows. Empty category = everything."""
    return learnings.get(_conn, category or None)


@mcp.tool()
def learnings_context() -> str:
    """All learnings rendered as a compact prompt block — the system's current
    understanding of the user, ready to inject before a decision."""
    return learnings.as_context(_conn)


# -------------------------------------------- reflection / distillation (self-evolving)
@mcp.tool()
def reflection_due(category: str = "") -> dict:
    """Check if enough new signal accumulated to distill it into a durable profile
    (importance-sum threshold). Returns the material to compress if due. Cheap: the
    model already in the loop does the distilling — no extra API call. Call this at
    natural breaks (e.g. after a company in /hunt)."""
    cat = category or None
    due = distill.is_due(_conn, cat)
    return {"due": due, "pending_weight": distill.pending_weight(_conn, cat),
            "threshold": distill.THRESHOLD,
            "material": distill.material(_conn, cat) if due else []}


@mcp.tool()
def reflection_apply(section: str, content: str) -> dict:
    """Save the model's distilled principles as the compact profile for a section
    (voice|targeting). Byte-capped (curate, not accumulate); marks that category's
    pending learnings distilled so they don't re-trigger. Takes effect next load,
    not mid-draft."""
    return distill.apply(_conn, section, content)


@mcp.tool()
def profile_get(section: str) -> str:
    """The current distilled profile for a section (voice|targeting). Load this
    before drafting/targeting — it's the compressed, durable version of everything
    learned, cheaper to carry than the raw learnings."""
    return distill.get_profile(_conn, section)


# ----------------------------------------------------- credit lifecycle (R11)
@mcp.tool()
def credits_refresh(service: str = "hunter", account_id: str = "default") -> dict:
    """Poll the provider's balance endpoint (source of truth) and update the cached row.
    Currently Hunter exposes a free balance endpoint; others are tracked via the ledger
    + reactive 402/429 detection. Use this to reconcile drift."""
    if service != "hunter":
        return {"service": service, "note": "no balance endpoint; tracked via ledger + 402/429"}
    from integrations import hunter
    try:
        bal = hunter.account_balance()
    except Exception as e:  # noqa: BLE001
        if e.__class__.__name__ == "CreditError":
            credits.mark_exhausted(_conn, service, account_id)
            return credits.check(_conn, service, account_id)
        return {"status": "error", "detail": str(e)}
    credits.seed(_conn, service, account_id,
                 remaining=bal["remaining"], monthly_quota=bal["quota"])
    return credits.check(_conn, service, account_id)


@mcp.tool()
def credits_add_account(service: str, account_id: str, remaining: int = 0,
                        monthly_quota: int = 0) -> dict:
    """Register an additional account for a service so the chain can rotate to it when
    the primary is exhausted. NOTE: rotating fresh free accounts to dodge limits violates
    most providers' ToS — surface this to the user; never do it silently."""
    credits.seed(_conn, service, account_id, remaining=remaining,
                 monthly_quota=monthly_quota or None)
    return {"service": service, "account_id": account_id, "registered": True,
            "warning": "Rotating free accounts to extend credits violates most providers' "
                       "Terms of Service. Use a paid plan for sustained volume."}


if __name__ == "__main__":
    mcp.run()
