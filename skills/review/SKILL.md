---
name: review
description: Review pending outreach before it sends — approve, edit, or reject each email and LinkedIn message. Use when the user says "review my drafts", "show me what's queued", "/job-hunter:review", or before any send. This is the human gate; nothing leaves without it.
---

# Review

The human gate. Every email and LinkedIn message passes through here before it can send. This is a real safety boundary, not a formality — the send tools refuse anything that isn't `approved`.

## Flow
1. `list_pending_messages` — show each draft: recipient, channel, subject, body. Group by company.
2. For each, the user does one of:
   - **Approve** → `set_message_status(id, "approved")`. Then, for email: `gmail_draft(id)` so they see the exact Gmail draft, and `send_email(id)` when they confirm (or `channel="mailapp"`). For LinkedIn: the note/DM is queued for them to send manually (see hunt — LinkedIn is never auto-sent).
   - **Edit** → apply their changes, re-store, keep as `draft`. **Capture why they edited** with `learning_record("voice", ...)` — "they cut the humor line", "shortened the intro", "made the ask softer". This is the main way the system learns their voice.
   - **Reject** → `set_message_status(id, "rejected")`. Capture the reason as a learning too.

## The point
The review gate is where the system gets smarter. Every edit and rejection is a lesson recorded against `learnings`, so over time the drafts arrive closer to send-ready and the user touches them less. Treat each correction as signal worth keeping, not just a one-off fix.

## Safety
- Never call `send_email` on a message the user hasn't explicitly approved. The tool blocks it anyway, but don't try.
- LinkedIn messages are never sent by a tool — they're queued for the user to send by hand.
