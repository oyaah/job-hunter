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

## The loop (per company)
Work one company end to end, then move to the next. `state_get` loads just that company; the worker agents do the heavy lifting in isolation and hand back compact digests. The arc: find the people who matter (`target-scout`) → get verified contact info (`contact-enricher`) → understand the top person (`person-researcher`) → draft voice-matched outreach (`message-writer`) → review gate → on approval, send the email (`send_email`) and send the LinkedIn connection request via `mcp__linkedin__connect_with_person` (then `linkedin_sent`) → mark the company done.

The LinkedIn DM is not sent now — it's prepared and waits for the connection to be accepted. The `watch` step (run it periodically, or pair with `/loop`) detects acceptances and runs DM draft → review → auto-send. Keep LinkedIn volume human-paced (~15-25 connects/day), not bulk.

You know how to sequence this. Adapt to what each company gives you — skip steps that are already done, dig deeper where it matters. The worker agents and tools are there; use them as the situation calls for.

## Token discipline (this is the one thing to hold onto)
- Worker agents run in their own context and return digests — never pull their scratch work into the loop.
- The DB is the memory; the conversation isn't. Between companies you work from `state_get`, not history.
- Load the static context (resume, prefs, voice profile, learnings) once, reuse it. Don't reload per company.

## Resumable
The loop is resumable — `state_get` and `pipeline_board` tell you what's done. If interrupted, re-running `hunt` continues from where the pipeline left off; skip companies already `sent`/`done`.

## Keep learning (self-evolving)
The whole point is that this gets more "yours" over time. Every correction at review, every rejected target, every stated preference → `learning_record`. Next run, it shows up in `learnings_context` and the drafts/targets arrive closer to right.

At a natural break (after finishing a company), check `reflection_due("voice")` and `reflection_due("targeting")`. If due, run the `reflect` step: distill the raw learnings into the durable profile (`reflection_apply`). It's cheap — you do the distilling, no extra API call — and keeps the carried context compact instead of an ever-growing list. Effects apply next load, never mid-draft.
