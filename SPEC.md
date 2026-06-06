# job-hunter — Specification

The complete design of job-hunter: what it is, how every part works, and **why** each decision was made. If `CLAUDE.md` is the philosophy and `docs/plans/` are the build plans, this is the authoritative map of the system as it stands.

---

## 1. What it is, and the philosophy

job-hunter automates **personalized job-hunt cold outreach** end to end: find the people who matter at target companies, get their verified contact info, research them, draft outreach in *your* voice, let you review it, send it, run the LinkedIn connect→accept→DM dance, and do it company after company — on the least tokens possible.

It is built on one bet, stated in `CLAUDE.md` and honored everywhere: **the model is the intelligence; the plugin is context + tools, not a cage.** Skills and agents are written as *context for a smart model*, not step-by-step scripts. The only hard constraints are safety rails (below) and the anti-AI voice lint. Everything else is the model's judgment, because over-constraining a capable model makes it dumber.

Three properties follow from that bet and shape the whole system:

- **Self-evolving.** The system learns *this user's* preferences from how they edit, reject, and approve, and feeds that back into future drafts and targeting (§6). It was generalized away from one person's hand-built skills precisely so it could learn yours.
- **Token-lean.** Thin orchestration holds file paths and per-company state; heavy work runs in isolated sub-agents that return compact digests; static context is loaded once; the loop resets between companies. The DB is the memory; the context window is a workbench.
- **Human-gated where it matters.** Nothing outbound — email or LinkedIn — leaves without a review gate.

---

## 2. Architecture

```
skills/      thin slash-commands (context + dispatch): setup, hunt, target, draft, review, watch, reflect, status
agents/      worker agents (isolated context, compact returns): target-scout, contact-enricher, person-researcher, message-writer
servers/outreach-mcp/   ONLY load-bearing tools (~8 FastMCP tools); state lives in files
references/  loaded-on-demand context (voice + targeting templates, enrichment fallback)
hooks/       SessionStart readiness summary
.mcp.json    launches outreach (our server) only — LinkedIn rides the user's own Chrome
```

**Why this shape:** it's the compound-engineering / superpowers convention — skills are the UX surface and stay near-trivial; worker agents do the reasoning in isolated contexts; one MCP server holds the logic so the agent's context stays lean (a fat skill bloats every turn). The same server is framework-agnostic, so the product runs under Claude Code, Codex, and Codex terminal identically; the Claude desktop app is reached later via an `.mcpb` bundle of the same package.

**One bundled MCP server, plus the user's own browser:**
- `outreach` (ours) — all state, enrichment, email, learnings, LinkedIn lifecycle + rate guard. The only server we auto-load.
- LinkedIn actions run in the **user's own logged-in Chrome** (Claude in Chrome), guided by `references/linkedin-playbook.md`. The `linkedin-scraper-mcp==4.13.2` backend is an **opt-in headless fallback** the user can add to their `.mcp.json` — not auto-loaded, so the default session carries zero LinkedIn tool schemas. See §LinkedIn for the channel precedence.

---

## 3. Data model

**State is files, not a database** (the career-ops pattern — a 49k⭐ tool runs its whole pipeline as markdown). Per-company state is `state/<slug>.json`; the board is `pipeline.md`; learnings are `learnings.md`; the distilled profiles are `voice-profile.md` / `targeting-prefs.md`. The model reads and writes these directly with built-in Read/Write/Edit — there are no state tools. The only persistence code owns is two JSON counters (Hunter credit balance in `usage.json`, the daily LinkedIn count in `li-actions.json`) via a ~20-line kvstore with atomic writes.

| Table | Holds | Notes |
|-------|-------|-------|
| `companies` | one row per target | lifecycle `status`: new→targeted→enriched→researched→drafted→review→sent→done |
| `contacts` | people at a company | email + `email_status` (verified/guessed), phone, hook, research digest |
| `messages` | drafted outreach | channel email/li_note/li_dm; status draft→approved→sent (+ `sending` claim) |
| `linkedin` | per-contact LI track | status DRAFTED→QUEUED→SENT→ACCEPTED→DM_REVIEW→DM_SENT |
| `credits` | per-provider balance cache | + `ledger` of billable ops |
| `learnings` | per-user insights | weight, `distilled_at`; the self-evolving substrate |
| `profiles` | distilled voice/targeting | byte-capped; reflected out of learnings |
| `li_actions` | daily LinkedIn counter | `(day, action)` → count; the rate guard's source of truth |

**Per-company isolation (KTD):** `state_get(company)` returns one company's full nested record. The orchestrator loads only the company it's working on — never all of them — which is what keeps the loop token-bounded across many companies.

---

## 4. The outreach loop

```
onboard → target → enrich → research → draft → REVIEW → send email
        → LinkedIn: guard → connect → WATCH for acceptance → draft DM → REVIEW → send DM → next company
```

The model drives sequencing (the `hunt` skill gives the arc and the tools, not a rigid script). Each worker agent runs isolated and returns a digest. Between companies, the loop works from `state_get`, not conversation history.

---

## 5. External integrations

**Enrichment — credit-gated fallback chain (Hunter → Apollo → ContactOut).** `enrich_contact` walks the chain, pre-flight credit-checks each provider (never fires a doomed call), and **gates on a verified email** — a guessed pattern is surfaced as a hypothesis, never returned as verified. Only Hunter is free-usable today (real free API + balance endpoint); Apollo/ContactOut/Lemlist are optional paid backends. Why a chain not parallel fan-out: conserves credits and tokens. Live-tested against the real Hunter API.

