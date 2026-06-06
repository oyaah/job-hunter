---
name: hunt
description: Run the job-hunt outreach loop — company after company, target → enrich → research → draft → review → send → LinkedIn → next. Use when the user says "start hunting", "run outreach", "/job-hunter:hunt", or gives a list of companies. The main loop.
---

# Hunt

The orchestrator. Work one company at a time, producing reviewed, send-ready outreach for the people who matter. State lives in files — you read and write `state/<company-slug>.json` and keep `pipeline.md` in sync (see `references/state-file.template.md`). There are no state tools; you edit the files.

You're a capable model. This gives you the arc and the tools; sequence each company by judgment.

## Start
Get the company list (the user gives it, or read existing `state/*.json`). **Show it and let the user confirm/edit before spending anything.** Load the static context once: the user's resume, `targeting-prefs.md`, `voice-profile.md`, and `learnings.md`. Don't reload per company.

## Per company
Create/open `state/<slug>.json`, work it end to end, then move on:
- **Target** — dispatch `target-scout` for the decision-makers + a hook each; write them into the file.
- **Enrich** — `enrich_contact(name, domain)` per contact; write the verified email (or flagged guess) into the file. If `needs_credits`, tell the user (pay/switch) — don't stall.
- **Research** — dispatch `person-researcher` for the top contact; save the digest.
- **Draft** — dispatch `message-writer` for the email + LinkedIn note + DM; save as drafts.
- **Review** — hand to the review gate. Nothing sends without approval. Append edits/rejections to `learnings.md`.
- **Send + LinkedIn** — on approval: `send_email(..., approved=true)`. Then LinkedIn: `linkedin_guard("connect")`; only if `ok`, send the connection + reviewed note in the user's Chrome (`references/linkedin-playbook.md`), then `linkedin_record("connect")` and set the contact's `linkedin.status = SENT`.
- Update `status` in the file and the `pipeline.md` row; next company.

The LinkedIn DM waits for acceptance — the `watch` step (or `/loop`) handles connect→accept→DM. Keep LinkedIn human-paced (the guard enforces a generous daily cap).

## Token discipline
Worker agents return compact digests — never pull their scratch into the loop. Between companies you work from the company file, not history. Load static context once.

## Keep learning (self-evolving)
Every correction at review, rejected target, or stated preference → append to `learnings.md`. At a natural break, run `reflect` to distill it into the profile files. Next run, drafts and targets arrive closer to right.
