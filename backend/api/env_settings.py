from __future__ import annotations
"""Dashboard view/edit over .env-backed Config values (CRM_UI_UX_PLAN.md Phase 2b) --
distinct from api/settings.py, which covers the dashboard-hot system_settings values.
These take effect only after the relevant process is restarted; see
services/env_settings.py's own docstring for why."""
from flask import Blueprint, jsonify, request

from services.env_settings import list_settings, update_settings

env_settings_bp = Blueprint("env_settings", __name__, url_prefix="/api/v1/env-settings")


@env_settings_bp.route("", methods=["GET"])
def get_env_settings():
    return jsonify(list_settings())


@env_settings_bp.route("", methods=["PATCH"])
def patch_env_settings():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422
    if not data:
        return jsonify({"error": ["request body must contain at least one setting"]}), 422
    for key, value in data.items():
        if not isinstance(value, str):
            return jsonify({"error": [f"{key} must be a string"]}), 422

    try:
        updated_keys = update_settings(data)
    except ValueError as exc:
        return jsonify({"error": [str(exc)]}), 422

    return jsonify({
        "updated": updated_keys,
        "note": "Saved to .env -- restart the relevant backend process(es) for this to take effect.",
        "settings": list_settings(),
    })
