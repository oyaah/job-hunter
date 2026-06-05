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
    conn = store.connect_default()
    accepted = {a["name"].lower() for a in linkedin.get_accepted_connections()}
    if not accepted:
        return
    rows = conn.execute(
        "SELECT c.id, c.name FROM contacts c JOIN linkedin l ON l.contact_id=c.id "
        "WHERE l.status='SENT'").fetchall()
    for r in rows:
        if r["name"].lower() in accepted:
            state.set_linkedin_status(conn, r["id"], "ACCEPTED")
            state.set_linkedin_status(conn, r["id"], "DM_REVIEW")
            print(f"[job-hunter] {r['name']} accepted your LinkedIn request — "
                  f"a DM is ready for review (/job-hunter:review).", flush=True)


if __name__ == "__main__":
    main()
