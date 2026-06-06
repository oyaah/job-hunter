# LinkedIn playbook — drive the user's own Chrome

This is context, not a script. You (the model) already know how to use a browser.
The job here is to do LinkedIn outreach **in the user's own logged-in Chrome** — the
session they're already signed into — instead of any bundled scraper. Read the goal,
honor the rails, use judgment.

## Which tool to use (cheapest reliable first)

1. **Claude in Chrome** (`/chrome`) — the default. The user is already logged into
   LinkedIn there; reuse that session. Open tabs, read the page, click, type.
2. **macOS automation** — if Chrome integration isn't on but you're on a Mac, you can
   drive Chrome/Safari via AppleScript through Bash (`osascript`) or a `macos-automator`
   tool if the user has one. Scriptable, no screenshots, cheap.
3. **`linkedin-scraper-mcp`** — only if the user opted into the fallback (README tells
   them how). Tools appear as `mcp__linkedin__*`. Headless, has known upstream bugs;
   use it only when there's no browser path.
4. **`computer-use`** — last resort (screenshots + clicks). Slow and token-heavy. Use
   only when nothing above can reach the page.

If none are available, say so plainly and stop — don't pretend an action happened.

## The outreach arc

Work **one contact at a time**, off the company state file (`state/<slug>.json`).

**Sending a connection request:**
1. `linkedin_guard("connect")`. If it returns `blocked`, stop for today — tell the user
   the cap is hit. Only proceed on `ok`.
2. Open the person's profile in Chrome (search their name + company if you don't have the
   URL). Confirm it's the right person against the company file.
3. Click **Connect** → **Add a note**, paste the **already-reviewed** note (the one that
   passed the review gate — never improvise a new one here), send.
4. `linkedin_record("connect")`, set the contact's `linkedin.status = SENT` in the file.

**Tracking acceptances (the `watch` loop):**
- For contacts with `linkedin.status == SENT`, open their profile in Chrome and read the
  **connection degree**: **1st** = accepted; 2nd/3rd = still pending. That's the reliable
  signal — there's no clean "pending invites" list. If a profile won't load, skip it.
- On acceptance: set `linkedin.status = DM_REVIEW`. If the prepared DM is thin or stale,
  redraft from their now-richer profile (dispatch `message-writer`).

**Sending the DM (1st-degree only):**
1. Surface the DM for review — same human gate as email. Capture any edit in `learnings.md`.
2. On approval: `linkedin_guard("message")`; only on `ok`, open the conversation in Chrome
   and send the reviewed text. Then `linkedin_record("message")`, set `linkedin.status = DM_SENT`.

## Rails (non-negotiable)

- **Review gate first.** The connection note and the DM are sent only *after* the human
  approved that exact text. You are pasting approved content, not writing it live.
- **The guard is the daily cap.** Always `linkedin_guard(...)` before the action; it's the
  honest cross-session counter and it's channel-agnostic — same call whether you're in
  Chrome, automator, or the MCP fallback.
- **Human-paced.** ~15–25 connects/day is healthy. LinkedIn tolerates normal activity, not
  bulk. The guard enforces the hard cap; you keep the rhythm sane.
- **Login / CAPTCHA.** Chrome integration pauses and hands control back when it hits a login
  or CAPTCHA — let the user clear it, then continue. Never try to defeat a challenge.
