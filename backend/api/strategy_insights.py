from __future__ import annotations

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from services.strategy_reflection_service import list_active_insights

# Step 19.5 -- READ-ONLY surface for Active strategy insights. Nothing in this file
# writes a StrategyInsight row: those are produced only by run_reflection_cycle()
# (Step 19.3), never by a human typing into the UI. That is Step 19.6's non-goal
# enforced structurally -- no PATCH/POST/DELETE routes exist here at all.
strategy_insights_bp = Blueprint(
    "strategy_insights", __name__, url_prefix="/api/v1/strategy-insights"
)


@strategy_insights_bp.route("", methods=["GET"])
def list_insights():
    db = SessionLocal()
    try:
        product_id = request.args.get("product_id") or None
        try:
            limit = int(request.args.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        return jsonify(list_active_insights(db, product_id=product_id, limit=limit))
    finally:
        db.close()
