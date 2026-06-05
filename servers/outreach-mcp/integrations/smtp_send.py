"""SMTP send via a Gmail App Password — the simple, cross-platform default.

stdlib only (smtplib), so it runs identically on macOS / Windows / Linux and under
any harness that runs this MCP server (Claude Code, Codex, Codex terminal). No OAuth,
no Cloud Console, no token expiry — the user generates one App Password and that's it.

Env: GMAIL_ADDRESS (the from address) + GMAIL_APP_PASSWORD (16-char app password)."""
import os
import smtplib
from email.mime.text import MIMEText

HOST = "smtp.gmail.com"
PORT = 465  # SSL


def _creds():
    addr = os.environ.get("GMAIL_ADDRESS")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not addr or not pw:
        raise RuntimeError("GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set — run /job-hunter:setup")
    return addr, pw


def _hdr(value):
    # Strip CR/LF so a crafted to/subject can't inject extra headers.
    return (value or "").replace("\r", " ").replace("\n", " ")


def build(from_addr, to, subject, body):
    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = _hdr(from_addr)
    msg["To"] = _hdr(to)
    msg["Subject"] = _hdr(subject)
    return msg


def send(to, subject, body):
    """Send an email from the user's Gmail via SMTP+SSL. Returns True on success."""
    addr, pw = _creds()
    msg = build(addr, to, subject, body)
    with smtplib.SMTP_SSL(HOST, PORT, timeout=30) as s:
        s.login(addr, pw)
        s.send_message(msg)
    return True


def configured():
    return bool(os.environ.get("GMAIL_ADDRESS") and os.environ.get("GMAIL_APP_PASSWORD"))
