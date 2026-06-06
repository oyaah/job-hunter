# Changelog

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
