"""Self-evolving layer. The system records what it learns about THIS user —
from review edits, rejections, approvals, or explicit guidance — and loads it
before every drafting/targeting decision. Repeated insights reinforce (weight
climbs), so the workflow tunes itself to the user over time instead of being
hard-coded. Minimal mechanism, model-driven: agents decide what's worth learning."""


def record(conn, category, insight, source=None, weight=1.0):
    """Add an insight, or reinforce it if already known (weight accumulates)."""
    conn.execute(
        """INSERT INTO learnings (category, insight, weight, source)
           VALUES (?,?,?,?)
           ON CONFLICT(category, insight) DO UPDATE SET
             weight = learnings.weight + excluded.weight,
             source = excluded.source,
             updated_at = datetime('now')""",
        (category, insight, weight, source),
    )
    conn.commit()


def get(conn, category=None, limit=None):
    """Insights, strongest first. Filter by category, or get all (for context loading)."""
    q = "SELECT id, category, insight, weight, source FROM learnings"
    params = []
    if category:
        q += " WHERE category=?"
        params.append(category)
    q += " ORDER BY weight DESC, updated_at DESC"
    if limit:
        q += " LIMIT ?"
        params.append(limit)
    return [dict(r) for r in conn.execute(q, params).fetchall()]


def forget(conn, learning_id):
    conn.execute("DELETE FROM learnings WHERE id=?", (learning_id,))
    conn.commit()


def as_context(conn, categories=None):
    """Render learnings as a compact block for an agent's prompt. The system's
    accumulated understanding of the user, ready to inject before a decision."""
    rows = get(conn)
    if categories:
        rows = [r for r in rows if r["category"] in categories]
    if not rows:
        return ""
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r["insight"])
    blocks = []
    for cat, insights in by_cat.items():
        lines = "\n".join(f"- {i}" for i in insights)
        blocks.append(f"### What I've learned about you — {cat}\n{lines}")
    return "\n\n".join(blocks)
