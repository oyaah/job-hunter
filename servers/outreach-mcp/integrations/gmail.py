"""Gmail integration — Desktop-app OAuth, keychain/file token, draft + send.

KTD3/KTD4: primary send channel. OAuth app stays in "Testing" mode (no Google
verification) so refresh tokens expire ~weekly — re-auth is expected, surfaced
clearly, never silent. Google libs are imported lazily so this module loads in
environments without them (tests, CI)."""
import base64
import os
from email.mime.text import MIMEText

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]
DEFAULT_TOKEN_PATH = os.path.expanduser("~/.config/job-hunter/gmail_token.json")
KEYRING_SERVICE = "job-hunter"
KEYRING_KEY = "gmail_token"


def _token_path():
    return os.environ.get("GMAIL_TOKEN_PATH") or DEFAULT_TOKEN_PATH


def _load_token_json():
    """Prefer the OS keychain; fall back to a 0600 file."""
    try:
        import keyring
        blob = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY)
        if blob:
            return blob
    except Exception:
        pass
    path = _token_path()
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return None


def _save_token_json(blob):
    try:
        import keyring
        keyring.set_password(KEYRING_SERVICE, KEYRING_KEY, blob)
        return
    except Exception:
        pass
    path = _token_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(blob)
    os.chmod(path, 0o600)


def get_credentials(client_secret_path, interactive=True):
    """Return valid OAuth creds, running the installed-app loopback flow on first
    run or when the refresh token has expired (Testing-mode ~7-day expiry)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    blob = _load_token_json()
    if blob:
        creds = Credentials.from_authorized_user_info(_json_loads(blob), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token_json(creds.to_json())
            return creds
        except Exception:
            creds = None  # refresh token expired (Testing mode) → re-consent
    if not interactive:
        raise RuntimeError(
            "Gmail token missing/expired. Run /job-hunter:setup to re-authenticate "
            "(Testing-mode refresh tokens expire ~weekly).")
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    _save_token_json(creds.to_json())
    return creds


def _service(client_secret_path, interactive=True):
    from googleapiclient.discovery import build
    creds = get_credentials(client_secret_path, interactive=interactive)
    return build("gmail", "v1", credentials=creds)


def _hdr(value):
    # Strip CR/LF so a crafted to/subject can't inject extra headers (the stdlib
    # also guards this; belt and suspenders).
    return (value or "").replace("\r", " ").replace("\n", " ")


def _raw(to, subject, body):
    msg = MIMEText(body, _charset="utf-8")  # handle non-ASCII bodies, not just us-ascii
    msg["to"] = _hdr(to)
    msg["subject"] = _hdr(subject)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def create_draft(to, subject, body, client_secret_path, interactive=True):
    """Create a Gmail draft (reviewable before send). Returns draft id."""
    svc = _service(client_secret_path, interactive)
    draft = svc.users().drafts().create(
        userId="me", body={"message": {"raw": _raw(to, subject, body)}}).execute()
    return draft["id"]


def send_draft(draft_id, client_secret_path, interactive=True):
    """Send a previously created draft (post human approval)."""
    svc = _service(client_secret_path, interactive)
    return svc.users().drafts().send(userId="me", body={"id": draft_id}).execute()


def send_message(to, subject, body, client_secret_path, interactive=True):
    """Direct send without a stored draft."""
    svc = _service(client_secret_path, interactive)
    return svc.users().messages().send(
        userId="me", body={"raw": _raw(to, subject, body)}).execute()


def _json_loads(blob):
    import json
    return json.loads(blob)
