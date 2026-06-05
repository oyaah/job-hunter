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
- **LinkedIn** — semi-auto: the agent drafts + queues, **you click send** (zero ban risk). Acceptance is detected (opt-in read-only poll) or you tell it; then the DM surfaces for review.

## Safety posture

- **LinkedIn is never automated.** The agent prepares; you act. Programmatic connect/message violates LinkedIn ToS.
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
| `/job-hunter:status` | Pipeline board + credit balances |

## Requirements

- Python 3.10+, `pip install -r requirements.txt`
- **Free + required:** Hunter.io API key, a Google account (Gmail send)
- **Optional (paid):** Apollo, ContactOut, Lemlist API keys

## License

MIT