**Email — `auto` channel, three backends:**
1. **SMTP + Gmail App Password** — stdlib `smtplib`, works on every OS and harness, no OAuth. The cross-platform default.
2. **macOS Mail.app** — AppleScript via `osascript` argv (injection-safe), zero credentials, uses the already-signed-in account. The friction-free Mac path (live-tested).
3. **Gmail OAuth API** — for the published one-click flow (see below).

`send_email channel="auto"` resolves to SMTP if configured, else Mail.app on macOS, else OAuth. The **approval gate is enforced at the tool layer**: `send_email` atomically claims `approved→sending` so it can't double-send, and reverts on failure. No message leaves unless `approved`.

**Published OAuth (the one-click goal).** `gmail.send` is a *sensitive* scope (not restricted) → publishing the OAuth app needs only Google's ~3–5 day brand review, **no CASA security audit**. Plan: ship a single `client_id` (installed-app `client_secret` is public by Google's design; PKCE carries security), so each user just clicks "Allow". Until the app is verified, SMTP/Mail.app cover everyone; OAuth flips on when Google clears it.

**LinkedIn — drive the user's own Chrome, channel-agnostic guard (Chrome-first).** The workflow speaks one contract — `connect / message / accepted` — and the **primary channel is the user's own logged-in Chrome** (Claude in Chrome), guided by `references/linkedin-playbook.md`. We bundle no browser: capability comes from the user's environment. Channel precedence mirrors Claude's own — Chrome → mac automation (osascript / macos-automator) → the opt-in `linkedin-scraper-mcp` headless fallback → computer-use (last resort). What stays **ours regardless of channel** is the production behavior the model can't do itself: the daily rate guard + counters (`linkedin_guard`/`linkedin_record`). Acceptance is detected by reading connection degree (**1st = accepted**) on the profile. **Honest limit:** LinkedIn automation is intrinsically fragile and ToS-adjacent; the design goal is *graceful + channel-swappable + rate-guarded*, not immortal. Driving the user's real session (vs a headless stealth browser) is both lighter and less adversarial to LinkedIn.

---

## 6. The self-evolving layer

The differentiator. Two pieces:

- **Learnings.** `learning_record(category, insight)` captures what the system learns about the user — primarily at the **review gate** (an edit to a draft is a voice lesson; a rejected target is a targeting lesson). Repeats reinforce (weight climbs). Agents load `learnings_context` / `profile_get` *before* drafting or targeting, so accumulated understanding shapes the next action.
- **Reflection (distillation).** When un-distilled learning weight crosses a threshold (Generative-Agents importance trigger, not time polling), the `reflect` step compresses raw learnings into a compact, **byte-capped** voice/targeting profile (Hermes/SkillOpt patch-not-rewrite). **The model already in the loop does the distilling — no extra LLM call.** Distilled learnings are flagged (kept as audit trail); effects apply on next load, never mid-draft, so there's no drift.

Net effect: drafts and targets get more "you" over time, and the carried context stays compact instead of an ever-growing list — without anyone editing code.

---

## 7. Safety rails (the few hard constraints)

1. **No email without explicit approval** — enforced at the tool layer (atomic claim), not just in a skill.
2. **LinkedIn is automated but gated + human-paced** — connection note and DM both pass review; a generous configurable daily cap (default 40) guards against runaway loops; it runs in the user's own real Chrome session; volume stays human-paced.
3. **Never invent an email** — gate sends on `verified`.
4. **Anti-AI voice lint is non-negotiable** — `add_message` rejects em/en-dashes and banned AI cadence at the server, on top of the user's learned voice.
5. **Credit honesty** — no doomed calls; exhaustion surfaces with pay/switch/rotate options; account rotation is flagged as ToS-risky, never silent.
6. **Secrets** — `userConfig sensitive` → env → OS keychain; never in repo/git/`plugin.json`. Logs are secret-redacted.

---

## 8. Reliability & distribution

- **Concurrency:** thread-local connections over WAL (§3).
- **Resilience:** retries with jittered backoff on transient errors (429/5xx/timeout); terminal errors (402/403/4xx) fast-fail. Secret-redacting log filter. A `health()` tool reports DB status, configured credentials (names only), and available send channels.
- **CI:** the test suite (60+ tests, mock-based/hermetic) is tracked in-repo and runs on push/PR via GitHub Actions on Python 3.12/3.13.
- **Distribution:** Claude Code marketplace plugin is primary; the server is packaged for `uvx` launch from PyPI (zero manual install). `.mcpb` (Claude desktop app) and a Codex snippet are planned follow-ups; the same package backs all surfaces.

---

## 9. Open risks (honest)

- **LinkedIn fragility** — unofficial automation breaks when LinkedIn changes; mitigated by pin + swappable adapter + clear failure surfacing, not eliminated.
- **OAuth verification is author-owned** — a Google process, not code; fallbacks cover the interim.
- **Paid providers (Apollo/ContactOut/Lemlist) not live-tested** — request shapes are correct, logic is mock-tested; verify when seats exist.
- **PyPI upload not yet done** — the wheel now builds correctly (`uv build`) and installs/runs as `job-hunter-mcp` via a hatch `sources` remap of the flat `servers/outreach-mcp/` tree to an importable `outreach_mcp` package (verified in a clean venv); the only remaining step is `twine upload` once a PyPI token exists. The plugin itself ships via the GitHub marketplace and runs the server from the flat layout directly.
