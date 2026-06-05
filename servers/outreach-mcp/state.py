"""Per-company state store. `get_company` is the unit of context isolation (KTD2):
the orchestrator loads only the current company's full record, never all of them."""


def _touch(conn, slug):
    conn.execute("UPDATE companies SET updated_at=datetime('now') WHERE slug=?", (slug,))


def upsert_company(conn, slug, name, status=None, fit_score=None, notes=None):
    conn.execute(
        """INSERT INTO companies (slug, name, status, fit_score, notes)
           VALUES (?,?,COALESCE(?,'new'),?,?)
           ON CONFLICT(slug) DO UPDATE SET
             name=excluded.name,
             status=COALESCE(?, companies.status),
             fit_score=COALESCE(?, companies.fit_score),
             notes=COALESCE(?, companies.notes),
             updated_at=datetime('now')""",
        (slug, name, status, fit_score, notes, status, fit_score, notes),
    )
    conn.commit()
    return slug


def set_company_status(conn, slug, status):
    conn.execute("UPDATE companies SET status=?, updated_at=datetime('now') WHERE slug=?",
                 (status, slug))
    conn.commit()


def add_contact(conn, company_slug, name, role=None, linkedin_url=None, hook=None):
    cur = conn.execute(
        "INSERT INTO contacts (company_slug, name, role, linkedin_url, hook) VALUES (?,?,?,?,?)",
        (company_slug, name, role, linkedin_url, hook),
    )
    conn.commit()
    return cur.lastrowid


_CONTACT_FIELDS = {"name", "role", "linkedin_url", "email", "email_status",
                   "email_score", "phone", "hook", "enrichment_source", "research_digest"}


def update_contact(conn, contact_id, **fields):
    cols = {k: v for k, v in fields.items() if k in _CONTACT_FIELDS}
    if not cols:
        return
    sets = ", ".join(f"{k}=?" for k in cols)
    conn.execute(f"UPDATE contacts SET {sets} WHERE id=?", (*cols.values(), contact_id))
    conn.commit()


def get_contact(conn, contact_id):
    row = conn.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()
    return dict(row) if row else None


def add_message(conn, contact_id, channel, body, subject=None):
    cur = conn.execute(
        "INSERT INTO messages (contact_id, channel, subject, body) VALUES (?,?,?,?)",
        (contact_id, channel, subject, body),
    )
    conn.commit()
    return cur.lastrowid


def set_message_status(conn, message_id, status, sent=False):
    if sent:
        conn.execute("UPDATE messages SET status=?, sent_at=datetime('now') WHERE id=?",
                     (status, message_id))
    else:
        conn.execute("UPDATE messages SET status=? WHERE id=?", (status, message_id))
    conn.commit()


def upsert_linkedin(conn, contact_id, note=None, dm=None, status="DRAFTED"):
    conn.execute(
        """INSERT INTO linkedin (contact_id, status, note, dm) VALUES (?,?,?,?)
           ON CONFLICT(contact_id) DO UPDATE SET
             note=COALESCE(?, linkedin.note), dm=COALESCE(?, linkedin.dm)""",
        (contact_id, status, note, dm, note, dm),
    )
    conn.commit()


_LI_STAMPS = {"QUEUED": "queued_at", "SENT": "sent_at", "ACCEPTED": "accepted_at"}


def set_linkedin_status(conn, contact_id, status):
    stamp = _LI_STAMPS.get(status)
    if stamp:
        conn.execute(f"UPDATE linkedin SET status=?, {stamp}=datetime('now') WHERE contact_id=?",
                     (status, contact_id))
    else:
        conn.execute("UPDATE linkedin SET status=? WHERE contact_id=?", (status, contact_id))
    conn.commit()


def get_company(conn, slug):
    """Full nested record for ONE company — the context-isolation unit."""
    crow = conn.execute("SELECT * FROM companies WHERE slug=?", (slug,)).fetchone()
    if not crow:
        return None
    company = dict(crow)
    contacts = []
    for c in conn.execute("SELECT * FROM contacts WHERE company_slug=? ORDER BY id", (slug,)):
        contact = dict(c)
        contact["messages"] = [
            dict(m) for m in conn.execute(
                "SELECT * FROM messages WHERE contact_id=? ORDER BY id", (c["id"],))
        ]
        li = conn.execute("SELECT * FROM linkedin WHERE contact_id=?", (c["id"],)).fetchone()
        contact["linkedin"] = dict(li) if li else None
        contacts.append(contact)
    company["contacts"] = contacts
    return company


def pipeline_board(conn):
    """One row per company: status + contact/sent counts. For /status."""
    rows = conn.execute(
        """SELECT c.slug, c.name, c.status, c.fit_score,
                  COUNT(DISTINCT ct.id) AS contacts,
                  COUNT(DISTINCT CASE WHEN m.status='sent' THEN m.id END) AS sent
           FROM companies c
           LEFT JOIN contacts ct ON ct.company_slug = c.slug
           LEFT JOIN messages m ON m.contact_id = ct.id
           GROUP BY c.slug ORDER BY c.updated_at DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


def list_pending_messages(conn):
    """Drafts + approved-not-sent messages, joined with contact/company — for /review."""
    rows = conn.execute(
        """SELECT m.*, ct.name AS contact_name, ct.email AS contact_email,
                  ct.company_slug
           FROM messages m JOIN contacts ct ON ct.id = m.contact_id
           WHERE m.status IN ('draft','approved') ORDER BY m.id"""
    ).fetchall()
    return [dict(r) for r in rows]
