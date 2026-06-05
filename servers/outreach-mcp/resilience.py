"""Production resilience — retries, secret-redacting logging. stdlib only, lightweight.

External calls fail transiently (timeouts, 429, 5xx); those retry with jittered
backoff. Terminal failures (402/403 = auth/credits) do not retry — they fast-fail
to the credit/exhaustion path. Secrets must never reach logs."""
import logging
import random
import re
import time

# CreditError lives in integrations._base; import lazily to avoid a hard dependency
# here (keeps this module importable in isolation).


def retry(fn, attempts=3, base_delay=0.5, max_delay=8.0):
    """Call fn(); retry on transient errors with jittered exponential backoff.
    Does NOT retry CreditError (402/403/429-as-exhaustion) or 4xx client errors —
    those are terminal and handled upstream. Returns fn()'s value or re-raises."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if not _is_transient(e) or i == attempts - 1:
                raise
            last = e
            delay = min(max_delay, base_delay * (2 ** i)) * (0.5 + random.random())
            logging.getLogger("job-hunter").warning(
                "transient error (attempt %d/%d), retrying in %.1fs: %r",
                i + 1, attempts, delay, e)
            time.sleep(delay)
    raise last  # unreachable, for type-checkers


def _is_transient(e):
    if e.__class__.__name__ == "CreditError":
        return False
    name = e.__class__.__name__.lower()
    if "timeout" in name or "connecterror" in name or "readerror" in name:
        return True
    # httpx.HTTPStatusError carries .response.status_code
    resp = getattr(e, "response", None)
    code = getattr(resp, "status_code", None)
    if code is not None:
        return code == 429 or 500 <= code < 600
    return False


# --- secret-redacting logging -------------------------------------------------
_SECRET_PATTERNS = [
    re.compile(r"(api_key=)[^&\s\"']+", re.I),
    re.compile(r"(li_at=)[^;&\s\"']+", re.I),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.I),
    re.compile(r"(\"?(?:password|token|secret|app_password)\"?\s*[:=]\s*\"?)[^\"',\s]+", re.I),
]


def redact(text):
    s = str(text)
    for pat in _SECRET_PATTERNS:
        s = pat.sub(r"\1[REDACTED]", s)
    return s


class _RedactFilter(logging.Filter):
    def filter(self, record):
        try:
            record.msg = redact(record.getMessage())
            record.args = ()
        except Exception:  # noqa: BLE001
            pass
        return True


def configure_logging():
    """Attach the redaction filter to the root logger and quiet noisy libs."""
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    root = logging.getLogger()
    if not any(isinstance(f, _RedactFilter) for f in root.filters):
        root.addFilter(_RedactFilter())
