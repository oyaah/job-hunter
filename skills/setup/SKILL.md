---
name: setup
description: Onboard a user into job-hunter — ingest resume, capture targeting preferences and voice samples, collect API keys, and complete Gmail OAuth. Run this once before hunting; re-run anytime to update. Trigger on "set up job-hunter", "/job-hunter:setup", "onboard", "configure outreach".
---

# Job-Hunter Setup

Guided onboarding. Walk the user through each step, confirm before moving on, and write results to the outreach store + `${CLAUDE_PLUGIN_DATA}`. Keep it conversational — this is the only high-touch step; everything after is automated.

> These steps are a checklist of what to capture, not a rigid script. Read the user, skip what doesn't apply, go deeper where they have strong opinions. Whenever the user states a preference about how they want outreach done ("I never want X", "always lead with Y"), append it to `learnings.md` — that's how the system starts tuning to them from minute one.

## Steps

### 1. Resume
Ask for the user's resume (PDF or DOCX path). Extract it (use the `pdf`/`docx` reader available in the host) into a structured profile: name, headline, skills, projects they can speak to, education, location, links. Store it in `${CLAUDE_PLUGIN_DATA}/profile.md`. This feeds both targeting (skill overlap) and drafting (accurate toolkit, no invented credentials).

### 2. Targeting preferences
Open `references/targeting-prefs.template.md`. Walk the user through each field (role focus, primary differentiator, company filters, affinity signals, who-matters, hard-nos). Write the filled copy to `${CLAUDE_PLUGIN_DATA}/targeting-prefs.md`.

### 3. Voice profile
This is what stops outreach sounding like AI. Ask for **2-3 of the user's real past messages** (any cold emails / DMs they actually sent and liked). Distill them into `references/voice-profile.template.md`'s slots — identity line, differentiator, default register, sign-off, honesty guardrails, toolkit, extra banned words. Write to `${CLAUDE_PLUGIN_DATA}/voice-profile.md`. Do NOT copy the seed user's content — learn *their* patterns. The universal anti-AI lint (`voice.lint`) applies on top regardless.

### 4. API keys
The plugin prompts for these as sensitive `userConfig` at enable-time (keychain-stored). Confirm which the user actually has:
- **Hunter.io** (free tier, required) — the default enrichment provider.
- **Apollo / ContactOut / Lemlist** (optional, paid) — toggle on only if the user has a seat. Tell them honestly: Apollo API enrichment needs a paid plan; Lemlist has no free tier; ContactOut has no self-serve API.
Check balances with `credits_status` (it polls Hunter's real balance endpoint).

### 5. Email sending (SMTP App Password — the simple default)
The default send channel is SMTP with a Gmail **App Password** — works on Mac, Windows, and Linux, under Claude Code / Codex / anywhere, no OAuth, no token expiry. Walk the user through:
1. Enable 2-Step Verification on their Google account (required for App Passwords).
2. https://myaccount.google.com/apppasswords → create one named "job-hunter" → copy the 16-char password.
3. Enter their Gmail address (`gmail_address`) and the App Password (`gmail_app_password`, stored sensitive). Done — `send_email` works.

**Alternatives** (only if preferred): the `local` channel — sends through the desktop mail client the user is already signed into, no keys at all. On macOS (Mail.app) and Windows-with-Outlook it truly **sends**; on Linux and Windows-without-Outlook it opens the message **pre-filled** and the user clicks Send (`send_email` returns `delivery:"composed"` so this is never silent). Or the OAuth `gmail` channel (Desktop credentials.json from Google Cloud Console; ~weekly re-auth). SMTP is recommended for everyone — it's the only zero-touch path on every OS.

### 6. LinkedIn automation
LinkedIn actions run through the bundled `linkedin` MCP server (auto-installed via `uvx`). First run, it opens a real browser session for the user to log into LinkedIn once — the session persists at `~/.linkedin-mcp/profile/`, no cookie copying. Confirm the user is okay with automated connection requests + DMs (both still pass the review gate), and set expectations on volume: keep it human-paced (~15-25 connects/day), not bulk — that's what keeps the account safe. Point them at `/job-hunter:watch` (or pairing it with `/loop`) for hands-off acceptance → DM.

## Done
Summarize what's configured (profile ✓, prefs ✓, voice ✓, which providers, Gmail/Mail.app, LinkedIn posture) and the next step: `/job-hunter:hunt` with a company list.

## Re-running
Setup is idempotent. Re-running updates profile/prefs/voice/keys without wiping pipeline state.
