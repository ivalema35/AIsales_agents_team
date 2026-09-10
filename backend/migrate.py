import secrets

from database.db_config import engine

# New columns on already-existing tables -- schema.sql's CREATE TABLE IF NOT EXISTS only
# handles brand-new tables, so a column added to an existing table's definition needs an
# explicit, idempotent ALTER TABLE here (checked against PRAGMA table_info) or it silently
# never reaches a dev DB that was created before the column was added.
COLUMN_MIGRATIONS = [
    ("products", "target_regions", "TEXT DEFAULT '[]'"),
    ("leads", "instagram_url", "TEXT"),
    ("leads", "facebook_url", "TEXT"),
    ("leads", "linkedin_url", "TEXT"),
    # Added mid-Step-6.1, after real-process testing showed a single global staleness window
    # can't work across loops running at 2s vs 300s. Any DB that already created
    # system_heartbeats without this column needs the ALTER, not just the CREATE.
    ("system_heartbeats", "expected_interval_seconds", "INTEGER NOT NULL DEFAULT 60"),
    ("products", "target_business_categories", "TEXT DEFAULT '[]'"),
    ("products", "target_person_roles", "TEXT DEFAULT '[]'"),
    ("outreach_logs", "subject_candidates", "TEXT"),
    ("products", "followup_cadence_days", "TEXT DEFAULT '[]'"),
    ("whatsapp_templates", "product_id", "TEXT"),
    ("whatsapp_templates", "is_active", "INTEGER DEFAULT 1"),
    ("whatsapp_templates", "origin", "TEXT DEFAULT 'ADMIN'"),
    ("whatsapp_templates", "reasoning", "TEXT"),
    ("outreach_logs", "open_count", "INTEGER DEFAULT 0"),
    ("products", "cross_sell_product_ids", "TEXT DEFAULT '[]'"),
    ("leads", "reference_code", "TEXT"),
    ("whatsapp_templates", "followup_level", "INTEGER"),
    ("whatsapp_templates", "button_url", "TEXT"),
    ("whatsapp_templates", "button_label", "TEXT"),
    ("outreach_logs", "content_sections", "TEXT"),
    ("products", "default_tone", "TEXT"),
    ("products", "default_format", "TEXT"),
    ("leads", "campaign_id", "TEXT"),
    ("campaigns", "last_approved_date", "TEXT"),
    ("campaigns", "lead_count_goal", "INTEGER"),
    ("campaigns", "pending_strategy_proposal", "TEXT"),
    ("discovery_runs", "campaign_id", "TEXT"),
    ("campaigns", "watchdog_alert", "TEXT"),
    ("campaigns", "kickoff_draft", "TEXT"),
    ("campaigns", "email_render_mode", "TEXT"),
    ("campaigns", "last_todo_signal", "TEXT"),
    ("todo_items", "is_blocker", "INTEGER DEFAULT 0"),
    ("todo_items", "lead_id", "TEXT"),
    ("whatsapp_templates", "qc_caution", "TEXT"),
    ("whatsapp_templates", "draft_context", "TEXT"),
    ("whatsapp_templates", "button_2_url", "TEXT"),
    ("whatsapp_templates", "button_2_label", "TEXT"),
    ("campaigns", "email_outreach_approved_at", "TIMESTAMP"),
    ("campaigns", "whatsapp_outreach_approved_at", "TIMESTAMP"),
    ("campaigns", "test_outreach_sent_at", "TIMESTAMP"),
    ("whatsapp_templates", "header_image_url", "TEXT"),
]


