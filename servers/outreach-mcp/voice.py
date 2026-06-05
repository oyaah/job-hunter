"""Voice engine — generalized anti-AI lint + voice-profile scaffolding.

Generalized from the user's personal yash-voice-writer skill: the five
non-negotiables become user-agnostic rules a distilled voice profile can
extend. `lint` is the hard gate U6 runs on every draft before review."""
import re

# Em-dash (and the en-dash people paste from docs) — the #1 AI tell.
EM_DASH_RE = re.compile(r"[—–]")

# Openers that scream template/AI. Matched case-insensitively at any position.
BANNED_OPENERS = [
    "i am writing to express",
    "i hope this email finds you well",
    "i am excited about the opportunity",
    "i am reaching out to",
    "i wanted to reach out",
    "to whom it may concern",
]

# Corporate/AI filler words. Whole-word match, case-insensitive.
BANNED_WORDS = [
    "leverage", "synergy", "passionate", "thrilled", "delve", "robust",
    "spearheaded", "utilize", "esteemed", "groundbreaking", "cutting-edge",
    "results-driven", "proven track record",
]


def lint(text: str) -> list:
    """Return a list of {type, match, advice} violations. Empty list = clean."""
    issues = []
    for m in EM_DASH_RE.finditer(text):
        issues.append({
            "type": "em_dash",
            "match": m.group(0),
            "advice": "Replace with a period, comma, or split the sentence. No em/en dashes.",
        })
    low = text.lower()
    for opener in BANNED_OPENERS:
        idx = low.find(opener)
        if idx != -1:
            issues.append({
                "type": "ai_cadence",
                "match": text[idx:idx + len(opener)],
                "advice": "Drop the template opener. Lead with who you are + what you build.",
            })
    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            issues.append({
                "type": "filler_word",
                "match": word,
                "advice": f"'{word}' reads as AI/corporate. Use a plainer, specific word.",
            })
    return issues


def is_clean(text: str) -> bool:
    return not lint(text)


# Slots a distilled voice profile fills (U3 setup writes these from user samples).
PROFILE_SLOTS = [
    "identity_line",      # one-line who-they-are + what they build
    "differentiator",     # the headline edge (e.g. research, shipped product)
    "default_register",   # cold-pitch | warm-reply | technical-flex | casual | formal
    "signoff",            # plain sign-off the user actually uses
    "honesty_guardrails", # gaps to state honestly, claims never to overstate
    "toolkit",            # real skills/projects, used accurately
    "banned_extra",       # user-specific words/phrases to also avoid
]
