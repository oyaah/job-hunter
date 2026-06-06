<div align="center">

# 🦺 job-hunter

### Be the yellow helmet in a sea of grey.

**An AI plugin that runs your whole job-hunt outreach — finds the right people, writes emails that sound like *you*, and works LinkedIn — company after company, while you approve each one.**

[![CI](https://github.com/oyaah/job-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/oyaah/job-hunter/actions)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-7C3AED)](https://docs.claude.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)

</div>

---

## The problem

The job market is a crowd. Hundreds of identical applicants, identical resumes, identical "I am writing to express my keen interest" emails — all landing in the same ignored inbox. Applying through a portal makes you grey. **One.** Of. **Thousands.**

The people who get the interview don't apply harder. They reach the *right human* with a message that proves they actually looked — and they do it at *every* target company, not just the two they had energy for that week.

That's hard to do by hand. It's slow, it's repetitive, and good outreach takes real research per person. So most people don't. They stay grey.

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
  send the email + the LinkedIn connect
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
- **Volume *and* quality.** The thing that's normally a trade-off. Company after company, each one personal.
- **You approve everything.** Nothing leaves your account without you saying yes. It's an assistant, not a spam cannon.

## Who this is for

- **New grads & students** drowning in a flooded entry-level market.
- **Career switchers** who need to reach humans, not ATS filters.
- **Researchers / engineers** whose edge is specific work that a generic application buries.
- Anyone who knows **the personal cold email beats the 500th portal submission** — and wants to send 30 of them well, not 2.

Not for: bulk spam. It's deliberately rate-limited and human-reviewed. Quality is the whole point.

## Quickstart

> Works in **Claude Code** today. Desktop-app bundle (`.mcpb`) and Codex supported too.

```bash
# 1. install (Claude Code)
/plugin marketplace add oyaah/job-hunter
/plugin install job-hunter
# enable it, then:
/job-hunter:setup       # resume + your voice + one free API key + how you send mail

# 2. hunt
/job-hunter:hunt        # give it companies — it works them one by one, you approve each
/job-hunter:watch       # checks LinkedIn acceptances, drafts the DMs
/job-hunter:status      # where everything stands
```

**What you need (all free):**
- A **[Hunter.io](https://hunter.io/api-keys)** key — free, finds verified emails.
- A way to send mail — **macOS Mail.app** (zero setup, it's already signed in) or a **Gmail [App Password](https://myaccount.google.com/apppasswords)** (works on any OS). A one-click Google sign-in option is coming.
- For LinkedIn automation: **[uv](https://docs.astral.sh/uv/)** + one browser login the first time.

Optional paid power-ups (Apollo, ContactOut, Lemlist) plug in if you have them; it works great without.

## How it's built (and why it's light)

The best Claude plugins win by trusting the model and giving it only the tools it truly needs. job-hunter follows that: **the model drives everything through simple files it edits directly** (your pipeline, learnings, and voice profile are just markdown/JSON you can read). Real code exists only for the handful of things the model *can't* do itself — verified email lookup, sending mail, the anti-AI lint, and an honest LinkedIn rate limit. **8 small tools, no database.** Simple wins.

See [`SPEC.md`](SPEC.md) for the full design and [`CLAUDE.md`](CLAUDE.md) for the philosophy.

## Safety, plainly

- **Nothing sends without your explicit approval** — email and LinkedIn both.
- **Never invents an email address** — only verified ones go out.
- **LinkedIn stays human-paced** — a daily cap, real review, no bulk blasting. (LinkedIn automation is against their ToS; this keeps it gentle and gated, but use your judgment.)
- **Your keys live in your OS keychain**, never in this repo.

## License

MIT — yours to use and adapt.

<div align="center">
<br>
<b>Stop being grey. Reach the right people, in your own voice, at every company that matters.</b>
<br><br>
⭐ Star it if a flooded job market has ever made you feel invisible.
</div>
