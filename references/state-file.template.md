# State files — how the model tracks everything (no database)

All pipeline state lives in plain files under the data dir (`${CLAUDE_PLUGIN_DATA}` at runtime, `~/.config/job-hunter/` locally). You (the model) read and write them directly with Read/Write/Edit. There are no state tools — the files *are* the state.

## Per-company: `state/<company-slug>.json`
```json
{
  "company": "Acme Corp",
  "slug": "acme",
  "status": "drafted",            // new|targeted|enriched|researched|drafted|review|sent|done
  "fit_score": 8.5,
  "contacts": [
    {
      "name": "Jane Doe",
      "role": "CTO",
      "linkedin_url": "https://linkedin.com/in/jane",
      "hook": "the fraud-pipeline talk she gave",
      "email": "jane@acme.com",
      "email_status": "verified",  // verified|guessed|null  (only 'verified' is send-ready)
      "phone": null,
      "research": "concise digest of who she is + the hook",
      "email_draft": { "subject": "...", "body": "...", "status": "sent" },
      "linkedin": { "note": "...", "dm": "...", "status": "DM_SENT" }
      // linkedin.status: DRAFTED|QUEUED|SENT|ACCEPTED|DM_REVIEW|DM_SENT
    }
  ]
}
```
Update a contact's status by editing this file. Advancing the company lifecycle = changing `status`.

## The board: `pipeline.md`
A human-readable table you keep in sync so `/job-hunter:status` and the user can see everything at a glance:
```
| Company | Status   | Contacts | Sent | LinkedIn |
|---------|----------|----------|------|----------|
| Acme    | sent     | 1        | 1    | DM_SENT  |
```

## Learnings: `learnings.md`
Append-only, timestamped. Every review edit / rejection / stated preference becomes a line:
```
- 2026-06-06 [voice] user cut the humor close on formal emails
- 2026-06-06 [targeting] skip companies under 10 people
```

## Profiles: `voice-profile.md`, `targeting-prefs.md`
The distilled, durable version of the learnings. Reflection = you rewriting these files from `learnings.md` (see the reflect skill). Loaded before every draft/target.

## What stays a tool (the model can't do these itself)
`enrich_contact`, `verify_email`, `credits_status` (Hunter HTTP), `send_email` (gated send), `voice_lint` (deterministic), `linkedin_guard`/`linkedin_record` (honest cross-session counter), `health`. LinkedIn actions go through the bundled `linkedin` MCP. Everything else is a file you edit.
