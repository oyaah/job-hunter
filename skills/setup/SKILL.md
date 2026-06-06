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

### 5. Email sending — make the user pick ONE of three
This is a choice, not a stack. Present the three options, let the user pick, and record it as `send_method` (userConfig). Everything after honors that one choice.

**Option A — `gmail_mcp` (recommended).** The user installs an **already-available Gmail MCP** into their own Claude Code (their pick of which one), authorizes it, and job-hunter sends through it — real Gmail API, proper threading, from their actual account, nothing stored here. Confirm it shows in `/mcp`. At send time `send_email` returns `status:"delegate"` and you complete the send via that MCP's tool.

**Option B — `mac_automation` (macOS only, no MCP, no keys).** Skip all of that: send through the **Mail.app** account they're already signed into, via `osascript` automation built into the outreach server. Zero credentials. Needs macOS **Automation** permission for the terminal app to control **Mail** (System Settings → Privacy & Security → Automation; the first send may pop a one-time confirm). `send_email` truly sends.

**Option C — `app_password` (any OS).** One Gmail **App Password** over SMTP — dead simple, cross-platform, no OAuth:
1. Enable 2-Step Verification (required for App Passwords).
2. https://myaccount.google.com/apppasswords → create one named "job-hunter" → copy the 16-char password.
3. Enter `gmail_address` + `gmail_app_password` (sensitive). Done.

Set `send_method` to their choice. Steer them: **A** for the best experience, **B** if they're on a Mac and want zero keys/zero setup, **C** for one simple cross-platform path. (The OAuth `gmail` channel and `channel="local"` on Windows/Linux still exist as manual overrides, but the three above are the supported choices.)

### 6. LinkedIn automation (uses the user's own Chrome)
LinkedIn runs in the user's **own logged-in Chrome** — no bundled scraper, no cookie copying. Setup: install the **[Claude in Chrome](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn)** extension, run `/chrome` in Claude Code, and stay signed into LinkedIn in that browser. Then connection requests + DMs happen on the user's real session (both still pass the review gate). The full flow + fallbacks live in `references/linkedin-playbook.md`.

Confirm the user is okay with automated connects + DMs, and set volume expectations: human-paced (~15-25 connects/day), not bulk — that's what keeps the account safe (the `linkedin_guard` daily cap enforces it). Point them at `/job-hunter:watch` (or pairing it with `/loop`) for hands-off acceptance → DM.

**No Chrome integration?** It needs a direct Anthropic plan + the extension. On a **Mac**, the bundled `macos-automator` server is the fallback — it drives the user's real Chrome via AppleScript (open Chrome → LinkedIn → act). It needs Node (for `npx`) and, on first use, macOS **Automation + Accessibility** permission grants (System Settings → Privacy & Security). The guard + review gate are identical either way.

## Done
Summarize what's configured (profile ✓, prefs ✓, voice ✓, which providers, Gmail/Mail.app, LinkedIn posture) and the next step: `/job-hunter:hunt` with a company list.

## Re-running
Setup is idempotent. Re-running updates profile/prefs/voice/keys without wiping pipeline state.
