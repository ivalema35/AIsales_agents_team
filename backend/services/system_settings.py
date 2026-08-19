"""Dashboard-controlled runtime switches (Step 4.4). Unlike .env config (only read at
process start), these are checked fresh from the DB every time -- a toggle flipped from
the dashboard takes effect on the scheduler's next tick, no restart needed.

All switches default CLOSED/false if no row exists yet -- the same fail-safe default as
Config.AUTONOMOUS_OUTREACH_ENABLED (tracker.md A.3): a missing setting must never be
silently treated as "on".
"""
from __future__ import annotations
from database.models import SystemSetting

DISCOVERY_ENABLED = "discovery_enabled"
AUTONOMOUS_OUTREACH_ENABLED = "autonomous_outreach_enabled"
# Step 4.3: lets the AI auto-send its own drafted reply for a low-risk inbound message
# (a simple OBJECTION, high confidence, nothing pricing/legal/hostile-sounding).
# INTERESTED/DEMO_REQUESTED/high-risk/low-confidence always escalate to a human
# regardless of this switch -- it only ever governs the narrow low-stakes case.
AUTO_REPLY_ENABLED = "auto_reply_enabled"
# A short, safe "we got your message, we'll follow up shortly" holding reply sent
# immediately for ANY inbound message that escalates to a human (INTERESTED/DEMO_
# REQUESTED/high-risk/low-confidence) -- so a real lead is never met with silence while
# waiting for a human. Deliberately a SEPARATE switch from AUTO_REPLY_ENABLED: this never
# answers the actual question or makes any claim, it only acknowledges receipt, so it's a
# lower-risk capability than the substantive low-risk-OBJECTION auto-reply above.
ACKNOWLEDGMENT_REPLY_ENABLED = "acknowledgment_reply_enabled"

# CRM_UI_UX_PLAN.md Phase 2 -- previously .env-only (Config, read once at process start),
# now dashboard-editable and checked fresh, same "no restart needed" contract as the
# boolean switches above. Config's own env-var value is still each one's fallback DEFAULT
# (used until a human ever actually sets it from the dashboard) so a fresh install with no
# dashboard changes yet behaves exactly as before.
EOD_REPORT_RECIPIENTS = "eod_report_recipients"                    # comma-separated emails
EOD_REPORT_WHATSAPP_RECIPIENTS = "eod_report_whatsapp_recipients"  # comma-separated numbers
OUTREACH_DAILY_CAP_EMAIL = "outreach_daily_cap_email"
OUTREACH_DAILY_CAP_WHATSAPP = "outreach_daily_cap_whatsapp"
DISCOVERY_COOLDOWN_HOURS = "discovery_cooldown_hours"

STR_KEYS = {EOD_REPORT_RECIPIENTS, EOD_REPORT_WHATSAPP_RECIPIENTS}
INT_KEYS = {OUTREACH_DAILY_CAP_EMAIL, OUTREACH_DAILY_CAP_WHATSAPP, DISCOVERY_COOLDOWN_HOURS}


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


def get_str(db, key: str, default: str = "") -> str:
    row = db.get(SystemSetting, key)
    return row.value if row is not None else default


def set_str(db, key: str, value: str) -> None:
    row = db.get(SystemSetting, key)
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=key, value=value))
    db.commit()


def get_int(db, key: str, default: int = 0) -> int:
    row = db.get(SystemSetting, key)
    if row is None:
        return default
    try:
        return int(row.value)
    except (TypeError, ValueError):
        return default


def set_int(db, key: str, value: int) -> None:
    set_str(db, key, str(int(value)))


def get_all(db) -> dict:
    from config import Config  # local import -- avoids a module-load-order cycle with config.py
    return {
        DISCOVERY_ENABLED: get_bool(db, DISCOVERY_ENABLED, default=False),
        AUTONOMOUS_OUTREACH_ENABLED: get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=False),
        AUTO_REPLY_ENABLED: get_bool(db, AUTO_REPLY_ENABLED, default=False),
        ACKNOWLEDGMENT_REPLY_ENABLED: get_bool(db, ACKNOWLEDGMENT_REPLY_ENABLED, default=False),
        EOD_REPORT_RECIPIENTS: get_str(db, EOD_REPORT_RECIPIENTS, default=",".join(Config.EOD_REPORT_RECIPIENTS)),
        EOD_REPORT_WHATSAPP_RECIPIENTS: get_str(
            db, EOD_REPORT_WHATSAPP_RECIPIENTS, default=",".join(Config.EOD_REPORT_WHATSAPP_RECIPIENTS)),
        OUTREACH_DAILY_CAP_EMAIL: get_int(db, OUTREACH_DAILY_CAP_EMAIL, default=Config.OUTREACH_DAILY_CAP_EMAIL),
        OUTREACH_DAILY_CAP_WHATSAPP: get_int(
            db, OUTREACH_DAILY_CAP_WHATSAPP, default=Config.OUTREACH_DAILY_CAP_WHATSAPP),
        DISCOVERY_COOLDOWN_HOURS: get_int(db, DISCOVERY_COOLDOWN_HOURS, default=Config.DISCOVERY_COOLDOWN_HOURS),
    }
