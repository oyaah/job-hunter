# Changelog

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
