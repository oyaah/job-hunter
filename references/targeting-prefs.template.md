# Targeting Preferences

> Filled during `/job-hunter:setup`. The `target-scout` agent reads this to build a fit-scored shortlist of companies and the specific people who matter. Generalized from a research-track internship hunt, but works for any role type.

## Role focus
<!-- The exact roles you're targeting. Be specific. -->
_e.g. "AI engineering intern, ML engineering intern, applied-research intern"_

## Primary differentiator
<!-- What should lead your outreach. This sets whether you target research-track or product-track first. -->
_e.g. "Publications → lead with research at academic labs + research-heavy startups" OR "Shipped products → lead with builder war-stories at product companies"_

## Company filters
- **Size:** <!-- startup | midsize | big-MNC | any. Can be a ranked preference. -->
- **Funding/stage:** <!-- e.g. "funded (Seed+), has budget for interns" | "any" -->
- **Has interns / early-career roles:** <!-- yes/prefer/any -->
- **Geography:** <!-- onsite cities, remote-ok, hybrid -->

## Affinity signals (boost fit score when present)
- **Same college/alumni:** <!-- your school(s); set "require" or "boost" -->
- **Skill overlap:** <!-- the skills that make you a real edge; companies using these rank higher -->
- **Domain overlap:** <!-- industries/problem-spaces where your background is a custom fit -->
- **Other:** <!-- partner institutions, specific tech stacks, anything that makes you non-generic -->

## Who matters (decision-makers to find per company)
<!-- Priority order of roles to reach. -->
_e.g. "Founder/CTO at startups; hiring manager or team lead at midsize; PI/lab head for research; recruiter only as last resort"_

## Tiers (optional — group targets)
<!-- If you think in tiers, list them so the scout groups output. e.g. academic PIs → research startups → industry labs → structured programs → product (secondary). -->

## Hard nos
<!-- Companies, sectors, or role types to never surface. -->

---

## How the scout researches (built-in method)

1. **Don't fetch LinkedIn URLs directly** — they return auth walls. To resolve a person/company, search `"name + company + role"`.
2. **Fetch the company's product page directly** — the single most valuable move. Surfaces the specific hook (product name, approach, partner) that general search misses.
3. **One concrete hook per target** — that's what the message leads with.
4. **Never fabricate contacts.** Flag confidence. Email verification happens in the enrichment step, not here.
5. **Output a ranked shortlist**, not a 50-item dump: name + role/company, the one-line *why it fits you specifically*, the hook, and a realism read.
