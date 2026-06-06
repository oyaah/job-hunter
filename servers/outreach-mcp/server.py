"""outreach-mcp — the load-bearing tools ONLY. Everything the model can do itself
(per-company state, the pipeline board, learnings, reflection, lifecycle) lives in
files the model edits directly; this server is just the handful of things the model
genuinely cannot do: authenticated HTTP enrichment, gated mail send, a deterministic
voice lint, and an honest cross-session LinkedIn rate guard."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import resilience  # noqa: E402

resilience.configure_logging()  # redact secrets, quiet httpx URL logging

from mcp.server.fastmcp import FastMCP  # noqa: E402

import enrichment  # noqa: E402
import usage  # noqa: E402
import guard  # noqa: E402
import voice  # noqa: E402

mcp = FastMCP("outreach")


# ------------------------------------------------------------------- enrichment
@mcp.tool()
def enrich_contact(name: str, domain: str, linkedin_url: str = "") -> dict:
    """Resolve a VERIFIED email (+phone if found) for a person via the credit-gated
    chain (Hunter→Apollo→ContactOut). `domain` is the company email domain (acme.com).
    Returns verified | unverified (a guess, never send-ready) | no_match | needs_credits.
    Write the result into the company's state file yourself. Never invents an address."""
    contact = {"name": name, "linkedin_url": linkedin_url or None}
    return enrichment.enrich(contact, domain)


@mcp.tool()
def verify_email(email: str) -> dict:
    """Verify a single email's deliverability via Hunter (records 1 credit)."""
    from integrations import hunter
    if not usage.usable("hunter", 1):
        return {"status": "needs_credits"}
    try:
        res = hunter.email_verifier(email)
    except Exception as e:  # noqa: BLE001
        if e.__class__.__name__ == "CreditError":
            usage.mark_exhausted("hunter")
        return {"status": "error", "detail": str(e)}
    usage.record("hunter", 1)
    return res


@mcp.tool()
def credits_status() -> dict:
    """Provider credit balances/usage. Refreshes Hunter from its real balance endpoint
    when a key is set; others come from the local ledger + reactive exhaustion."""
    if os.environ.get("HUNTER_API_KEY"):
        try:
            from integrations import hunter
            bal = hunter.account_balance()
            usage.seed("hunter", remaining=bal["remaining"], quota=bal["quota"])
        except Exception:  # noqa: BLE001
            pass
    return usage.status()


# ------------------------------------------------------------------------- send
# Safety rail: nothing sends unless the caller passes approved=True, which the
# review skill does ONLY after showing the draft and getting human approval.
def _gmail_creds_path():
    return os.environ.get("GMAIL_CREDENTIALS_PATH") or \
        os.path.expanduser("~/.config/job-hunter/credentials.json")


def _resolve_channel(channel):
    if channel != "auto":
        return channel
    # The user picks ONE send method at setup (userConfig send_method).
    method = (os.environ.get("SEND_METHOD") or "").strip().lower()
    if method == "gmail_mcp":
        return "gmail_mcp"      # handled by the model via its own Gmail MCP, not here
    if method == "mac_automation":
        return "local"         # osascript → Mail.app, no MCP, no keys
    if method == "app_password":
        return "smtp"
    # No explicit choice → fall back to whatever's actually configured.
    from integrations import smtp_send, localmail
    if smtp_send.configured():
        return "smtp"
    if localmail.available():
        return "local"
    return "gmail"


def _send_via(channel, to, subject, body):
    """Returns {"channel": str, "delivery": "sent"|"composed"}. "composed" means the
    local mail client opened pre-filled and the USER still has to click Send."""
    channel = _resolve_channel(channel)
    if channel == "gmail_mcp":
        # The user chose to send through a Gmail MCP they installed in Claude Code.
        # This server can't call another MCP — signal the model to do the send itself.
        return {"channel": "gmail_mcp", "delivery": "delegate"}
    if channel in ("local", "mailapp"):  # "mailapp" kept as a back-compat alias
        from integrations import localmail
        res = localmail.send(to, subject, body)
        return {"channel": res["via"], "delivery": res["delivery"]}
    if channel == "gmail":
        from integrations import gmail
        gmail.send_message(to, subject, body, _gmail_creds_path())
        return {"channel": "gmail", "delivery": "sent"}
    from integrations import smtp_send
    smtp_send.send(to, subject, body)
    return {"channel": "smtp", "delivery": "sent"}


