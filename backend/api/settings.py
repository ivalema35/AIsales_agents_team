"""Dashboard-controlled runtime switches (Step 4.4) -- discovery/outreach on-off, backed
by system_settings (checked fresh every scheduler tick, no process restart needed)."""
from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from services.system_settings import (
    get_all, set_bool, DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED, AUTO_REPLY_ENABLED)

settings_bp = Blueprint("settings", __name__, url_prefix="/api/v1/settings")

_KNOWN_KEYS = {DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED, AUTO_REPLY_ENABLED}


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

    for key, value in data.items():
        if not isinstance(value, bool):
            return jsonify({"error": [f"{key} must be a boolean"]}), 422

    db = SessionLocal()
    try:
        for key, value in data.items():
            set_bool(db, key, value)
        return jsonify(get_all(db))
    finally:
        db.close()
