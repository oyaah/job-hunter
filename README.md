# job-hunter

End-to-end job-hunt cold outreach automation for Claude Code + Codex. Targets the people who matter, enriches their contact info, researches them, drafts voice-matched emails + LinkedIn DMs, gets your review, and sends — company after company, on the least tokens possible.

> **Opt-in by design.** This plugin connects to paid services and sends real mail. It ships `defaultEnabled: false` — nothing outbound exists until you enable it and complete `/job-hunter:setup`.

## What it does

```
onboard → target → enrich → research → draft → REVIEW → send → queue LinkedIn → monitor → DM → next company
```

- **Target** — companies + the specific decision-makers, fit-scored by your prefs (size, funding, alumni, skill overlap, role).
- **Enrich** — verified email/phone via a credit-gated chain: Hunter → Apollo → ContactOut.
- **Research** — a compact per-person digest (personality + hook) that makes the message land.
- **Draft** — cold email + LinkedIn note + DM in *your* voice (learned from your samples), anti-AI lint enforced.
- **Review** — nothing sends without your explicit approval. Approve / edit / reject.
- **Send** — Gmail API (primary) or local Mail.app; Lemlist sequences optional.
- **LinkedIn** — automated via the bundled [linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server): the agent sends the connection request, the `watch` step detects acceptance, then drafts the DM, you review it, and it's sent automatically.

## Safety posture

- **LinkedIn is automated but gated and human-paced.** The connection note and DM both pass a review gate before sending; keep volume sane (~15-25 connects/day), not bulk.
- **Every email is human-reviewed** before it leaves your account.
- **Secrets live in the OS keychain / env**, never in this repo or git.

## Install

```bash
# Claude Code
/plugin marketplace add oyaah/job-hunter
/plugin install job-hunter
# then enable it, and run:
/job-hunter:setup
```

```bash
# Codex — point at the same MCP server, export env vars:
export HUNTER_API_KEY=... GMAIL_TOKEN_PATH=~/.config/job-hunter/gmail_token.json
pip install -r requirements.txt
```

## Skills

| Skill | Does |
|-------|------|
| `/job-hunter:setup` | Onboard: resume, prefs, voice samples, API keys, Gmail OAuth |
| `/job-hunter:hunt` | The main loop — runs company after company |
| `/job-hunter:target` | Build / refine the company + people shortlist |
| `/job-hunter:draft` | Draft a voice-matched email + LinkedIn note + DM |
| `/job-hunter:review` | Approve / edit / reject pending messages before send |
| `/job-hunter:watch` | Watchdog: detect LinkedIn acceptances, then draft + review + send the DM |
| `/job-hunter:status` | Pipeline board + credit balances |

The bundled `linkedin` MCP server ([linkedin-scraper-mcp](https://github.com/stickerdaniel/linkedin-mcp-server)) runs via `uvx` and performs the actual LinkedIn connect/message actions; first run opens a browser to log in once.

## Requirements

- Python 3.10+, `pip install -r requirements.txt`
- **Free + required:** Hunter.io API key; a Gmail address + [App Password](https://myaccount.google.com/apppasswords) for sending (SMTP — works on every OS, no OAuth)
- **For LinkedIn automation:** `uv` (the bundled `linkedin` server runs via `uvx`)
- **Optional (paid):** Apollo, ContactOut, Lemlist API keys

## Portability

Works under **Claude Code, Codex, and Codex terminal** — they all run the same `outreach-mcp` server; secrets come from `userConfig` (Claude) or plain env vars (Codex). The Claude **app** uses its own connectors and is a separate surface. Default email send (SMTP) and all enrichment are pure Python stdlib + `httpx`, so nothing is OS-specific except the optional macOS `mailapp` channel.

## License

MIT
