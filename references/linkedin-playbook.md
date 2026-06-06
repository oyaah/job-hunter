# LinkedIn playbook — drive the user's own Chrome, fast

This is context, not a script. You (the model) already know how to use a browser.
The job: do LinkedIn outreach **in the user's own logged-in Chrome** — the session
they're already signed into. Move fast, honor the rails, use judgment.

## The one rule that makes everything work: trusted input

LinkedIn **ignores synthetic JavaScript clicks** (`.click()`, dispatched events) on its
Connect / Message / Send controls — it checks `event.isTrusted`. So:

- **Reading and navigating is free.** Use Chrome `execute javascript` to set URLs, scrape
  search results, read a profile, confirm degree/identity. This always works.
- **Acting (click a button, type, send) needs a *trusted* input path:**
  1. **Claude in Chrome** (`/chrome`) — the default. It issues real, trusted clicks. Use it.
  2. **macos-automator / System Events** (mac fallback) — real OS-level mouse clicks and
     keystrokes (`click at {x,y}`, `keystroke`). **Requires macOS Accessibility permission**
     for the terminal app (one-time grant). This is what makes the fallback actually send.
  3. **computer-use** — last resort (screenshots). Rarely needed.

If neither trusted path is available, do the reading/disambiguation, prep the draft, and
tell the user to do the final click — never pretend it sent.

## Go fast: batch the steps

When you have Claude in Chrome, drive it **inline** with `browser_batch` — pack the predictable
sequence into one round trip instead of one tool call per step. Typical batches:

- **Open + confirm a person:** `[navigate, wait 1.5s, screenshot, find "Message/Connect button"]`.
- **Connect:** `[left_click <Connect ref>, wait 1.5s, screenshot]` → then `[left_click "Send without a note" | type note + click Send, screenshot]`.
- **DM:** `[left_click <Message ref>, screenshot]` → `[left_click <composer>, type <reviewed text>, screenshot]` (leave Enter to the gate/user as agreed).
- **Acceptance check:** `[navigate, wait, find "Pending button / connection degree"]`.

Prefer **element refs** from `find`/`read_page` over pixel coordinates — LinkedIn's layout shifts and
a ref click lands every time; coordinates drift after scroll. If the extension drops mid-batch
("extension disconnected"), it's usually transient — `list_connected_browsers`, `select_browser`, retry.
Reading/searching never needs trusted input, so batch those freely; only the click/type/send steps
need the trusted path above.

## How LinkedIn is laid out (so you move fast, no fumbling)

- **People search:** `https://www.linkedin.com/search/results/people/?keywords=<name>%20<company>`.
  Each result card shows a **degree badge — "· 1st / 2nd / 3rd"** and an action button:
  **1st-degree → "Message"**, 2nd/3rd → **"Connect"** or **"Follow"**.
- **Disambiguate before acting.** Multiple people share names. Match on the headline /
  education / location in the card (e.g. "IITR '27", "iGEM IIT Roorkee") and the **1st**
  badge before you touch anything. Scrape cards generically with `a[href*="/in/"]` plus the
  surrounding card text — don't depend on LinkedIn's churning CSS class names.
- **Connect:** click **Connect** → **"Add a note"** → paste the reviewed note (≤300 chars) → **Send**.
- **DM (1st-degree only):** click **Message** → a composer overlay opens bottom-right with a
  contenteditable text box, **already focused** → type the reviewed text → **Enter sends**
  (Shift+Enter = newline). For a 2nd/3rd-degree person you can't DM — connect first.
- **Acceptance check (the `watch` loop):** open the person's profile or re-run the search;
  **degree shows "1st" once they've accepted** (2nd/3rd = still pending). That's the reliable
  signal — there's no clean "pending invites" list.

### Concrete fallback send (System Events, when Chrome integration is off)

1. `execute javascript` to find the target button, `scrollIntoView`, and read its center
   `getBoundingClientRect()` plus `innerHeight`/`innerWidth`.
2. Read the Chrome window's screen `position`/`size` via System Events; the page's top-left
   in screen points ≈ `(winX, winY + (winHeight − innerHeight))`. Add the button's viewport
   x/y to get screen coords. `click at {x, y}` — a real, trusted click — opens the composer.
3. The composer text box is auto-focused: `keystroke "<reviewed text>"`, then `key code 36`
   (Return) to send. Verify by reading the thread back.

## The outreach arc

Work **one contact at a time**, off the company state file (`state/<slug>.json`).

**Connect:** `linkedin_guard("connect")` → if `ok`, find + confirm the person, Connect +
paste the **already-reviewed** note, Send → `linkedin_record("connect")`, set `linkedin.status = SENT`.

**Watch acceptances:** for `status == SENT`, check the degree; on **1st** set `DM_REVIEW`
(redraft the DM from their richer profile if it's thin — dispatch `message-writer`).

**DM:** surface for review (same gate as email; log edits to `learnings.md`) → on approval
`linkedin_guard("message")` → if `ok`, send the reviewed text in the composer (Enter) →
`linkedin_record("message")`, set `DM_SENT`.

## Rails (non-negotiable)

- **Review gate first.** The note and the DM are sent only *after* the human approved that
  exact text. You paste approved content; you never improvise a message to a real person.
- **Guard is the daily cap.** Always `linkedin_guard(...)` before the action — the honest,
  channel-agnostic counter. Same call whether Chrome or System Events.
- **Human-paced.** ~15–25 connects/day. The guard enforces the hard cap; you keep the rhythm sane.
- **Login / CAPTCHA.** Chrome integration pauses for these — let the user clear it, then continue.
  Never try to defeat a challenge.
