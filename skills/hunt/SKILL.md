---
name: hunt
description: Run the job-hunt outreach loop — company after company, target → enrich → research → draft → review → send → queue LinkedIn → next. Use when the user says "start hunting", "run outreach", "/job-hunter:hunt", or gives a list of companies to work through. The main loop.
---

# Hunt

The orchestrator. Work through companies one at a time, producing reviewed, send-ready outreach for the people who matter at each — on the least tokens possible.

You are a capable model. This skill gives you the goal, the loop shape, and the tools. How you sequence a given company is your judgment — adapt to what you find.

## Start
1. Get the company list (the user provides it, or pull `targeting` results). **Show it and let the user confirm or edit before you spend anything** — add, drop, reorder.
2. Load the static context ONCE: the user's `profile.md`, `targeting-prefs.md`, `voice-profile.md`, and `learnings_context`. This is cached for the session; don't reload per company.

## The loop (per company — keep context bounded)
For each confirmed company, work it end to end, then move on:

1. `state_get(company)` — load only this company. Don't carry the last company's data forward.
2. **Target** — dispatch `target-scout` (isolated) for the decision-makers + hooks, if not already targeted.
3. **Enrich** — dispatch `contact-enricher` (isolated) for verified emails via the credit chain. If a provider is exhausted, surface it and let the user decide (pay/switch/rotate) rather than stalling silently.
4. **Research** — dispatch `person-researcher` (isolated) for the top contact(s); it returns a compact digest.
5. **Draft** — dispatch `message-writer` (isolated) for the voice-matched email + LinkedIn note + DM.
6. **Review** — hand to the review gate. Nothing sends without approval. Capture edits/rejections as `learnings`.
7. **Send + queue** — on approval: `send_email`; `linkedin_queue` the note+DM for the user to send by hand.
8. `set_company_status(company, "sent")`, then next company.

## Token discipline (this matters)
- Each worker agent runs in its OWN context and returns a compact digest. Never inherit their scratch work into the loop.
- State lives in the DB, not the conversation. Between companies, you're working from `state_get`, not history.
- Don't reload static context per company. Load once, reuse.

## Resumable
The loop is resumable — `state_get` and `pipeline_board` tell you what's done. If interrupted, re-running `hunt` continues from where the pipeline left off; skip companies already `sent`/`done`.

## Keep learning
The whole point is that this gets more "yours" over time. Every correction at review, every rejected target, every stated preference → `learning_record`. Next run, it shows up in `learnings_context` and the drafts/targets arrive closer to right.
