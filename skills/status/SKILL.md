---
name: status
description: Show the outreach pipeline board, credit balances, and LinkedIn connections awaiting acceptance. Use when the user says "status", "where am I", "show the pipeline", "how many credits left", "/job-hunter:status".
---

# Status

A fast read on where everything stands. Pull and present:

- **Pipeline** — `pipeline_board`: each company's stage (new → targeted → enriched → researched → drafted → review → sent → done) and contact/sent counts.
- **Awaiting LinkedIn acceptance** — `linkedin_awaiting`: connection requests the user has sent that haven't been accepted yet.
- **Pending review** — `list_pending_messages`: drafts waiting on the user.
- **Credits** — `credits_balances`: remaining per provider/account, with any `low`/`exhausted` flags and reset dates. If something's exhausted, say so plainly and name the options (pay / switch provider / rotate account).
- **What it's learned** — optionally `learnings_context` to show how the system has tuned to the user so far.

Keep it scannable. Lead with what needs the user's attention (pending reviews, exhausted credits, accepted connections with DMs ready).
