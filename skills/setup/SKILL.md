---
name: setup
description: Onboard a user into job-hunter — ingest resume, capture targeting preferences and voice samples, collect API keys, and complete Gmail OAuth. Run this once before hunting; re-run anytime to update. Trigger on "set up job-hunter", "/job-hunter:setup", "onboard", "configure outreach".
---

# Job-Hunter Setup

Guided onboarding. Walk the user through each step, confirm before moving on, and write results to the outreach store + `${CLAUDE_PLUGIN_DATA}`. Keep it conversational — this is the only high-touch step; everything after is automated.

> These steps are a checklist of what to capture, not a rigid script. Read the user, skip what doesn't apply, go deeper where they have strong opinions. Whenever the user states a preference about how they want outreach done ("I never want X", "always lead with Y"), record it with `learning_record` — that's how the system starts tuning to them from minute one.

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
Seed each enabled service's credit row via `credits_seed` (poll the balance endpoint where available, e.g. Hunter `/v2/account`).

### 5. Gmail OAuth
Primary send channel. Walk the user through:
1. Create a **Desktop-app** OAuth client in Google Cloud Console, download `credentials.json`.
2. Keep the consent screen in **Testing** status, add their own Google account as a test user (no Google verification, no multi-week review).
3. Run the local OAuth flow (the `gmail.get_credentials` path) — they click through the "Google hasn't verified this app" warning once. Token lands in the OS keychain.
**Tell them the one catch:** Testing-mode refresh tokens expire ~weekly, so they'll re-auth occasionally. That's expected and safe. Offer **local Mail.app** (macOS, AppleScript, zero OAuth) as an alternative if they'd rather skip the Cloud Console step.

### 6. LinkedIn posture
Confirm the safe default: **the agent drafts and queues LinkedIn notes + DMs; the user clicks Send.** Ask whether to enable the optional read-only acceptance poller (off by default) — explain it polls slowly and never acts, but is still unofficial-API and best left off unless they want hands-off acceptance detection.

## Done
Summarize what's configured (profile ✓, prefs ✓, voice ✓, which providers, Gmail/Mail.app, LinkedIn posture) and the next step: `/job-hunter:hunt` with a company list.

## Re-running
Setup is idempotent. Re-running updates profile/prefs/voice/keys without wiping pipeline state.
