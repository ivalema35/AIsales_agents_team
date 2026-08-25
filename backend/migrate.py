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
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            raw.executescript(f.read())
        _seed_default_channel_policy(raw)
        _backfill_lead_reference_codes(raw)
    print("Schema applied.")


if __name__ == "__main__":
    run()
