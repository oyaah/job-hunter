#!/usr/bin/env python3
"""SessionStart hook — a fast, network-free snapshot so the user opens to what
needs attention: pipeline state, credit balances (with low/exhausted warnings +
reset dates), connections accepted (DMs ready), and drafts pending review.
Reads the DB only; must stay well under the hook timeout."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    try:
        import store
        import state
        import credits
        conn = store.connect_default()
    except Exception:
        return  # never block a session on the hook

    lines = []

    board = state.pipeline_board(conn)
    if board:
        active = [b for b in board if b["status"] not in ("done",)]
        sent = sum(b["sent"] for b in board)
        lines.append(f"job-hunter: {len(board)} companies, {sent} emails sent, "
                     f"{len(active)} in flight.")

    pending = state.list_pending_messages(conn)
    if pending:
        lines.append(f"  • {len(pending)} draft(s) awaiting your review (/job-hunter:review).")

    ready = conn.execute("SELECT COUNT(*) AS n FROM linkedin WHERE status='DM_REVIEW'").fetchone()
    if ready and ready["n"]:
        lines.append(f"  • {ready['n']} accepted LinkedIn connection(s) with a DM ready.")

    for b in credits.balances(conn):
        if b["status"] == "exhausted":
            reset = f" (resets {b['reset_at']})" if b["reset_at"] else ""
            lines.append(f"  ! {b['service']}/{b['account_id']} credits EXHAUSTED{reset} — "
                         f"pay, switch provider, or rotate account.")
        elif b["status"] == "low":
            lines.append(f"  • {b['service']} credits low: {b['remaining']} left.")

    try:
        import learnings
        n = len(learnings.get(conn))
        if n:
            lines.append(f"  • tuned to you: {n} learned preference(s) applied to drafts/targeting.")
    except Exception:
        pass

    if lines:
        print("\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
