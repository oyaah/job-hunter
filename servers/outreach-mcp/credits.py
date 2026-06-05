"""Credit ledger + fallback-chain provider selection.

Truth is the provider's balance endpoint; this table is a fast local cache.
`pick_provider` never fires a doomed call — it short-circuits to the next
usable provider/account in the chain (KTD5, R11).
"""

LOW_THRESHOLD = 0.10  # flip to 'low' below 10% of monthly quota

# Per-op provider chains. Order = preference. Cost = credits per successful op.
# Hunter has no phone capability, so it's absent from the 'phone' chain.
CHAINS = {
    "enrich": [("hunter", 1), ("apollo", 1), ("contactout", 1)],
    "email_find": [("hunter", 1), ("apollo", 1), ("contactout", 1)],
    "verify": [("hunter", 1), ("apollo", 1)],
    "phone": [("apollo", 8), ("contactout", 1)],
    "search": [("apollo", 0)],  # Apollo api_search consumes no credits
}


def _recompute_status(remaining, quota):
    if remaining <= 0:
        return "exhausted"
    if quota and remaining < LOW_THRESHOLD * quota:
        return "low"
    return "ok"


def seed(conn, service, account_id="default", remaining=0, monthly_quota=None,
         status=None, reset_at=None):
    if status is None:
        status = _recompute_status(remaining, monthly_quota)
    conn.execute(
        """INSERT INTO credits (service, account_id, remaining, monthly_quota, status, reset_at)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(service, account_id) DO UPDATE SET
             remaining=excluded.remaining, monthly_quota=excluded.monthly_quota,
             status=excluded.status, reset_at=excluded.reset_at,
             last_checked=datetime('now')""",
        (service, account_id, remaining, monthly_quota, status, reset_at),
    )
    conn.commit()


def check(conn, service, account_id="default"):
    row = conn.execute(
        "SELECT * FROM credits WHERE service=? AND account_id=?",
        (service, account_id),
    ).fetchone()
    return dict(row) if row else None


def record(conn, service, account_id, op, cost, contact_id=None):
    """Decrement remaining, log the billable op, recompute status."""
    cur = check(conn, service, account_id)
    if cur is None:
        raise ValueError(f"no credit row for {service}/{account_id}")
    remaining = cur["remaining"] - cost
    status = _recompute_status(remaining, cur["monthly_quota"])
    conn.execute(
        "UPDATE credits SET remaining=?, status=?, last_checked=datetime('now') "
        "WHERE service=? AND account_id=?",
        (remaining, status, service, account_id),
    )
    conn.execute(
        "INSERT INTO ledger (service, account_id, op, cost, contact_id) VALUES (?,?,?,?,?)",
        (service, account_id, op, cost, contact_id),
    )
    conn.commit()
    return remaining


def mark_exhausted(conn, service, account_id="default", reset_at=None):
    """Reactive exhaustion (caught a 402/403/429 from the provider)."""
    conn.execute(
        "UPDATE credits SET status='exhausted', reset_at=COALESCE(?, reset_at), "
        "last_checked=datetime('now') WHERE service=? AND account_id=?",
        (reset_at, service, account_id),
    )
    conn.commit()


def pick_provider(conn, op):
    """Return (service, account_id) of the first chain member that can do `op`,
    or None if every provider/account is exhausted or under-credited."""
    chain = CHAINS.get(op, CHAINS["enrich"])
    for service, cost in chain:
        rows = conn.execute(
            "SELECT account_id, remaining, status FROM credits WHERE service=? "
            "ORDER BY (account_id='default') DESC, account_id ASC",
            (service,),
        ).fetchall()
        for r in rows:
            if r["status"] != "exhausted" and r["remaining"] >= cost:
                return (service, r["account_id"])
    return None


def balances(conn):
    """All credit rows, for the status board / SessionStart summary."""
    rows = conn.execute(
        "SELECT service, account_id, remaining, monthly_quota, status, reset_at "
        "FROM credits ORDER BY service, account_id"
    ).fetchall()
    return [dict(r) for r in rows]
