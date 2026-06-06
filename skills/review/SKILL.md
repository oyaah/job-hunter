---
name: review
description: Review pending outreach before it sends — approve, edit, or reject each email and LinkedIn message. Use when the user says "review my drafts", "show what's queued", "/job-hunter:review", or before any send. The human gate.
---

# Review

The human gate. Every email and LinkedIn message passes through here before it can send. Drafts live in the company files (`state/*.json`, each contact's `email_draft` / `linkedin`); find the ones whose status isn't `sent`/`approved`.

For each draft, show the user (recipient, subject, body) and take one of:
- **Approve** → for email, send by the precedence below; for LinkedIn the note/DM are sent in the user's Chrome after `linkedin_guard` — see hunt/watch and `references/linkedin-playbook.md`. Mark the draft `sent` in the file.
- **Edit** → apply the change in the file, keep it as a draft. **Append the reason to `learnings.md`** (`- <date> [voice] they shortened the intro`). This is the main way the system learns the user's voice.
- **Reject** → mark rejected in the file; append the reason to `learnings.md`.

## How to send an approved email (honor the user's chosen method)

The user picked **one** send method at setup (`send_method`). Always `voice_lint` the final body and get explicit approval of that exact text, then send by their choice — `send_email(to, subject, body, approved=true)` resolves it for you:

- **`gmail_mcp`** (recommended) — `send_email` returns `status:"delegate"` with the approved subject/body. That's your cue to send it through the **Gmail MCP the user installed in Claude Code** (its send / create-message tool). Don't re-lint or re-ask — it's already gated. Then mark the draft sent.
- **`mac_automation`** (macOS, no keys, no MCP) — `send_email` sends via Mail.app through `osascript`. Truly sends.
- **`app_password`** — `send_email` sends over SMTP with the Gmail App Password. Works on every OS.

`send_email` voice-lints again and enforces `approved=true` at the tool layer for the methods it sends itself. Surface what actually happened: if it returns `delivery:"composed"` (Linux / Outlook-less Windows local client) tell the user to click Send — never report a draft as delivered. If it returns `status:"delegate"`, the send isn't done until you've called the Gmail MCP.

## The point
The review gate is where the system gets smarter. Every edit and rejection is a line in `learnings.md`, so over time drafts arrive closer to send-ready. Treat each correction as signal worth keeping.

## Safety
Never call `send_email` with `approved=true` on something the user hasn't explicitly approved — the tool blocks `approved=false`, but don't try. LinkedIn messages are sent only after `linkedin_guard` returns ok.
