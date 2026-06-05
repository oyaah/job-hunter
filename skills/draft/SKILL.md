---
name: draft
description: Draft a voice-matched cold email + LinkedIn note + DM for a contact. Use when the user says "draft an email", "write outreach for X", "/job-hunter:draft", or wants messages for a researched target. Drafts only — sending happens at the review gate.
---

# Draft

Produce voice-matched outreach for one or more researched contacts.

If the contact isn't researched yet, run **person-researcher** first (the message is only as good as the hook). Then dispatch **message-writer** with the contact's digest, the user's `voice-profile.md`, and `learnings_context`.

The writer enforces the user's learned voice plus the universal anti-AI lint. Drafts land in the store with status `draft` and flow to `/job-hunter:review` — nothing sends here.

Show the user the draft. If they edit it, that edit is a voice lesson — capture the gist with `learning_record("voice", ...)` so the next draft needs less correction.
