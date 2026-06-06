---
name: watch
description: Watchdog for LinkedIn connection acceptances — check who accepted, then draft + review + send their DM. Use when the user says "check linkedin", "any acceptances", "/job-hunter:watch", or pair with /loop for hands-off monitoring.
---

# Watch

The watchdog for the LinkedIn track. Cheap by design: it only looks at contacts actually awaiting acceptance, so it costs almost nothing when there's nothing to do. It works **in the user's own Chrome** — see `references/linkedin-playbook.md` for how (and the fallbacks if Chrome isn't available).

## What it does
1. Read the `state/*.json` files for contacts whose `linkedin.status == SENT` (request sent, not yet accepted).
2. For each, open their profile in Chrome and read the **connection degree**: **1st degree = accepted** (2nd/3rd = still pending). That's the reliable signal — there's no clean "list pending invites" view. If a profile won't load for one, skip it and move on.
3. For anyone now 1st-degree: set their `linkedin.status = DM_REVIEW` in the file. If the prepared DM is thin or stale, dispatch `message-writer` to draft a fresh one from their now-richer profile.
4. Surface the DM for a quick review (same gate as email — capture any edit in `learnings.md`).
5. On approval: `linkedin_guard("message")`; if `ok`, send the reviewed DM in Chrome (per the playbook), then `linkedin_record("message")` and set `linkedin.status = DM_SENT`.

No Chrome integration? On a Mac it falls back to `macos-automator` (drives your real Chrome via AppleScript) — see the playbook. The guard + review gate are identical no matter the channel.

## Hands-off
Pair with `/loop` on a slow interval (a few hours) so acceptances get picked up without babysitting. Keep the cadence slow — polite to LinkedIn, cheap on tokens. It acts only on real acceptances, one at a time. Keep volume human-paced; the guard enforces the daily cap.
