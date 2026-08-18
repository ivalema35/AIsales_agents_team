from __future__ import annotations
"""Dashboard customization -- lets a human pin any Analytics chart onto the Dashboard's
own "Your widgets" section via an "Add to Home" button on the Analytics page. Persisted
server-side (system_settings, same pattern as every other dashboard-editable value) so
the same pinned set shows up from any browser/device, not just localStorage on one.
"""
import json

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from services.system_settings import get_str, set_str

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/v1/dashboard")

DASHBOARD_WIDGETS_KEY = "dashboard_widgets"
# Must match Analytics.jsx's own widget ids exactly -- keeps a stray/renamed id from
# ever silently surviving into a state nothing can render.
VALID_WIDGETS = {"funnel", "channel_performance", "trend", "by_product", "outreach_funnel"}


@dashboard_bp.route("/widgets", methods=["GET"])
def get_widgets():
    db = SessionLocal()
    try:
        raw = get_str(db, DASHBOARD_WIDGETS_KEY, default="[]")
        try:
            widgets = json.loads(raw)
        except (TypeError, ValueError):
            widgets = []
        return jsonify({"widgets": [w for w in widgets if w in VALID_WIDGETS]})
    finally:
        db.close()


@dashboard_bp.route("/widgets", methods=["PUT"])
def save_widgets():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("widgets"), list):
        return jsonify({"error": ["widgets must be a JSON array"]}), 422

    widgets = [w for w in data["widgets"] if w in VALID_WIDGETS]
    db = SessionLocal()
    try:
        set_str(db, DASHBOARD_WIDGETS_KEY, json.dumps(widgets))
        return jsonify({"widgets": widgets})
    finally:
        db.close()
