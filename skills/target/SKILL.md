---
name: target
description: Build or refine the company + people shortlist for outreach. Use when the user says "find companies", "who should I reach out to", "build my target list", "/job-hunter:target", or wants to add/refine targets before hunting.
---

# Target

Turn the user's preferences (and a seed — a role, an industry, or a starting company list) into a fit-scored shortlist of companies and the people who matter at each.

Dispatch the **target-scout** agent (isolated context, returns a compact ranked shortlist). Pass it the user's `targeting-prefs.md`, the seed, and let it apply `learnings`. Persist results to the store.

Then show the user the shortlist and ask if it's right — too broad, wrong tier, missing a filter? Their reaction is signal: append it to `learnings.md` so the list improves every time. This is the loop that makes targeting yours, not generic.

When the user's happy, the companies are queued for `/job-hunter:hunt`.
