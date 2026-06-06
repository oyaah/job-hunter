# job-hunter — Design Philosophy & Working Notes

This file is the source of truth for *how this plugin is built and why*. Read it before changing skills, agents, or the server. It encodes a specific bet: **the model is the intelligence; the plugin is context + tools, not a cage.**

---

## Core philosophy

### 1. Trust the model
The single biggest design rule. Give the model the **right context** (these md files) and the **right tools** (the `outreach` MCP server), then get out of its way. Every hard-coded `if/else`, every rigid step-script, every "you must do exactly X then Y" instruction makes the system **dumber** — it removes the model's room to think, explore, and adapt to the person in front of it.

- Skills and agents are **context, not scripts.** They explain the goal, the constraints that genuinely matter (safety, voice, credit limits), and the tools available. They do **not** choreograph every step.
- Prefer "here's what good looks like and why" over "do these 9 steps in order."
- The only things that are non-negotiable are **safety rails** (no email sends without human review, LinkedIn never auto-acted, never invent an email address) and the **universal anti-AI voice lint**. Everything else is the model's judgment.
- When you're tempted to add a constraint, ask: *does this prevent harm, or just prevent the model from thinking?* If the latter, delete it.

### 2. Self-evolving
The workflow **tunes itself to the user** instead of being hard-coded to anyone (it was generalized away from one person's hand-built skills precisely so it could learn yours).

- The `learnings` store (MCP: `learning_record`, `learnings_get`, `learnings_context`) is the memory. It captures what the system learns about *this* user — from review edits, rejections, approvals, and explicit guidance.
- **The review gate is the primary learning moment.** When the user edits a draft, the *diff* is a lesson ("they cut the humor line", "they always shorten the intro"). When they reject a target, that's a targeting lesson. Record it.
- **Load before you decide.** Every agent that targets or drafts reads the distilled `profile_get(...)` + recent `learnings_context` first, so accumulated understanding shapes the next action. Repeats reinforce (weight climbs); the strongest signals lead.
- **Reflection (the self-evolving step).** Raw learnings get noisy. When accumulated signal crosses a threshold (sum of un-distilled `weight` ≥ `THRESHOLD` — Generative-Agents importance-trigger, not time/count polling), the `reflect` step distills them into a compact, **byte-capped** voice/targeting profile (Hermes/SkillOpt patch-not-rewrite). **The model already in the loop does the distilling — no extra LLM API call.** Distilled learnings are flagged (kept as audit trail), effects apply next load (not mid-draft, so no drift). This is `distill.py` + `reflection_due`/`reflection_apply`/`profile_get`.
- Over time the voice profile, targeting filters, and outreach style drift toward what actually gets *this user* replies — without anyone editing code.

### 3. Least tokens, most capability
Model-power-dependent, not prompt-bloated.

- **Thin orchestration.** The `hunt` loop holds file paths and per-company state, not accumulated history.
- **Sub-agent context isolation.** Heavy work (research, enrichment) runs in worker agents that return compact digests (≤~1500 tokens), never raw dumps. The orchestrator never inherits their scratch work.
- **Per-company state is the unit.** Load only the company you're working on (`state_get`). The DB is the memory; the context window is a workbench.
- **Static context is cached.** Resume, prefs, voice profile, learnings load once per session, not per company.
- **Loop reset between companies.** Carry state through files, not conversation.

### 4. Capability comes from the user's environment — we ship context, not bundled browsers
The plugin does **not** carry its own browser or GUI driver. The user's Claude Code already provides the capabilities — Claude in Chrome (their logged-in session), `computer-use`, mac automation (osascript / macos-automator). The plugin's job is to supply the **playbook** that tells a smart model how to use whatever it has, plus the few load-bearing tools the model can't be (enrichment HTTP, gated send, voice lint, the honest LinkedIn rate guard). This is why LinkedIn moved off the bundled `linkedin-scraper-mcp` (which loaded ~17 tools into every session) and onto Chrome: lighter, fewer tokens, fewer dependencies, and it reuses the session the user is already in. Channel precedence mirrors Claude's own: **MCP → Bash → Chrome → computer-use** — cheapest reliable tool first, screenshots last. Bundling a heavy server to do what the user's own environment already does is the anti-pattern.

---

## Learnings extracted from compound-engineering-plugin & superpowers

This plugin deliberately copies the patterns that make those plugins good:

- **Skills are the UX surface; agents do the work.** Skills are slash-commands, thin (a description + intent + which agent/tool to use). Agents are workers, never user-invoked. compound-engineering ships ~38 skills over ~50 agents and keeps each skill near-trivial.
- **Reference external context on demand, don't embed it.** Skills point at `references/*.md` and load them when needed, keeping the skill body small (superpowers pattern).
- **Sub-agents get a fresh, focused context.** One concern each. They explore widely and return a condensed result. This is how you do a lot of work without a giant context window.
- **Parallel where safe, serial where there's overlap.** Independent units fan out; dependent ones sequence.
- **Compounding knowledge.** ce-compound writes learnings back so the system gets smarter over time. Our `learnings` store is the same idea, scoped to user-preference tuning.
- **Human-in-the-loop on anything outbound or irreversible.** Review gates before sends.

---

## Architecture (what lives where)

```
skills/      thin slash-commands (context + dispatch)
agents/      worker agents (isolated context, compact returns)
servers/outreach-mcp/   ONLY load-bearing tools (~8): the few things the model can't do itself
references/  loaded-on-demand context (voice + targeting templates)
hooks/       SessionStart summary (pipeline + credits + learnings)
monitors/    opt-in read-only LinkedIn acceptance poller (disabled by default)
```

- **State lives in files, not a database.** Per-company state (`state/<slug>.json`), the pipeline board (`pipeline.md`), learnings (`learnings.md`), and the voice/targeting profiles are plain files under `${CLAUDE_PLUGIN_DATA}` that the model edits directly with Read/Write/Edit. The only persistence code owns is two JSON counters (`usage.json` credit balance, `li-actions.json` daily LinkedIn count) via a tiny kvstore. No SQLite. The ~8 tools are only the things the model genuinely cannot do: authenticated HTTP enrichment, gated mail send, deterministic voice lint, the honest cross-session rate guard. See `references/state-file.template.md`.
- **Secrets** via `userConfig sensitive` → env vars → OS keychain. Never in repo/git/plugin.json. The MCP server reads keys from env, so Codex works with plain env vars too.

## Safety rails (the few hard constraints)

1. **No email leaves without explicit human approval.** The review gate is a real gate.
2. **LinkedIn is automated, but gated and human-paced.** Connection requests and DMs happen in the **user's own logged-in Chrome** (Claude in Chrome), guided by `references/linkedin-playbook.md` — not a bundled scraper. The connection note + DM still pass the review gate before they go, and DMs are reviewed again after acceptance. `linkedin_guard`/`linkedin_record` are the channel-agnostic daily cap (same call whether Chrome, mac automation, or the opt-in `linkedin-scraper-mcp` fallback). Keep volume human-paced (~15-25 connects/day) — LinkedIn tolerates normal activity, not bulk blasting; the review gates + guard are what keep it safe.
3. **Never invent an email address.** Gate sends on a `verified` enrichment result; a guessed pattern is a hypothesis, surfaced as such.
4. **Anti-AI voice lint is non-negotiable** (em/en-dashes, banned openers/words) — on top of the user's learned voice.
5. **Credit honesty.** Don't fire doomed API calls; tell the user plainly when a provider is exhausted and offer pay/switch/rotate. Account rotation for free credits is flagged as ToS-violating, never silent.

## Conventions

- Python, type hints where they help, no docstrings on unchanged code.
- Tests live in `tests/`, run `python3 -m pytest tests/ -q`. Test behavior, mock external HTTP only.
- New MCP tool → add to `server.py`, keep the docstring action-oriented (the model reads it to decide when to call).
- When you add a skill or agent, write it as **context for a smart model**, not a script. If it reads like a flowchart, rewrite it.
