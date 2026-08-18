"""Dashboard-controlled runtime settings (Step 4.4, extended CRM_UI_UX_PLAN.md Phase 2)
-- discovery/outreach on-off, plus operational values (EOD recipients, send caps,
discovery cooldown) that used to be .env-only. All backed by system_settings (checked
fresh every scheduler/report tick, no process restart needed)."""
from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from services.system_settings import (
    get_all, set_bool, set_str, set_int,
    DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED, AUTO_REPLY_ENABLED,
    ACKNOWLEDGMENT_REPLY_ENABLED, EOD_REPORT_RECIPIENTS, EOD_REPORT_WHATSAPP_RECIPIENTS,
    OUTREACH_DAILY_CAP_EMAIL, OUTREACH_DAILY_CAP_WHATSAPP, DISCOVERY_COOLDOWN_HOURS,
    STR_KEYS, INT_KEYS)

settings_bp = Blueprint("settings", __name__, url_prefix="/api/v1/settings")

_BOOL_KEYS = {DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED, AUTO_REPLY_ENABLED,
              ACKNOWLEDGMENT_REPLY_ENABLED}
_KNOWN_KEYS = _BOOL_KEYS | STR_KEYS | INT_KEYS


@settings_bp.route("", methods=["GET"])
def get_settings():
    db = SessionLocal()
    try:
        return jsonify(get_all(db))
    finally:
        db.close()


@settings_bp.route("", methods=["PATCH"])
def patch_settings():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    unknown = set(data.keys()) - _KNOWN_KEYS
    if unknown:
        return jsonify({"error": [f"unknown setting(s): {sorted(unknown)}"]}), 422

    errors = []
    for key, value in data.items():
        if key in _BOOL_KEYS and not isinstance(value, bool):
            errors.append(f"{key} must be a boolean")
        elif key in STR_KEYS and not isinstance(value, str):
            errors.append(f"{key} must be a string")
        elif key in INT_KEYS:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{key} must be a non-negative integer")
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        for key, value in data.items():
            if key in _BOOL_KEYS:
                set_bool(db, key, value)
            elif key in STR_KEYS:
                set_str(db, key, value)
            else:
                set_int(db, key, value)
        return jsonify(get_all(db))
    finally:
        db.close()