def _table_exists(raw_conn, table):
    row = raw_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _add_missing_columns(raw_conn):
    for table, column, coltype in COLUMN_MIGRATIONS:
        if not _table_exists(raw_conn, table):
            continue  # brand-new table -- schema.sql's own CREATE TABLE already has this column
        existing = {row[1] for row in raw_conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            raw_conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def _seed_default_channel_policy(raw_conn):
    """Phase 10 Step 10.1: an unconfigured country now falls back to EMAIL-only (never
    guesses WHATSAPP) -- correct for a genuinely new region, but WITHOUT this seed it
    would also silently break WhatsApp for every existing India lead the moment this
    migration runs, since 'IN' is products.target_country's own default and today's
    real, working behavior there includes WhatsApp. Seeding IN explicitly is what makes
    the step's own DoD promise ("an Indian lead is unaffected") actually true, not just
    stated. Idempotent -- only inserts if no row for 'IN' exists yet, so a dashboard
    admin who later edits this policy is never overwritten by a re-run.
    """
    row = raw_conn.execute(
        "SELECT 1 FROM channel_policies WHERE country_code='IN'"
    ).fetchone()
    if row is None:
        raw_conn.execute(
            "INSERT INTO channel_policies (id, country_code, allowed_channels) "
            "VALUES (lower(hex(randomblob(16))), 'IN', '[\"EMAIL\", \"WHATSAPP\"]')"
        )


def _fix_discovery_run_constraint(raw_conn):
    """2026-09-08/09, real live incident: `discovery_runs` kept its original
    UNIQUE(product_id, query, region) constraint even after cooldown tracking became
    per-campaign (Step 17.7) -- two campaigns for the same product proposing the
    identical query+region hit a real IntegrityError that cascaded into a 16-hour
    scheduler outage (see database/models.py's DiscoveryRun docstring for the full
    incident). SQLite can't ALTER a constraint in place, so this rebuilds the table --
    safe here because this table is pure cooldown bookkeeping: losing a row just means
    one campaign's next discovery tick isn't rate-limited by an old timestamp, never a
    real data loss. Idempotent: only runs while the OLD constraint is still present.

    2026-09-09 follow-up, real bug found live: the original idempotency check looked for
    a constraint NAME ("uq_discovery_run_v2") that this rebuild's own `UNIQUE (...)` clause
    never actually assigns (SQLite constraints declared this way are unnamed) -- so that
    check could never match, and this rebuilt the entire table on EVERY migrate.py run
    (harmless here since it's pure cooldown data safely copied each time, but wasteful, and
    a needless risk while the discovery scheduler could be mid-tick against this same
    table). Fixed to check for the OLD constraint's real shape instead of a name that was
    never actually written anywhere.
    """
    if not _table_exists(raw_conn, "discovery_runs"):
        return  # brand-new DB -- schema.sql's own CREATE already has the correct constraint
    existing_sql = raw_conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='discovery_runs'"
    ).fetchone()
    if not existing_sql or "UNIQUE (product_id, query, region)" not in (existing_sql[0] or ""):
        return  # already migrated (or somehow already correct)

    raw_conn.execute("ALTER TABLE discovery_runs RENAME TO discovery_runs_old_uq")
    raw_conn.execute("""
        CREATE TABLE discovery_runs (
            id            TEXT PRIMARY KEY,
            product_id    TEXT NOT NULL,
            query         TEXT NOT NULL,
            region        TEXT NOT NULL,
            campaign_id   TEXT,
            last_run_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (campaign_id, query, region),
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
        )
    """)
    raw_conn.execute("""
        INSERT INTO discovery_runs (id, product_id, query, region, campaign_id, last_run_at)
        SELECT id, product_id, query, region, campaign_id, last_run_at FROM discovery_runs_old_uq
    """)
    raw_conn.execute("DROP TABLE discovery_runs_old_uq")
    print("discovery_runs: rebuilt with UNIQUE(campaign_id, query, region).")


def _backfill_lead_reference_codes(raw_conn):
    """Phase 12 Step 12.1 -- every lead that existed before this column shipped needs a
    real code too (the alert/UI feature has no "N/A" fallback in its own design; a lead
    with no code would just be unreferenceable in an alert). Runs AFTER the schema script,
    so the UNIQUE index already exists and a freak collision fails loudly here rather than
    silently creating a duplicate.
    """
    rows = raw_conn.execute("SELECT id FROM leads WHERE reference_code IS NULL").fetchall()
    for (lead_id,) in rows:
        while True:
            code = "LD-" + secrets.token_hex(4).upper()
            clash = raw_conn.execute(
                "SELECT 1 FROM leads WHERE reference_code = ?", (code,)
            ).fetchone()
            if not clash:
                break
        raw_conn.execute("UPDATE leads SET reference_code = ? WHERE id = ?", (code, lead_id))


def run():
    with engine.begin() as conn:
        raw = conn.connection
        # Column migrations run BEFORE the schema script -- a statement later in schema.sql
        # can reference a column that's new to an EXISTING table (e.g. an index on it), and
        # that statement would fail against a DB that predates the column if executescript
        # ran first (real ordering bug hit adding whatsapp_templates.product_id + its index
        # in the same change).
        _add_missing_columns(raw)
        _fix_discovery_run_constraint(raw)
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            raw.executescript(f.read())
        _seed_default_channel_policy(raw)
        _backfill_lead_reference_codes(raw)
    print("Schema applied.")


if __name__ == "__main__":
    run()
