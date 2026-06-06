# Privacy Policy — job-hunter

**job-hunter runs entirely on your own machine.** It is a local Claude Code / Codex plugin, not a hosted service. There is no job-hunter server, account, or analytics.

## What it stores, and where
All data stays in local files under `~/.config/job-hunter/` (or your configured data dir): your resume-derived profile, per-company pipeline state, drafted messages, learnings, and two small usage counters. Nothing is uploaded to the author.

## Credentials
API keys (Hunter, optional Apollo/etc.) and any Gmail OAuth token are stored in your operating system's keychain or local config — never transmitted to the author and never committed to the repo.

## Third-party services *you* connect
When you provide keys, the plugin calls these on your behalf, from your machine: Hunter.io / Apollo / ContactOut (email enrichment), your Gmail (sending mail, via Gmail API or SMTP), and LinkedIn (via the bundled automation server, using your own logged-in session). Your use of each is governed by that service's own terms and privacy policy.

## Gmail data use
With the `gmail.send` scope, the plugin only **composes and sends** mail you have explicitly approved. It does not read, store, or transmit your inbox. Tokens live in your OS keychain.

## Contact
Questions: open an issue at https://github.com/oyaah/job-hunter.
