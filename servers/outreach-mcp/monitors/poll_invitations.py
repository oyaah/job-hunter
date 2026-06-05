#!/usr/bin/env python3
"""OPT-IN, READ-ONLY LinkedIn acceptance poller (KTD6).

Run as a background monitor on a slow cadence. Checks which queued connection
requests have been accepted and flips them to ACCEPTED so the prepared DM can
surface for review. Prints one notification line per newly-accepted connection
(the monitor delivers stdout to the session). Never sends or acts. Disabled by
default in monitors.json — only runs if the user opted in and set LINKEDIN_LI_AT.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store        # noqa: E402
import state        # noqa: E402
from integrations import linkedin  # noqa: E402


def main():
    if not os.environ.get("LINKEDIN_LI_AT"):
        return  # poller off
    try:
        conn = store.connect_default()
        accepted = linkedin.get_accepted_connections()  # [{name, profile}]
    except Exception:
        return  # never crash the session on a flaky poll
    if not accepted:
        return

    from collections import Counter
    profiles = {a["profile"].lower() for a in accepted if a.get("profile")}
    accepted_name_counts = Counter(a["name"].lower() for a in accepted if a.get("name"))

    try:
        rows = conn.execute(
            "SELECT c.id, c.name, c.linkedin_url FROM contacts c "
            "JOIN linkedin l ON l.contact_id=c.id WHERE l.status='SENT'").fetchall()
    except Exception:
        return
    sent_name_counts = Counter((r["name"] or "").lower() for r in rows)

    for r in rows:
        url = (r["linkedin_url"] or "").lower()
        # Prefer matching on the unique profile identifier embedded in the URL.
        matched = any(p and p in url for p in profiles)
        if not matched:
            # Name fallback ONLY when unambiguous on both sides — never flip the
            # wrong contact when two people share a name.
            nm = (r["name"] or "").lower()
            matched = bool(nm) and accepted_name_counts.get(nm, 0) == 1 \
                and sent_name_counts.get(nm, 0) == 1
        if matched:
            state.set_linkedin_status(conn, r["id"], "ACCEPTED")
            state.set_linkedin_status(conn, r["id"], "DM_REVIEW")
            print(f"[job-hunter] {r['name']} accepted your LinkedIn request — "
                  f"a DM is ready for review (/job-hunter:review).", flush=True)


if __name__ == "__main__":
    main()