@mcp.tool()
def send_email(to: str, subject: str, body: str, approved: bool = False,
               channel: str = "auto") -> dict:
    """Send an email. BLOCKED unless approved=True (the review gate sets this only after
    human approval).

    The user picks ONE send method at setup (userConfig send_method), and channel="auto"
    honors it: 'gmail_mcp' → returns delivery='delegate' (YOU send via the user's own
    Gmail MCP, since this server can't call another MCP); 'mac_automation' → Mail.app via
    osascript (macOS, no keys); 'app_password' → SMTP. You can also force a channel:
    auto | smtp | local | gmail. The 'local' channel uses the desktop mail client; on
    Linux (and Windows without Outlook) it opens the message pre-filled and returns
    delivery='composed' — you still click Send.
    The body is voice-linted first; lint failures block the send."""
    if not approved:
        return {"error": "send blocked — approved is false. Show the draft, get explicit "
                         "human approval at the review gate, then call with approved=True."}
    if not to:
        return {"error": "no recipient email — enrich the contact first."}
    violations = voice.lint(body)
    if violations:
        return {"error": "voice lint failed — rewrite before sending.", "violations": violations}
    try:
        used = _send_via(channel, to, subject, body)
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "detail": str(e),
                "hint": "Set GMAIL_ADDRESS/GMAIL_APP_PASSWORD, or use channel='local'."}
    if used["delivery"] == "delegate":
        return {"status": "delegate", "to": to, "channel": "gmail_mcp",
                "subject": subject, "body": body,
                "note": "send_method=gmail_mcp — this draft is approved + voice-linted. "
                        "Send it now via the user's installed Gmail MCP (its send/create-message "
                        "tool), then mark the draft sent. Do NOT re-lint or re-ask approval."}
    status = "sent" if used["delivery"] == "sent" else "composed"
    out = {"status": status, "to": to, "channel": used["channel"], "delivery": used["delivery"]}
    if used["delivery"] == "composed":
        out["note"] = "Opened in your local mail client — click Send to actually deliver it."
    return out


# ------------------------------------------------------------------- voice lint
@mcp.tool()
def voice_lint(text: str) -> dict:
    """Deterministic anti-AI check: em/en-dashes, banned AI openers, filler words.
    Returns violations (empty = clean). Run on every draft before review."""
    return {"violations": voice.lint(text), "clean": voice.is_clean(text)}


# -------------------------------------------------------------- LinkedIn guard
@mcp.tool()
def linkedin_guard(action: str = "connect") -> dict:
    """Pre-flight rate guard — call BEFORE any mcp__linkedin__connect_with_person /
    send_message. action = connect | message. Returns ok+remaining or blocked+reason
    at the generous daily cap. Never perform the action when ok is false."""
    return guard.guard(action)


@mcp.tool()
def linkedin_record(action: str = "connect") -> dict:
    """Count one performed LinkedIn action toward today's cap (call after a successful
    connect/message)."""
    return {"action": action, "today": guard.record(action)}


# ------------------------------------------------------------------------ health
@mcp.tool()
def health() -> dict:
    """Readiness at a glance: which credentials are set (names only), which send
    channels are available, the LinkedIn daily count. Surfaces no secrets."""
    out = {"credentials": {k: bool(os.environ.get(f"{k.upper()}_API_KEY"))
                           for k in ("hunter", "apollo", "contactout", "lemlist")},
           "send_method": (os.environ.get("SEND_METHOD") or "unset"),
           "email_channels": [], "linkedin_today": guard.used_today("connect")}
    try:
        from integrations import smtp_send, localmail
        if smtp_send.configured():
            out["email_channels"].append("smtp")
        if localmail.available():
            out["email_channels"].append(f"local ({localmail.describe()})")
        if os.environ.get("GMAIL_CREDENTIALS_PATH") or os.path.exists(
                os.path.expanduser("~/.config/job-hunter/credentials.json")):
            out["email_channels"].append("gmail-oauth")
    except Exception:  # noqa: BLE001
        pass
    out["ready_to_send"] = bool(out["email_channels"])
    return out


def main():
    mcp.run()


if __name__ == "__main__":
    main()
