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

# Phase 6 Step 6.4 -- deliberately defaults TRUE, breaking this file's usual "missing setting
# = off" rule. That rule exists to keep risky autonomous SENDS (to real leads) off by
# default; this switch only ever emails the admin's own inbox about the admin's own system,
# so there's no external risk to guard against, and defaulting it off would recreate the
# exact blindness this phase exists to fix on every fresh install.
STUCK_ALERT_ENABLED = "stuck_alert_enabled"
# Minimum minutes between two stuck-alert emails -- an ongoing outage must not turn into an
# email storm; the tick keeps checking every pass, it just doesn't re-notify until this
# cooldown elapses (or the problem clears and recurs).
STUCK_ALERT_COOLDOWN_MINUTES = "stuck_alert_cooldown_minutes"
# ISO timestamp of the last stuck-alert send -- internal bookkeeping, not dashboard-editable.
STUCK_ALERT_LAST_SENT_AT = "stuck_alert_last_sent_at"

# Phase 11 Step 11.4 -- our OWN contact details, shown in the contact block of every
# structured outreach email. Deliberately settings rather than a new table or a Config
# constant: these change (a new number, a new profile link) without the change being a
# deploy, which is the entire reason system_settings exists. Each one is independently
# optional -- an empty value simply drops its line, by the same Step 11.3 rule that drops
# a whole section when it has no content, so a business that has no profile page just has
# one fewer row rather than a blank label.
COMPANY_CONTACT_EMAIL = "company_contact_email"
COMPANY_CONTACT_PHONE = "company_contact_phone"
COMPANY_WEBSITE_URL = "company_website_url"
COMPANY_PROFILE_URL = "company_profile_url"

COMPANY_CONTACT_KEYS = (COMPANY_CONTACT_EMAIL, COMPANY_CONTACT_PHONE,
                        COMPANY_WEBSITE_URL, COMPANY_PROFILE_URL)

# Phase 15 Step 15(B).2 -- the real per-search cost is admin-configurable rather than
# hardcoded, since this project cannot independently verify Serper's own current billed
# rate; the admin sets the real number once they know it. Monthly budget resets are
# judged against `prospect_searches.created_at` directly (real spend already recorded
# there), never a separate running counter that could drift from the real rows.
PROSPECT_SEARCH_MONTHLY_BUDGET = "prospect_search_monthly_budget"
PROSPECT_SEARCH_COST_PER_SEARCH = "prospect_search_cost_per_search"

STR_KEYS = {EOD_REPORT_RECIPIENTS, EOD_REPORT_WHATSAPP_RECIPIENTS, STUCK_ALERT_LAST_SENT_AT,
            *COMPANY_CONTACT_KEYS}
INT_KEYS = {OUTREACH_DAILY_CAP_EMAIL, OUTREACH_DAILY_CAP_WHATSAPP, DISCOVERY_COOLDOWN_HOURS,
            STUCK_ALERT_COOLDOWN_MINUTES}
FLOAT_KEYS = {PROSPECT_SEARCH_MONTHLY_BUDGET, PROSPECT_SEARCH_COST_PER_SEARCH}


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


def get_float(db, key: str, default: float = 0.0) -> float:
    row = db.get(SystemSetting, key)
    if row is None:
        return default
    try:
        return float(row.value)
    except (TypeError, ValueError):
        return default


def set_float(db, key: str, value: float) -> None:
    set_str(db, key, str(float(value)))


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
        STUCK_ALERT_ENABLED: get_bool(db, STUCK_ALERT_ENABLED, default=True),
        STUCK_ALERT_COOLDOWN_MINUTES: get_int(db, STUCK_ALERT_COOLDOWN_MINUTES, default=60),
        # Default to empty, not to a plausible-looking placeholder: an unset contact
        # detail must render as absent, never as a wrong address a real lead might use.
        **{key: get_str(db, key, default="") for key in COMPANY_CONTACT_KEYS},
        # Phase 15 Step 15(B).2 -- budget defaults to 0.0 (blocked), the same fail-safe
        # posture as AUTONOMOUS_OUTREACH_ENABLED: a feature that spends real money never
        # silently runs until a human explicitly sets a real, non-zero budget.
        PROSPECT_SEARCH_MONTHLY_BUDGET: get_float(db, PROSPECT_SEARCH_MONTHLY_BUDGET, default=0.0),
        PROSPECT_SEARCH_COST_PER_SEARCH: get_float(db, PROSPECT_SEARCH_COST_PER_SEARCH, default=0.01),
    }
