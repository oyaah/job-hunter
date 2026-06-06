<div align="center">

# 🦺 job-hunter

### Be the yellow helmet in a sea of grey.

**An AI plugin that runs your entire job-hunt outreach — finds the right people, writes emails that sound like *you*, works LinkedIn in your own browser — company after company, while you approve every send.**

[![CI](https://github.com/oyaah/job-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/oyaah/job-hunter/actions)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-7C3AED)](https://docs.claude.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)

</div>

---

## The problem

The job market is a crowd. Hundreds of identical applicants, identical resumes, identical "I am writing to express my keen interest" emails — all landing in the same ignored inbox. Applying through a portal makes you grey. **One.** Of. **Thousands.**

The people who get the interview don't apply harder. They reach the *right human* with a message that proves they actually looked — and they do it at *every* target company, not just the two they had energy for that week.

That's slow, repetitive, and research-heavy to do by hand. So most people don't. They stay grey.

## What job-hunter does

It does the hard part, at scale, in your voice — and **you stay in control of every send.**

```
your resume + a list of companies
        │
        ▼
  find the people who matter      → founders, hiring managers, the lead who'd actually read it
  get their verified email        → no guessing, no bounces
  research each person            → their work, their posts, the one real hook
  write the outreach in YOUR voice → no AI tells, no "I am thrilled to" — sounds like you typed it
        │
        ▼
  YOU review it  ──►  approve / edit / reject
        │
        ▼
  send the email + the LinkedIn connect   (in your own Chrome, your own session)
        │
        ▼
  when they accept  ──►  drafts the DM ──► you approve ──► sent
        │
        ▼
              next company. and the next. and the next.
```

And it **learns you**. Every time you edit a draft, it remembers *why* — shorter intros, drop the humor, lead with the project — so the next email needs less fixing. It gets more *you* over time.

## Why it makes you the yellow helmet

- **Right person, not a portal.** A real human who can say yes, reached directly.
- **Proof you looked.** Every message references something specific about *them* — the thing generic applicants never do.
- **Your voice, not a robot's.** A built-in lint hard-blocks the AI tells (em-dashes, "I am writing to express…", "leverage", "thrilled"). It reads like a sharp person wrote it in one sitting.
- **Volume *and* quality.** The trade-off everyone accepts — refused. Company after company, each one personal.
- **Runs in your own browser.** LinkedIn happens in *your* logged-in Chrome, not a sketchy headless scraper. Lighter, safer, and there's nothing extra to log into.
- **You approve everything.** Nothing leaves your account without you saying yes. It's an assistant, not a spam cannon.

## Who this is for

- **New grads & students** drowning in a flooded entry-level market.
- **Career switchers** who need to reach humans, not ATS filters.
- **Researchers / engineers** whose edge is specific work that a generic application buries.
- Anyone who knows **the personal cold email beats the 500th portal submission** — and wants to send 30 of them well, not 2.

Not for: bulk spam. It's deliberately rate-limited and human-reviewed. Quality is the whole point.

---

## Quickstart (try it in 2 minutes)

> Works in **Claude Code** today. Desktop-app bundle (`.mcpb`) and Codex supported too.

```bash
/plugin marketplace add oyaah/job-hunter
/plugin install job-hunter
# enable it, then:
/job-hunter:setup       # resume + your voice + one free API key + how you send mail
/job-hunter:hunt        # give it companies — it works them one by one, you approve each
```

That alone gets you verified emails and voice-matched drafts you approve and send. For the **hands-off, full-pipeline** experience (LinkedIn included, acceptances auto-watched), do the setup below once.

---

## ⚡ Full automation — what to have, what to do

The most hands-off version runs the whole arc — find → enrich → research → draft → **you approve** → send email **and** work LinkedIn → watch for acceptances → draft + send the DM → next company — looping on its own. Here's the complete setup.

### 1. Have these ready

| # | What | Why | Free? |
|---|------|-----|-------|
| 1 | **[Claude Code](https://docs.claude.com/en/docs/claude-code)** + a direct Anthropic plan (Pro/Max) | runs the plugin; the plan unlocks the Chrome integration | plan is paid |
| 2 | **Python 3.12+** | runs the outreach server (`python3 --version`) | ✅ |
| 3 | **[Hunter.io](https://hunter.io/api-keys) API key** | finds *verified* emails — no guessing, no bounces | ✅ 50/mo |
| 4 | **A send channel** — a Gmail **[App Password](https://myaccount.google.com/apppasswords)** (recommended) | so email actually sends, hands-off, on any OS | ✅ |
| 5 | **[Claude in Chrome](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) extension** + signed into LinkedIn in that Chrome | LinkedIn runs in *your* real session — trusted clicks, no scraper | ✅ |
| 6 | *(mac fallback)* **[Node.js](https://nodejs.org)** | powers the `macos-automator` fallback that drives Chrome when the extension isn't available | ✅ |

### 2. Do this once

```bash
# a. install + enable the plugin
/plugin marketplace add oyaah/job-hunter
/plugin install job-hunter

# b. turn on Chrome control (the LinkedIn engine)
/chrome                      # or launch with:  claude --chrome
#    → keep a Chrome window signed into LinkedIn

# c. run the guided setup — it walks you through the rest
/job-hunter:setup            # resume · your writing voice · Hunter key · Gmail App Password
```

**Grant the mac permissions** (only needed for the `macos-automator` fallback, and asked for on first use): System Settings → Privacy & Security → **Automation** *and* **Accessibility** → enable **your terminal app** (whatever runs Claude Code — e.g. Ghostty, Terminal, iTerm) for **Google Chrome** and **System Events**; and in Chrome, **View → Developer → Allow JavaScript from Apple Events**.

> ⚠️ **After granting Accessibility, fully quit and reopen your terminal app.** macOS caches the old "denied" state until the app restarts, so real clicks/keystrokes will keep failing (`-1719 not allowed assistive access`) until you do. Automation (reading/navigating Chrome) works without a restart; Accessibility (clicking/typing) needs one. This is why **Claude in Chrome is the smoother path** — it issues trusted clicks itself and needs none of these grants.

### 3. Then let it run

```bash
/job-hunter:hunt                 # feed it companies; it works them one by one, you approve each send
/job-hunter:watch                # checks who accepted your LinkedIn requests, drafts their DMs
/job-hunter:status               # where every contact stands
```

Want it truly hands-off? Pair the watcher with `/loop` on a slow cadence so acceptances turn into reviewed DMs without you babysitting:

```bash
/loop 3h /job-hunter:watch
```

> **One honest note on "full" automation.** LinkedIn outreach runs in your real Chrome via **Claude in Chrome**, which issues *trusted* clicks — that's what reliably opens a connect dialog or sends a DM. The plain `macos-automator` fallback is great for opening Chrome, searching, and reading the page, but LinkedIn's anti-bot guards reject *synthetic* clicks, so on the fallback path you may finish the final click yourself. Either way, **every** note and DM still passes your review gate first — automation never means "unsupervised."

---

## Choosing how you send mail

SMTP with a Gmail App Password is the only fully hands-off path on every OS — use it unless you have a reason not to.

| Channel | OS | Setup | Behaviour |
|---------|-----|-------|-----------|
| **SMTP** *(recommended)* | mac / win / linux | a Gmail **[App Password](https://myaccount.google.com/apppasswords)** (enable 2FA first) | **sends** silently, zero-touch, no token expiry |
| **`local`** | macOS | nothing — uses Mail.app you're already signed into | **sends** via Mail.app |
| **`local`** | Windows | nothing if **Outlook** is installed & configured | Outlook → **sends**; otherwise opens your default client **pre-filled** (you click Send) |
| **`local`** | Linux | nothing — uses `xdg-email` / Thunderbird | opens a compose window **pre-filled** (you click Send) |
| **Gmail OAuth** | mac / win / linux | a Desktop `credentials.json` from Google Cloud | **sends**; re-auth ~weekly (Testing mode) |

The `local` channel never *pretends* it sent: when it can only pre-fill a draft (Linux, or Windows without Outlook) `send_email` returns `delivery: "composed"` and tells you to click Send.

## Optional paid power-ups

Apollo, ContactOut, and Lemlist plug in if you already pay for them (better enrichment / sequenced sending). The plugin works great without any of them.

---

## How it's built (and why it's light)

The best Claude plugins win by trusting the model and giving it only the tools it truly needs. job-hunter follows that:

- **The model drives everything through plain files it edits directly** — your pipeline, learnings, and voice profile are just markdown/JSON you can open and read. State is files, not a database.
- **Capability comes from your own environment.** The plugin ships *context* (a LinkedIn playbook) and a handful of load-bearing tools, not a bundled browser. LinkedIn rides your Chrome; mac scripting rides the thin `macos-automator` server. Channel precedence mirrors Claude's own: **Chrome → macos-automator → computer-use**, cheapest reliable first.
- **Real code exists only for what the model can't do itself** — verified email lookup, gated mail send, the anti-AI voice lint, and an honest cross-session LinkedIn rate limit. **8 small tools, no database, zero LinkedIn tools loaded until you act.**

See [`SPEC.md`](SPEC.md) for the full design, [`CLAUDE.md`](CLAUDE.md) for the philosophy, and [`references/linkedin-playbook.md`](references/linkedin-playbook.md) for exactly how it works LinkedIn.

## Safety, plainly

- **Nothing sends without your explicit approval** — email and LinkedIn both.
- **Never invents an email address** — only verified ones go out.
- **LinkedIn stays human-paced** — a daily cap (default 40), real review, no bulk blasting. (LinkedIn automation is against their ToS; this keeps it gentle and gated, but use your judgment.)
- **Your keys live in your OS keychain**, never in this repo.

## License

MIT — yours to use and adapt.

<div align="center">
<br>
<b>Stop being grey. Reach the right people, in your own voice, at every company that matters.</b>
<br><br>
⭐ Star it if a flooded job market has ever made you feel invisible.
</div>
