---
title: "refactor: Chrome-first outreach automation (drive the user's own desktop, unbundle the scraper)"
type: refactor
status: active
date: 2026-06-06
version_target: 0.4.0
---

# refactor: Chrome-first outreach automation

## Summary

Make job-hunter drive **the user's own browser and desktop** instead of bundling a heavy headless LinkedIn scraper. LinkedIn outreach becomes Claude-in-Chrome driven (the user is already logged in), guided by one tight playbook md — `linkedin-scraper-mcp` is demoted from an always-on MCP (~17 tools loaded every session) to an *optional, documented fallback*. Mail keeps its existing SMTP + osascript Mail.app paths. The whole change is context-and-config, not new runtime code: fewer tools, fewer tokens, broader reach.

---

## Problem Frame

The plugin's `.mcp.json` auto-starts `linkedin-scraper-mcp==4.13.2`, loading ~17 tools into **every** session whether or not LinkedIn is used. That scraper spins its own Patchright Chromium (40MB+ download), carries open upstream bugs (#407/#432/#433), and duplicates a browser the user already has open and logged in. It's token-heavy, fragile, and a setup barrier — the opposite of "I want many people to use this."

Claude Code now drives the user's real Chrome (`/chrome`) and native macOS apps (`computer-use`, or AppleScript via osascript / steipete's `macos-automator-mcp`). The model's own tool precedence is **MCP → Bash → Chrome → computer-use**. The plugin should lean into that: ship *context* (a playbook) telling the model how to do LinkedIn outreach in the user's browser, and reserve the bundled scraper for users who can't run Chrome integration.

This is a direct application of the plugin's existing CLAUDE.md bet — *the model is the intelligence; the plugin is context + tools, not a cage* — and of Peter Steinberger's automator design lesson: **one powerful capability + a good knowledge base beats many narrow tools.**

---

## Requirements

- R1. LinkedIn primary path = Claude in Chrome on the user's logged-in session, guided by a declarative playbook (not click-by-click choreography).
- R2. `linkedin-scraper-mcp` removed from auto-start; documented as an optional fallback the user can opt into.
- R3. The `linkedin_guard` / `linkedin_record` rate rail still wraps **every** LinkedIn action regardless of channel (Chrome or MCP).
- R4. Mail send unchanged in behavior (SMTP default, osascript Mail.app local, Gmail OAuth); automation/computer-use only documented as last resort.
- R5. All hard safety rails preserved: human review gate before any send, never invent an email, voice lint, human-paced LinkedIn volume.
- R6. Net token reduction in a default session (no LinkedIn MCP tools loaded unless opted in).
- R7. Docs (README, setup skill, CLAUDE.md, CHANGELOG, manifests) reflect the Chrome-first model and tell the user exactly what to install.

---

## Key Technical Decisions

- **KTD1 — Chrome over bundled scraper for LinkedIn.** The user is already authenticated in their browser; Chrome integration reuses that session, sidesteps the scraper's bugs, and removes a 40MB install. Trade-off: Chrome integration is beta and needs a direct Anthropic plan + the extension. Mitigated by R2's documented fallback.
- **KTD2 — Ship context, not bundled browsers.** The plugin adds *no* new MCP server. Chrome / computer-use / macos-automator are capabilities the *user's* Claude Code provides; the plugin only provides the playbook that tells the model how to use whatever it has. This is what makes the change token-negative.
- **KTD3 — Keep `linkedin_guard`/`linkedin_record` as the channel-agnostic rail.** The honest cross-session daily cap is the one thing the model can't do itself and is the core safety property; it stays in the outreach MCP and is called the same way no matter how the action is performed.
- **KTD4 — Mail stays as-is.** `localmail.py` (osascript Mail.app) is already the "automator" path on mac and is near-zero tokens (a subprocess call); routing mail through `macos-automator-mcp` would add a dependency for no gain. Document automator/computer-use as only-if-needed.
- **KTD5 — Fallback is opt-in via a one-line `.mcp.json` snippet in the README**, not a disabled-by-default server entry, to guarantee zero tool load for the default user.

---

## Channel precedence (for both LinkedIn and mail)

