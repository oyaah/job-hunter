"""Reflection / distillation — the self-evolving step (token-cheap).

Borrowed, deliberately minimal:
- Generative Agents: fire when accumulated importance (sum of un-distilled
  `weight`) crosses a threshold — proportional to signal, not time/count polling.
- Hermes / SkillOpt: patch a compact, BYTE-CAPPED profile (curate, don't grow).
- No extra LLM API call: the model already in the loop does the distilling
  reasoning when the server says it's due. This module only tracks the trigger,
  hands over the material, applies the patch, and marks learnings distilled.
- Effects apply next time the profile is loaded — not mid-draft — so no drift.
"""

THRESHOLD = 10.0     # distill once this much un-distilled weight accumulates
PROFILE_CAP = 2000   # hard byte cap per profile section (forces curation)
MATERIAL_LIMIT = 20  # most-weighted pending learnings to hand the model


def pending_weight(conn, category=None):
    q = "SELECT COALESCE(SUM(weight),0) AS w FROM learnings WHERE distilled_at IS NULL"
    params = []
    if category:
        q += " AND category=?"
        params.append(category)
    return conn.execute(q, params).fetchone()["w"]


def is_due(conn, category=None, threshold=THRESHOLD):
    return pending_weight(conn, category) >= threshold


def material(conn, category=None, limit=MATERIAL_LIMIT):
    """Top un-distilled learnings for the model to compress into principles."""
    q = ("SELECT id, category, insight, weight FROM learnings WHERE distilled_at IS NULL")
    params = []
    if category:
        q += " AND category=?"
        params.append(category)
    q += " ORDER BY weight DESC, updated_at DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(q, params).fetchall()]


def _clip_to_cap(content, cap):
    """Fit content under `cap` bytes. Prefer whole lines; if even the first line
    is over-cap, hard byte-slice it (on a UTF-8 boundary) so we keep a truncated
    principle rather than wiping the profile to empty (data-loss guard)."""
    clipped, size = [], 0
    for line in content.splitlines():
        nxt = size + len(line.encode()) + 1
        if nxt > cap:
            break
        clipped.append(line)
        size = nxt
    if clipped:
        return "\n".join(clipped)
    # No whole line fits: byte-slice the first line, trimming partial UTF-8 tail.
    return content.encode()[:cap].decode("utf-8", "ignore").strip()


def get_profile(conn, section):
    row = conn.execute("SELECT content FROM profiles WHERE section=?", (section,)).fetchone()
    return row["content"] if row else ""


def apply(conn, section, content, mark_category=None):
    """Replace a profile section with the model's distilled principles (byte-capped),
    and mark the pending learnings as distilled so they don't re-trigger. Raw
    learnings are kept (audit trail), just flagged."""
    content = content.strip()
    if not content:
        # Never blank a good profile or retire its source learnings on empty input.
        return {"section": section, "skipped": "empty content", "kept_existing": True}
    if len(content.encode()) > PROFILE_CAP:
        content = _clip_to_cap(content, PROFILE_CAP)
    conn.execute(
        "INSERT INTO profiles (section, content) VALUES (?,?) "
        "ON CONFLICT(section) DO UPDATE SET content=excluded.content, updated_at=datetime('now')",
        (section, content))
    cat = mark_category or section
    conn.execute(
        "UPDATE learnings SET distilled_at=datetime('now') "
        "WHERE distilled_at IS NULL AND category=?", (cat,))
    conn.commit()
    return {"section": section, "bytes": len(content.encode()), "capped": PROFILE_CAP}
