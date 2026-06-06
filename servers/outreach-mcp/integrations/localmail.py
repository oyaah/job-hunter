"""Local mail-client send — the zero-OAuth, zero-API-key fallback, on every OS.

Sends through whatever desktop mail client the user is already signed into (their
Gmail, Outlook, whatever), so there are no keys to manage and nothing leaves the
machine except the mail itself.

Reality is not uniform across platforms, and this module is honest about it:

  - macOS   → Mail.app via AppleScript. Truly **sends**.
  - Windows → Outlook via PowerShell COM if Outlook is installed. Truly **sends**.
              Otherwise the OS default mail client is opened with the message
              pre-filled (**composed** — the user clicks Send).
  - Linux   → xdg-email / Thunderbird open a pre-filled compose window
              (**composed** — the user clicks Send). No reliable headless send.

So `send()` returns {"delivery": "sent"} when the message actually went out, or
{"delivery": "composed"} when it was only opened pre-filled for the user to send.
Callers MUST surface that difference — "composed" is not "sent".

Security: user-controlled to/subject/body are never interpolated into a shell or
script string. macOS passes them as osascript argv; Windows passes them as
environment variables read inside the script; Linux passes them as separate
process args or a percent-encoded mailto URI. No string-literal breakout is possible.
"""
import platform
import shutil
import subprocess
from urllib.parse import quote


# --------------------------------------------------------------------- backend

def _backend():
    system = platform.system()
    if system == "Darwin":
        return "macos" if shutil.which("osascript") else None
    if system == "Windows":
        # We can always at least open the default client via `start mailto:`.
        return "windows"
    if system == "Linux":
        if shutil.which("xdg-email"):
            return "linux-xdg"
        if shutil.which("thunderbird"):
            return "linux-thunderbird"
        return None
    return None


def available():
    """True if some local mail path exists on this machine."""
    return _backend() is not None


def describe():
    """Human-readable name of the active backend, for /setup and health()."""
    return {
        "macos": "macOS Mail.app (sends)",
        "windows": "Windows Outlook/default client (sends if Outlook, else composes)",
        "linux-xdg": "Linux xdg-email (composes — you click Send)",
        "linux-thunderbird": "Linux Thunderbird (composes — you click Send)",
    }.get(_backend())


# ----------------------------------------------------------------------- macOS

# Fields arrive as `on run argv`, never interpolated into the script text, so
# newlines/quotes/backslashes in the body are literal and injection is impossible.
_MACOS_SCRIPT = '''
on run argv
    set theTo to item 1 of argv
    set theSubject to item 2 of argv
    set theBody to item 3 of argv
    tell application "Mail"
        set newMsg to make new outgoing message with properties {subject:theSubject, content:theBody, visible:false}
        tell newMsg
            make new to recipient at end of to recipients with properties {address:theTo}
            send
        end tell
    end tell
end run
'''


def _send_macos(to, subject, body):
    proc = subprocess.run(["osascript", "-e", _MACOS_SCRIPT, to, subject, body],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Mail.app send failed: {proc.stderr.strip()}")
    return {"delivery": "sent", "via": "macos-mail"}


# --------------------------------------------------------------------- Windows

# Read fields from env vars inside the script (never string-interpolated), so a
# crafted subject/body can't break out of the PowerShell command.
_OUTLOOK_PS = (
    "$o = New-Object -ComObject Outlook.Application; "
    "$m = $o.CreateItem(0); "
    "$m.To = $env:JH_TO; $m.Subject = $env:JH_SUBJECT; $m.Body = $env:JH_BODY; "
    "$m.Send()"
)


def _send_windows(to, subject, body):
    import os
    env = {**os.environ, "JH_TO": to, "JH_SUBJECT": subject, "JH_BODY": body}
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _OUTLOOK_PS],
        capture_output=True, text=True, env=env)
    if proc.returncode == 0:
        return {"delivery": "sent", "via": "windows-outlook"}
    # Outlook not installed / COM unavailable → open the default client pre-filled.
    uri = _mailto(to, subject, body)
    # `start` is a cmd builtin; `""` is the (empty) window title so the URI isn't
    # mistaken for one. The URI is percent-encoded, so no quoting breakout.
    subprocess.run(["cmd", "/c", "start", "", uri], check=True)
    return {"delivery": "composed", "via": "windows-mailto"}


# ----------------------------------------------------------------------- Linux

def _send_linux(to, subject, body):
    backend = _backend()
    if backend == "linux-xdg":
        # Separate args — no shell, no encoding pitfalls.
        subprocess.run(["xdg-email", "--subject", subject, "--body", body, to], check=True)
        return {"delivery": "composed", "via": "linux-xdg"}
    # Thunderbird -compose takes one comma-separated key='value' string; escape
    # single quotes and commas in the values so they can't break the field list.
    def esc(v):
        return v.replace("'", "\\'").replace(",", "\\,")
    compose = f"to='{esc(to)}',subject='{esc(subject)}',body='{esc(body)}'"
    subprocess.run(["thunderbird", "-compose", compose], check=True)
    return {"delivery": "composed", "via": "linux-thunderbird"}


# ------------------------------------------------------------------------ util

def _mailto(to, subject, body):
    return f"mailto:{quote(to)}?subject={quote(subject)}&body={quote(body)}"


def send(to, subject, body):
    """Send (or, where the OS forces it, compose) an email via the local mail client.

    Returns {"delivery": "sent"|"composed", "via": <backend>}. "composed" means the
    message was opened pre-filled and the USER must click Send — callers must say so.
    Raises if no local mail path exists on this machine."""
    backend = _backend()
    if backend == "macos":
        return _send_macos(to, subject, body)
    if backend == "windows":
        return _send_windows(to, subject, body)
    if backend in ("linux-xdg", "linux-thunderbird"):
        return _send_linux(to, subject, body)
    raise RuntimeError("no local mail client found — use SMTP (Gmail App Password) instead")
