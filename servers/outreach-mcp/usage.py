"""Credit tracking for the enrichment providers, backed by a JSON file (was the
SQLite `credits` table). Truth is the provider's balance endpoint; this is a fast
local cache + the fallback-chain selector. Only Hunter has a free balance endpoint
today; Apollo/ContactOut are tracked by the ledger + reactive 402/403/429."""
import kvstore

FILE = "usage.json"
LOW = 0.10  # flip to 'low' below 10% of quota

# Per-op provider chains (order = preference, cost = credits/op). Hunter has no
# phone capability, so it's absent from the phone chain.
CHAINS = {
    "enrich": [("hunter", 1), ("apollo", 1), ("contactout", 1)],
    "email_find": [("hunter", 1), ("apollo", 1), ("contactout", 1)],
    "verify": [("hunter", 1), ("apollo", 1)],
    "phone": [("apollo", 8), ("contactout", 1)],
}


def _all():
    return kvstore.load(FILE)


def _status(remaining, quota):
    if remaining <= 0:
        return "exhausted"
    if quota and remaining < LOW * quota:
        return "low"
    return "ok"


def seed(service, remaining=0, quota=None, reset_at=None):
    d = _all()
    d[service] = {"remaining": remaining, "quota": quota,
                  "status": _status(remaining, quota), "reset_at": reset_at}
    kvstore.save(FILE, d)
    return d[service]


def check(service):
    return _all().get(service)


def record(service, cost):
    d = _all()
    row = d.get(service)
    if not row:
        return None
    row["remaining"] = max(0, row.get("remaining", 0) - cost)
    row["status"] = _status(row["remaining"], row.get("quota"))
    kvstore.save(FILE, d)
    return row["remaining"]


def mark_exhausted(service, reset_at=None):
    d = _all()
    row = d.setdefault(service, {"remaining": 0, "quota": None})
    row["status"] = "exhausted"
    if reset_at:
        row["reset_at"] = reset_at
    kvstore.save(FILE, d)


def usable(service, cost):
    row = _all().get(service)
    return bool(row) and row.get("status") != "exhausted" and row.get("remaining", 0) >= cost


def pick(op):
    """First provider in the op's chain that can pay for it, or None."""
    for service, cost in CHAINS.get(op, CHAINS["enrich"]):
        if usable(service, cost):
            return service
    return None


def status():
    """All provider balances — for credits_status / health."""
    return _all()
