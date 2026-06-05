"""LinkedIn adapter — the swappable seam (KTD4).

The workflow speaks ONE contract: connect / message / accepted. Today those
actions are performed by the bundled `linkedin-scraper-mcp` backend (the model
calls mcp__linkedin__connect_with_person / send_message / get_person_profile).
This module owns the *production behavior* that is ours regardless of backend:
the daily rate guard and the action counter. If the backend is ever swapped for
a fork or an in-house Playwright module, only which tool the skill calls changes
— the guard, counters, and lifecycle stay put.

Rate guard is generous and configurable (KTD6): the backend's own track record is
that normal-pace use rarely triggers flags, so this is a safety rail against a
runaway loop, not a tight ToS cap.
"""
import os

DEFAULT_DAILY_CAP = 40  # generous; override via LINKEDIN_DAILY_CAP


def daily_cap():
    try:
        return int(os.environ.get("LINKEDIN_DAILY_CAP", DEFAULT_DAILY_CAP))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_CAP


def _today(conn):
    return conn.execute("SELECT date('now','localtime')").fetchone()[0]


def used_today(conn, action="connect"):
    row = conn.execute("SELECT count FROM li_actions WHERE day=? AND action=?",
                       (_today(conn), action)).fetchone()
    return row["count"] if row else 0


def guard(conn, action="connect"):
    """Pre-flight: may we do one more `action` today? Returns ok + remaining, or
    blocked + reason. Call before every connect/message; never act when blocked."""
    cap = daily_cap()
    u = used_today(conn, action)
    if u >= cap:
        return {"ok": False, "action": action, "used": u, "cap": cap,
                "reason": f"daily {action} cap reached ({u}/{cap}) — resets tomorrow. "
                          f"Raise LINKEDIN_DAILY_CAP if you want more."}
    return {"ok": True, "action": action, "used": u, "cap": cap, "remaining": cap - u}


def record(conn, action="connect"):
    """Count one performed action toward today's total."""
    conn.execute(
        "INSERT INTO li_actions (day, action, count) VALUES (?,?,1) "
        "ON CONFLICT(day, action) DO UPDATE SET count = count + 1",
        (_today(conn), action))
    conn.commit()
    return used_today(conn, action)