```
LinkedIn:  Claude in Chrome (user's session)   ← primary, default
           → macos-automator / osascript Chrome control (mac, scriptable)
           → linkedin-scraper-mcp               ← opt-in fallback (headless, no Chrome ext)
           → computer-use (screenshots)         ← last resort, slowest

Mail:      SMTP (Gmail App Password)            ← primary, cross-platform, hands-off
           → local mail client (osascript Mail.app / Outlook / xdg-email)
           → computer-use                       ← last resort
```

Mirrors Claude's own MCP → Bash → Chrome → computer-use ordering: cheapest reliable tool first, screenshots last.

---

## Implementation Units

### U1. LinkedIn playbook reference (`references/linkedin-playbook.md`)

**Goal:** The single new context file — how the model runs LinkedIn outreach in the user's Chrome, declaratively.
**Requirements:** R1, R3, R5.
**Files:** `references/linkedin-playbook.md` (new).
**Approach:** Declarative "what good looks like," not a macro. Cover: (1) precedence — prefer Chrome; if Chrome unavailable, fall back per the channel table; (2) the outreach arc — search the person, open their profile, read the hook, click Connect → Add a note (the reviewed note), send; track who's pending; once a request is accepted (1st-degree), draft+review the DM, send; (3) the guard contract — call `linkedin_guard("connect"|"message")` *before* each action, only proceed on `ok`, then `linkedin_record(...)`; (4) safety — note/DM pass the review gate first, keep volume human-paced (~15-25/day), pause for login/CAPTCHA (Chrome pauses automatically). Keep it tight (target < ~120 lines) — context for a smart model, not a script.
**Patterns to follow:** Tone and brevity of existing `references/*.template.md` and CLAUDE.md philosophy.
**Test scenarios:** Test expectation: none — documentation/context file, no behavior.
**Verification:** A reader (model) can run the connect→track→DM loop in Chrome from this file alone, and knows when/how to fall back.

### U2. Demote the LinkedIn scraper from auto-start (`.mcp.json`)

**Goal:** Stop loading ~17 scraper tools every session.
**Requirements:** R2, R6.
**Files:** `.mcp.json`.
**Approach:** Remove the `linkedin` server block so only `outreach` auto-starts. The fallback snippet lives in the README (U6) for users who want it. Confirm `outreach` env wiring is untouched.
**Test scenarios:** Test expectation: none — config. Verify JSON validity and that `outreach` still boots (existing boot check).
**Verification:** `.mcp.json` parses; a fresh session loads only the 8 outreach tools + the user's own Chrome/computer-use tools; no `linkedin-scraper-mcp` download is triggered.

### U3. Rewrite `watch` skill for Chrome-first acceptance + DM

**Goal:** The most scraper-coupled skill drives Chrome instead.
**Requirements:** R1, R3, R5.
**Files:** `skills/watch/SKILL.md`.
**Approach:** Replace `mcp__linkedin__get_person_profile` acceptance check and `mcp__linkedin__send_message` send with the Chrome playbook flow (open the person in Chrome, read connection degree = accepted signal; on acceptance draft+review+send DM). Point at `references/linkedin-playbook.md`. Keep the `linkedin_guard("message")` gate and `DM_REVIEW`/`DM_SENT` state transitions. Add one line: "no Chrome? see the fallback in the playbook."
**Test scenarios:** Test expectation: none — skill prose.
**Verification:** Skill no longer hard-codes `mcp__linkedin__*`; the acceptance→DM loop reads from the playbook; guard + review gate intact.

### U4. Update `hunt`, `review`, `status`, `setup` skills

**Goal:** Remove remaining scraper hard-coding; align language to Chrome-first.
**Requirements:** R1, R3, R5, R7.
**Files:** `skills/hunt/SKILL.md`, `skills/review/SKILL.md`, `skills/status/SKILL.md`, `skills/setup/SKILL.md`.
**Approach:** `hunt`: the connect step references the playbook (Chrome connect + note) wrapped by `linkedin_guard("connect")`/`linkedin_record`, not `mcp__linkedin__connect_with_person`. `review`: "LinkedIn note/DM are performed via the Chrome playbook after `linkedin_guard`" (drop "LinkedIn MCP"). `status`: unchanged logic (reads `health`), reword any MCP phrasing. `setup`: replace the LinkedIn-MCP browser-login step with the Chrome setup (install Claude-in-Chrome extension, `/chrome`, already logged into LinkedIn) + a short "fallback: opt into linkedin-scraper-mcp" pointer.
**Test scenarios:** Test expectation: none — skill prose.
**Verification:** `grep -r mcp__linkedin skills/` returns only the playbook-referenced fallback context (or nothing); each skill points at the playbook; guard calls preserved.

