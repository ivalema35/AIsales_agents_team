"""Dashboard-controlled runtime switches (Step 4.4). Unlike .env config (only read at
process start), these are checked fresh from the DB every time -- a toggle flipped from
the dashboard takes effect on the scheduler's next tick, no restart needed.

All switches default CLOSED/false if no row exists yet -- the same fail-safe default as
Config.AUTONOMOUS_OUTREACH_ENABLED (tracker.md A.3): a missing setting must never be
silently treated as "on".
"""
from database.models import SystemSetting

DISCOVERY_ENABLED = "discovery_enabled"
AUTONOMOUS_OUTREACH_ENABLED = "autonomous_outreach_enabled"
# Step 4.3: lets the AI auto-send its own drafted reply for a low-risk inbound message
# (a simple OBJECTION, high confidence, nothing pricing/legal/hostile-sounding).
# INTERESTED/DEMO_REQUESTED/high-risk/low-confidence always escalate to a human
# regardless of this switch -- it only ever governs the narrow low-stakes case.
AUTO_REPLY_ENABLED = "auto_reply_enabled"


def get_bool(db, key: str, default: bool = False) -> bool:
    row = db.get(SystemSetting, key)
    if row is None:
        return default
    return row.value.lower() == "true"


def set_bool(db, key: str, value: bool) -> None:
    row = db.get(SystemSetting, key)
    if row:
        row.value = "true" if value else "false"
    else:
        db.add(SystemSetting(key=key, value="true" if value else "false"))
    db.commit()


def get_all(db) -> dict:
    return {
        DISCOVERY_ENABLED: get_bool(db, DISCOVERY_ENABLED, default=False),
        AUTONOMOUS_OUTREACH_ENABLED: get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=False),
        AUTO_REPLY_ENABLED: get_bool(db, AUTO_REPLY_ENABLED, default=False),
    }
