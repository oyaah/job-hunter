# Changelog

## 0.4.2 — 2026-06-06 (pick-one send method + visible watchdog + faster Chrome)

- **One send method, chosen at setup (`send_method` userConfig) — no stacking.** Three options the user picks between: **`gmail_mcp`** (install an already-available Gmail MCP into your own Claude Code; job-hunter delegates the send to it — recommended), **`mac_automation`** (macOS only — send via Mail.app `osascript` automation, **no MCP, no keys**), or **`app_password`** (Gmail App Password over SMTP, every OS). `send_email channel="auto"` resolves to the chosen method; for `gmail_mcp` it returns `status:"delegate"` so the model completes the send through the user's MCP. Review gate (voice lint + human approval) holds for all three.
- **Watchdog is now visible + faster.** `watch` prints a status table (Contact · Was · Now · Action) so you can actually see acceptances flip, and drives Chrome **inline** with one `browser_batch` per degree-check instead of spawning a sub-agent. Live-tested end to end: connection request → accept → 1st-degree detection.
- **Faster Chrome driving** documented in `references/linkedin-playbook.md`: batch predictable step sequences into single `browser_batch` round trips; prefer element refs over pixel coordinates. Skills (review/setup/watch) updated for the pick-one model. No enrichment/guard/lint logic changed; no new bundled MCP (the Mac path is plain automation, in keeping with "capability comes from the user's environment").

## 0.4.1 — 2026-06-06 (remove the scraper for good; wire macos-automator as the mac fallback)

- **Removed `linkedin-scraper-mcp` entirely** — not even an opt-in anymore. The headless Patchright scraper (and its open bugs) is gone from the plugin.
- **Bundled `macos-automator` (steipete) as the mac fallback** — a thin 3-tool server (`execute_script` / `get_scripting_tips` / `accessibility_query`) that drives the user's **real Chrome** via AppleScript: open Chrome → LinkedIn → do the work. Channel precedence is now **Chrome → macos-automator → computer-use**. Needs Node (`npx`) + macOS Automation/Accessibility permission — documented in the README.
- All existing functionality unchanged and intact: the `watch` watchdog, the connect→accept→DM loop, `linkedin_guard`/`linkedin_record` rate cap, and every review gate work identically — only the channel underneath LinkedIn changed. Mail send untouched (SMTP / local Mail.app). Removed the now-dead scraper smoke-test script.

## 0.4.0 — 2026-06-06 (Chrome-first LinkedIn — drive your own browser, unbundle the scraper)

- **LinkedIn now runs in the user's own logged-in Chrome** (Claude in Chrome), guided by a single declarative playbook (`references/linkedin-playbook.md`) — search → connect+note → track acceptance (1st-degree) → DM, all human-reviewed. No bundled browser, no separate login, reuses the session you're already in.
- **Unbundled `linkedin-scraper-mcp`** from `.mcp.json` — it no longer auto-loads ~17 tools into every session. It's now an **opt-in headless fallback** (one-line snippet in the README) for users without Chrome integration. Big token win for the default user.
- **`linkedin_guard`/`linkedin_record` stay the channel-agnostic rate rail** — same daily-cap call whether you act via Chrome, mac automation, or the fallback MCP. All safety rails unchanged: review gate before every send, never invent an email, voice lint, human-paced volume.
- Channel precedence documented (MCP → Bash → Chrome → computer-use, cheapest reliable first). New CLAUDE.md principle: *capability comes from the user's environment; the plugin ships context, not bundled browsers.* Skills (hunt/watch/review/setup) + README + manifests updated. No outreach-tool or mail-send code changed.

## 0.3.0 — 2026-06-06 (cross-platform send + real packaging)

- **`local` send channel is now cross-platform** (was macOS-only). macOS Mail.app and Windows Outlook truly **send**; Linux (`xdg-email`/Thunderbird) and Windows-without-Outlook open a **pre-filled compose** window — `send_email` returns `delivery:"composed"` so a draft is never mistaken for a sent message. Injection-safe field passing per OS (osascript argv / PowerShell env vars / separate args). Replaced `mailapp.py` with `integrations/localmail.py`; 7 new tests.
- **PyPI wheel builds and runs.** hatch `sources` remap installs the flat `servers/outreach-mcp/` tree as the importable `outreach_mcp` package; `job-hunter-mcp` console entry verified in a clean venv. (Upload pending a token; plugin ships via GitHub marketplace.)
- Version + descriptions aligned to 0.3.0 across plugin.json / manifest.json / .codex-plugin / pyproject. README gains a full per-OS "What you need" section. `dist/`,`build/` gitignored.

## 0.3.0 — 2026-06-06 (simplification: files over DB)

- **Collapsed 37 MCP tools → 8.** Kept only what the model can't do itself: enrich_contact, verify_email, credits_status (Hunter HTTP), send_email (approved+lint gated), voice_lint, linkedin_guard/record, health.
- **State is files, not SQLite.** Per-company state (`state/<slug>.json`), pipeline board (`pipeline.md`), learnings (`learnings.md`), and voice/targeting profiles are files the model edits directly. Deleted store/state/credits/learnings/distill/linkedin_adapter + the whole DB layer.
- **kvstore** (atomic JSON) backs the only two counters code owns: credit balance + daily LinkedIn count.
- **Self-evolving via files:** learnings append to a file; reflection = the model rewriting the profile files. Same loop, no bookkeeping tools.
- Skills + agents rewritten to drive files. Automation arc (target→enrich→draft→review→send→LinkedIn→watch→DM) and all safety rails preserved. 30 focused tests.


## 0.2.0 — 2026-06-05 (productionization, in progress)

- **Concurrency:** thread-local SQLite connections over WAL — safe under FastMCP worker-thread dispatch (was a single shared connection that could crash / lose writes).
- **Resilience:** retry with jittered backoff (429/5xx/timeout retry; 402/403/4xx terminal); secret-redacting log filter; `health()` tool.
- **CI:** test suite tracked in-repo, GitHub Actions runs pytest on Python 3.12/3.13.
- **LinkedIn (production):** swappable `connect/message/accepted` adapter over a *pinned* `linkedin-scraper-mcp==4.13.2`; generous configurable daily rate guard (`LINKEDIN_DAILY_CAP`, default 40); acceptance via profile-degree (1st = accepted); guard wired into hunt/watch.
- **Email:** `auto` channel (SMTP App Password → macOS Mail.app → Gmail OAuth); SMTP default added; atomic send-claim prevents double-send.
- **Docs:** `SPEC.md` (full design + philosophy); packaging scaffold (`pyproject.toml`).

### Remaining for 0.2.0
- Published Google OAuth one-click flow (PKCE) + verification runbook.
- Full PyPI package restructure for `uvx` launch.
- `.mcpb` Claude-app bundle + Codex snippet.

## 0.1.0 — 2026-06-05

- Initial plugin: enrichment chain, voice-matched drafting, review gate, multi-channel send, LinkedIn lifecycle, self-evolving learnings + reflection. 49 tests.
