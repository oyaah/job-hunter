-- job-hunter outreach state + credit ledger

CREATE TABLE IF NOT EXISTS companies (
    slug        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'new',  -- new|targeted|enriched|researched|drafted|review|sent|done
    fit_score   REAL,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS contacts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    company_slug      TEXT NOT NULL REFERENCES companies(slug) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    role              TEXT,
    linkedin_url      TEXT,
    email             TEXT,
    email_status      TEXT,           -- verified|guessed|unavailable|null
    email_score       INTEGER,
    phone             TEXT,
    hook              TEXT,           -- the one concrete reference for the message
    enrichment_source TEXT,           -- hunter|apollo|contactout
    research_digest   TEXT,           -- compact person research
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id  INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    channel     TEXT NOT NULL,        -- email|li_note|li_dm
    subject     TEXT,
    body        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'draft',  -- draft|approved|rejected|sent
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    sent_at     TEXT
);

CREATE TABLE IF NOT EXISTS linkedin (
    contact_id  INTEGER PRIMARY KEY REFERENCES contacts(id) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'DRAFTED',  -- DRAFTED|QUEUED|SENT|ACCEPTED|EXPIRED|DM_REVIEW|DM_SENT
    note        TEXT,
    dm          TEXT,
    queued_at   TEXT,
    sent_at     TEXT,
    accepted_at TEXT
);

CREATE TABLE IF NOT EXISTS credits (
    service        TEXT NOT NULL,
    account_id     TEXT NOT NULL DEFAULT 'default',
    remaining      INTEGER NOT NULL DEFAULT 0,
    monthly_quota  INTEGER,
    reset_at       TEXT,
    status         TEXT NOT NULL DEFAULT 'ok',  -- ok|low|exhausted
    last_checked   TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (service, account_id)
);

CREATE TABLE IF NOT EXISTS ledger (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    service     TEXT NOT NULL,
    account_id  TEXT NOT NULL DEFAULT 'default',
    op          TEXT NOT NULL,
    cost        INTEGER NOT NULL DEFAULT 0,
    contact_id  INTEGER,
    ts          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company_slug);
CREATE INDEX IF NOT EXISTS idx_messages_contact ON messages(contact_id);

-- Self-evolving layer: insights the system learns about THIS user over time
-- (from review edits, rejections, explicit guidance). Loaded before every
-- drafting/targeting decision so the workflow tunes itself to the user.
CREATE TABLE IF NOT EXISTS learnings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     TEXT NOT NULL,          -- voice|targeting|enrichment|outreach|general
    insight      TEXT NOT NULL,
    weight       REAL NOT NULL DEFAULT 1.0,
    source       TEXT,                   -- review-edit|rejection|approval|explicit
    distilled_at TEXT,                   -- set when folded into a profile; NULL = pending
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(category, insight)
);
CREATE INDEX IF NOT EXISTS idx_learnings_cat ON learnings(category);

-- Distilled profiles: compact, durable principles the system reflects out of raw
-- learnings (Generative-Agents importance-threshold + Hermes patch-not-rewrite).
-- Byte-capped so they curate instead of growing forever. Loaded before drafting.
CREATE TABLE IF NOT EXISTS profiles (
    section     TEXT PRIMARY KEY,        -- voice|targeting
    content     TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
