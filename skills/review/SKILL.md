---
name: review
description: Review pending outreach before it sends — approve, edit, or reject each email and LinkedIn message. Use when the user says "review my drafts", "show what's queued", "/job-hunter:review", or before any send. The human gate.
---

# Review

The human gate. Every email and LinkedIn message passes through here before it can send. Drafts live in the company files (`state/*.json`, each contact's `email_draft` / `linkedin`); find the ones whose status isn't `sent`/`approved`.

For each draft, show the user (recipient, subject, body) and take one of:
- **Approve** → for email: `send_email(to, subject, body, approved=true)` (it voice-lints first; a lint failure means rewrite). For LinkedIn: the note/DM are sent in the user's Chrome after `linkedin_guard` — see hunt/watch and `references/linkedin-playbook.md`. Mark the draft `sent` in the file.
- **Edit** → apply the change in the file, keep it as a draft. **Append the reason to `learnings.md`** (`- <date> [voice] they shortened the intro`). This is the main way the system learns the user's voice.
- **Reject** → mark rejected in the file; append the reason to `learnings.md`.

## The point
The review gate is where the system gets smarter. Every edit and rejection is a line in `learnings.md`, so over time drafts arrive closer to send-ready. Treat each correction as signal worth keeping.

## Safety
Never call `send_email` with `approved=true` on something the user hasn't explicitly approved — the tool blocks `approved=false`, but don't try. LinkedIn messages are sent only after `linkedin_guard` returns ok.