### U5. CLAUDE.md — principle + safety rail update

**Goal:** Encode the "drive the user's own desktop, ship context not bundled browsers" bet.
**Requirements:** R3, R5, R7.
**Files:** `CLAUDE.md`.
**Approach:** Add a short principle under Core philosophy (capability comes from the user's environment — Chrome/computer-use/automator; the plugin supplies the playbook + the guard, nothing heavier). Update safety rail #2 to describe the Chrome-first channel and the channel-agnostic guard, and note the scraper is now an opt-in fallback. Keep it brief.
**Test scenarios:** Test expectation: none — docs.
**Verification:** CLAUDE.md describes the new model; safety rails still list review gate, no-invented-email, voice lint, human-paced LinkedIn.

### U6. README + prerequisites for the new model

**Goal:** Tell users exactly what to install and how the channels work.
**Requirements:** R2, R7.
**Files:** `README.md`.
**Approach:** Update the LinkedIn section to Chrome-first: install the **Claude in Chrome** extension, run `/chrome`, stay logged into LinkedIn; actions are gated + rate-capped. Add the **optional fallback** subsection with the exact `.mcp.json` snippet to add `linkedin-scraper-mcp` for users without Chrome integration. Note computer-use/macos-automator as power-user options. Fold into the existing "What you need" table (add: Claude in Chrome extension for the LinkedIn path; everything else unchanged).
**Test scenarios:** Test expectation: none — docs.
**Verification:** A new user can follow the README to the Chrome LinkedIn flow, and an advanced user can paste the fallback snippet.

### U7. Version bump to 0.4.0 + CHANGELOG

**Goal:** Ship the refactor as a coherent release.
**Requirements:** R7.
**Files:** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `manifest.json`, `.codex-plugin/plugin.json`, `pyproject.toml`, `CHANGELOG.md`.
**Approach:** Bump all version fields 0.3.0 → 0.4.0. Add a CHANGELOG entry summarizing: Chrome-first LinkedIn, scraper unbundled (token win), guard unchanged, docs. Adjust the codex/plugin descriptions that mention the bundled LinkedIn MCP.
**Test scenarios:** Test expectation: none — metadata. Verify all JSON parses.
**Verification:** Versions consistent at 0.4.0 across all manifests; CHANGELOG documents the change; `python3 -m pytest tests/ -q` still green (no code touched, but confirm).

---

## Scope Boundaries

**In scope:** LinkedIn channel pivot to Chrome, scraper unbundling, the playbook md, skill/doc/version updates, the guard staying channel-agnostic.

**Out of scope (this PR):**
- No changes to the 8 outreach MCP tools' code (enrich/verify/send/lint/guard/health) — behavior identical.
- No changes to mail send code (`localmail.py`, `smtp_send.py`) — already cross-platform.

### Deferred to Follow-Up Work
- A thin `references/automation-recipes.md` of AppleScript/JXA snippets (mac) if real usage shows the model needs them — only if a need is felt.
- Wiring `macos-automator-mcp` as an explicit documented fallback server, if Chrome proves insufficient for some users.

---

## Risks & Mitigations

- **Chrome integration is beta / plan-gated.** → R2 fallback snippet keeps non-Chrome users working; README states the requirement plainly.
- **Losing the scraper's deterministic profile-degree read** (the acceptance signal). → The playbook tells the model to read connection degree visually in Chrome; the fallback MCP remains for users who want the programmatic read.
- **Skill drift / stale `mcp__linkedin__` references.** → U4 verification greps to confirm removal.

---

## System-Wide Impact

Token profile of a default session drops by the LinkedIn scraper's ~17 tool schemas. No runtime code paths change; the outreach MCP and mail send are untouched. The change is portable to Codex (which also has no bundled browser — same playbook, same fallback).
