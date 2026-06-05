---
name: watch
description: Watchdog for LinkedIn connection acceptances — check who accepted, then auto-draft + review + send their DM. Use when the user says "check linkedin", "any acceptances", "/job-hunter:watch", or pair it with /loop for hands-off monitoring.
---

# Watch

The watchdog for the LinkedIn track. Cheap by design: it only looks at the contacts actually awaiting acceptance, so it costs almost nothing when there's nothing to do.

## What it does
1. `linkedin_awaiting` — the contacts whose connection request is SENT, not yet accepted.
2. For each, check acceptance with `mcp__linkedin__get_person_profile` and read the **connection degree**: **1st degree = accepted** (2nd/3rd = still pending). This is the reliable signal — the backend has no "list pending invites" tool, so degree is the proxy. If a profile fetch fails for one contact, skip it and move on; don't let one failure stop the rest.
3. For anyone now 1st-degree: `linkedin_accepted(contact_id)` → it returns the prepared DM and moves them to DM_REVIEW. If the DM is thin or stale, dispatch `message-writer` to draft a fresh one from their (now richer) profile.
4. Surface the DM to the user for a quick review (same gate as email — capture any edit as a `learning`).
5. On approval: check `linkedin_guard("message")`, and if `ok` send via `mcp__linkedin__send_message`, then `linkedin_dm_sent(contact_id)`.

## Hands-off
Pair with `/loop` on a slow interval (e.g. a few hours) so acceptances get picked up and DMs drafted without you babysitting. Keep the cadence slow — it's polite to LinkedIn and cheap on tokens. Nothing here blasts: it acts only on real acceptances, one at a time.

## Stay sane on volume
LinkedIn tolerates normal human-pace activity, not bulk automation. Keep connection sends and DMs to a sane daily count (think ~15-25 connects/day, not hundreds). If you're working a long company list, spread it out.
