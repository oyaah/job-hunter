"""LinkedIn rate guard — daily action counter backed by a JSON file (was the
SQLite `li_actions` table). Generous, configurable safety rail against runaway
loops, not a tight ToS cap; the backend's own track record is that normal-pace
use rarely triggers flags."""
import datetime
import os

import kvstore

FILE = "li-actions.json"
DEFAULT_DAILY_CAP = 40


def daily_cap():
    try:
        return int(os.environ.get("LINKEDIN_DAILY_CAP", DEFAULT_DAILY_CAP))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_CAP


def _today():
    return datetime.date.today().isoformat()


def used_today(action="connect"):
    return kvstore.load(FILE).get(_today(), {}).get(action, 0)


def guard(action="connect"):
    """Pre-flight: may we do one more `action` today? ok+remaining or blocked+reason."""
    cap = daily_cap()
    u = used_today(action)
    if u >= cap:
        return {"ok": False, "action": action, "used": u, "cap": cap,
                "reason": f"daily {action} cap reached ({u}/{cap}) — resets tomorrow. "
                          f"Raise LINKEDIN_DAILY_CAP for more."}
    return {"ok": True, "action": action, "used": u, "cap": cap, "remaining": cap - u}


def record(action="connect"):
    d = kvstore.load(FILE)
    day = d.setdefault(_today(), {})
    day[action] = day.get(action, 0) + 1
    kvstore.save(FILE, d)
    return day[action]
