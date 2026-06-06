---
name: status
description: Show the outreach pipeline, credit balances, and LinkedIn state. Use when the user says "status", "where am I", "show the pipeline", "how many credits", "/job-hunter:status".
---

# Status

A fast read on where everything stands. Pull and present:

- **Pipeline** — read `pipeline.md` (and the `state/*.json` files for detail): each company's stage and which contacts are sent / awaiting LinkedIn acceptance / pending review.
- **Credits** — `credits_status`: remaining per provider, with any low/exhausted flags. If exhausted, say so plainly and name the options (pay / switch provider).
- **LinkedIn today** — from `health` (`linkedin_today`) vs the daily cap.
- **What it's learned** — optionally summarize `learnings.md` / the profile files to show how it's tuned to the user.

Keep it scannable. Lead with what needs attention: pending reviews, exhausted credits, accepted connections with DMs ready.
