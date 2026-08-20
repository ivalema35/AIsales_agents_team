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
]


def _add_missing_columns(raw_conn):
    for table, column, coltype in COLUMN_MIGRATIONS:
        existing = {row[1] for row in raw_conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            raw_conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def run():
    with engine.begin() as conn:
        raw = conn.connection
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            raw.executescript(f.read())
        _add_missing_columns(raw)
    print("Schema applied.")


if __name__ == "__main__":
    run()
