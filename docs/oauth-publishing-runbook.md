# Gmail one-click OAuth — publishing runbook

The goal: a single published OAuth app so any user clicks "Allow" once and sends from their own Gmail — no App Password, no per-user Cloud Console. **This is an author-owned process** (Google review), not something the plugin runs. Until it's done, SMTP App Password + macOS Mail.app cover sending for everyone.

## The good news
`gmail.send` is a **sensitive** scope, *not restricted* → publishing needs Google's brand/consent review (~3–5 business days, free) and **no CASA third-party security audit** (that's only for restricted scopes). The installed-app `client_secret` is **public by Google's design** — PKCE carries the security — so shipping the `client_id` in the repo is fine.

## Steps (one-time, by the maintainer)
1. **Google Cloud Console → new project.** Enable the **Gmail API**.
2. **OAuth consent screen** → User type **External**. Fill app name, support email, logo, the homepage + privacy-policy URLs ([`PRIVACY.md`](../PRIVACY.md) hosted).
3. **Scopes** → add only `https://www.googleapis.com/auth/gmail.send`. Nothing else (keeps it sensitive, not restricted).
4. **Credentials → Create OAuth client ID → Desktop app.** Download `credentials.json`. Commit it as `servers/outreach-mcp/oauth_client.json` (client_id public; secret is non-secret for installed apps).
5. **Demo video** — record the consent flow + how the token is used (Google requires it for sensitive scopes).
6. **Submit for verification.** ~3–5 days. While pending, the app stays in **Testing** (100 test users, refresh tokens expire weekly) — fine for the author/beta.
7. **On approval → "In production".** Refresh tokens stop expiring; every user gets the one-click "Allow".

## Code side (already in place)
`integrations/gmail.py` runs the installed-app loopback flow (`InstalledAppFlow.run_local_server`, PKCE) against the shipped client, stores the token in the OS keychain, and `send_email(channel="gmail")` uses it. Once `oauth_client.json` ships and the app is verified, set `channel="gmail"` (or let `auto` prefer it).

## Until then
`send_email` defaults to `auto`: SMTP App Password → macOS Mail.app → OAuth. No one is blocked on the Google queue.
