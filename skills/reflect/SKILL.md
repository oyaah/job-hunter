---
name: reflect
description: Distill accumulated outreach feedback into the user's durable voice/targeting profile — the self-evolving step. Runs automatically when enough signal builds up; can be invoked manually with "reflect", "tune my profile", "/job-hunter:reflect".
---

# Reflect

Compress raw learnings into a few durable principles so the system gets sharper without growing noisier. This is what makes the workflow self-evolving — and it's cheap, because you (the model) do the distilling; no extra API call.

## When it fires
`reflection_due(category)` returns `due: true` once enough new signal has accumulated (sum of un-distilled learning weights crosses the threshold). The `hunt` loop checks this at natural breaks. You can also run it on demand.

## What to do when due
1. `reflection_due("voice")` (and `"targeting"`) — get the ranked raw learnings (the `material`).
2. Read the current `profile_get("voice")` so you patch, not blank-slate rewrite.
3. Distill: from the material + current profile, write **3-5 durable principles** — what to do, what to avoid, contradictions resolved. Patch the existing profile; keep what still holds, change what the new learnings overturned. Stay tight (there's a hard byte cap — curate, don't pile on).
4. `reflection_apply("voice", <distilled principles>)`. This saves the compact profile and marks those learnings distilled (they're kept as audit trail, just won't re-trigger).

## Principles
- **Patch, don't rewrite from scratch.** Preserve working content; change only what the evidence overturns.
- **Curate, don't accumulate.** The profile is capped on purpose. If it's full, drop the weakest principle to make room.
- **Takes effect next load, not mid-draft** — no changing voice in the middle of a message.
- Raw learnings are never deleted; the distilled profile is just the cheap, durable summary loaded before each draft.
