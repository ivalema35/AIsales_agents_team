from __future__ import annotations
import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Campaign, Product
from services.campaign_service import (
    compute_campaign_metrics, compute_campaign_lead_summary, get_daily_review,
    clear_campaign_watchdog_alert, revise_kickoff_draft, set_campaign_email_render_mode)

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/api/v1/campaigns")

# Phase 17 Step 17.5. PROPOSED->APPROVED only happens via Phase 18's human review action
# once that exists -- nothing in this file sets that transition automatically today.
VALID_STATUSES = {"PROPOSED", "APPROVED", "RUNNING", "COMPLETED", "PAUSED"}


def _parse_date(value, errors):
    """SQLAlchemy's DATE column only accepts a real python date object, never a raw
    string -- a real bug caught live (2026-09-01): passing "2026-09-01" straight through
    raised a 500 at commit time instead of failing cleanly. Returns None (and appends an
    error) for anything unparseable, so the caller always gets a 422, never a 500."""
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        errors.append("scheduled_date must be YYYY-MM-DD")
        return None


def _serialize(db, campaign, with_metrics=True):
    """`metrics` (Step 17.3) is ALWAYS computed live -- `metrics_summary` is returned
    alongside it only as the raw cache value, never substituted for a real computation.
    `with_metrics=False` skips the live query for list_campaigns' bulk case if it's ever
    needed for performance; real campaign volume is small enough that it isn't today."""
    data = {
        "id": campaign.id,
        "product_id": campaign.product_id,
        "name": campaign.name,
        "scheduled_date": str(campaign.scheduled_date) if campaign.scheduled_date else None,
        "target_segment": json.loads(campaign.target_segment or "{}"),
        "strategy_angle": campaign.strategy_angle,
        "email_render_mode": campaign.email_render_mode or "HTML",
        "status": campaign.status,
        "lead_count_goal": campaign.lead_count_goal,
        "metrics_summary_cache": json.loads(campaign.metrics_summary or "{}"),
        "created_at": str(campaign.created_at),
        "updated_at": str(campaign.updated_at),
    }
    if with_metrics:
        data["metrics"] = compute_campaign_metrics(db, campaign.id)
        data["lead_summary"] = compute_campaign_lead_summary(db, campaign.id)
    return data


@campaigns_bp.route("", methods=["GET"])
def list_campaigns():
    db = SessionLocal()
    try:
        query = db.query(Campaign)
        product_id = request.args.get("product_id")
        if product_id:
            query = query.filter(Campaign.product_id == product_id)
        status = request.args.get("status")
        if status:
            query = query.filter(Campaign.status == status)
        rows = query.order_by(Campaign.scheduled_date.desc(), Campaign.created_at.desc()).all()
        return jsonify([_serialize(db, r) for r in rows])
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>", methods=["GET"])
def get_campaign(campaign_id):
    db = SessionLocal()
    try:
        row = db.get(Campaign, campaign_id)
        if not row:
            return jsonify({"error": "campaign not found"}), 404
        return jsonify(_serialize(db, row))
    finally:
        db.close()


@campaigns_bp.route("", methods=["POST"])
def create_campaign():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if not data.get("product_id"):
        errors.append("product_id is required")
    if not data.get("name"):
        errors.append("name is required")

    # target_segment is deliberately free-form (2026-09-01 revision, see tracker.md /
    # MASTER_DEVELOPMENT_PRD.md §5C.0) -- only checked to be a real JSON object, never
    # validated against the product's own target_regions/target_business_categories/
    # target_person_roles. A campaign may genuinely target outside a product's standing
    # configuration; nothing here ever writes back to that product's own targeting fields.
    target_segment = data.get("target_segment")
    if target_segment is not None and not isinstance(target_segment, dict):
        errors.append("target_segment must be a JSON object")

    status = data.get("status", "PROPOSED")
    if status not in VALID_STATUSES:
        errors.append(f"status must be one of {sorted(VALID_STATUSES)}")

    # lead_count_goal (2026-09-02, Step 18.1): optional at creation -- a human who already
    # knows their target can set it directly, same as target_segment; left blank, the daily
    # strategist proposes one later (generate_campaign_todo), applied only on Approve.
    lead_count_goal = data.get("lead_count_goal")
    if lead_count_goal is not None and (not isinstance(lead_count_goal, (int, float))
                                         or isinstance(lead_count_goal, bool) or lead_count_goal <= 0):
        errors.append("lead_count_goal must be a positive number")

    scheduled_date = _parse_date(data.get("scheduled_date"), errors)

    db = SessionLocal()
    try:
        if data.get("product_id") and not db.get(Product, data["product_id"]):
            errors.append(f"product {data['product_id']!r} not found")
        if errors:
            return jsonify({"error": errors}), 422

        campaign = Campaign(
            product_id=data["product_id"],
            name=data["name"],
            scheduled_date=scheduled_date,
            target_segment=json.dumps(target_segment if target_segment is not None else {}),
            strategy_angle=data.get("strategy_angle"),
            lead_count_goal=int(lead_count_goal) if lead_count_goal is not None else None,
            status=status,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return jsonify(_serialize(db, campaign)), 201
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>", methods=["PUT"])
def update_campaign(campaign_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    target_segment = data.get("target_segment")
    if "target_segment" in data and not isinstance(target_segment, dict):
        errors.append("target_segment must be a JSON object")
    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append(f"status must be one of {sorted(VALID_STATUSES)}")
    scheduled_date = _parse_date(data.get("scheduled_date"), errors) if "scheduled_date" in data else None
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return jsonify({"error": "campaign not found"}), 404

        if "name" in data:
            if not data["name"]:
                return jsonify({"error": ["name cannot be empty"]}), 422
            campaign.name = data["name"]
        if "scheduled_date" in data:
            campaign.scheduled_date = scheduled_date
        if "target_segment" in data:
            campaign.target_segment = json.dumps(target_segment)
        if "strategy_angle" in data:
            campaign.strategy_angle = data["strategy_angle"]
        if "status" in data:
            campaign.status = data["status"]

        db.commit()
        db.refresh(campaign)
        return jsonify(_serialize(db, campaign))
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>/daily-review", methods=["GET"])
def daily_review(campaign_id):
    """Phase 18 Step 18.2 -- this campaign's real pending to-do items (Phase 21) plus a real
    sample draft for the 2-minute morning review. Read-only; approving/dismissing an
    individual item is `api/todos.py`'s job now, not this route's."""
    db = SessionLocal()
    try:
        if not db.get(Campaign, campaign_id):
            return jsonify({"error": "campaign not found"}), 404
        return jsonify(get_daily_review(db, campaign_id))
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>/email-render-mode", methods=["POST"])
def set_email_render_mode(campaign_id):
    """Daily Review chips: set HTML|TEXT render mode, clear kickoff cache. Never sends."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    db = SessionLocal()
    try:
        if not db.get(Campaign, campaign_id):
            return jsonify({"error": "campaign not found"}), 404
        try:
            return jsonify(set_campaign_email_render_mode(db, campaign_id, mode))
        except ValueError as exc:
            return jsonify({"error": [str(exc)]}), 422
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>/kickoff-draft/revise", methods=["POST"])
def revise_kickoff(campaign_id):
    """Kickoff template preview revision (Step 18.1b / Step 16.5 reuse) -- for campaigns
    with no real leads yet. Same conversational feedback as lead revise-draft; persists
    on campaigns.kickoff_draft. Never sends anything."""
    data = request.get_json(silent=True) or {}
    instruction = str(data.get("instruction") or "").strip()
    if not instruction:
        return jsonify({"error": ["instruction is required"]}), 422
    current_draft = data.get("current_draft")
    db = SessionLocal()
    try:
        if not db.get(Campaign, campaign_id):
            return jsonify({"error": "campaign not found"}), 404
        try:
            result = revise_kickoff_draft(db, campaign_id, instruction, current_draft)
        except RuntimeError as exc:
            return jsonify({"error": [str(exc)]}), 503
        return jsonify(result)
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>/watchdog/clear", methods=["POST"])
def clear_watchdog(campaign_id):
    """Phase 20 Step 20.3 -- the ONLY way a real Execution Watchdog alert is ever cleared,
    a real human decision (see services/campaign_service.py's clear_campaign_watchdog_alert
    docstring). Purely a pause/resume-eligibility toggle -- never touches
    AUTONOMOUS_OUTREACH_ENABLED, never claims or sends anything itself."""
    db = SessionLocal()
    try:
        if not db.get(Campaign, campaign_id):
            return jsonify({"error": "campaign not found"}), 404
        clear_campaign_watchdog_alert(db, campaign_id)
        return jsonify({"campaign_id": campaign_id, "watchdog_alert": None})
    finally:
        db.close()


@campaigns_bp.route("/<campaign_id>", methods=["DELETE"])
def delete_campaign(campaign_id):
    """Deleting a campaign never deletes its leads -- leads.campaign_id has no CASCADE
    (Step 17.1); this only removes the grouping row itself."""
    db = SessionLocal()
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return jsonify({"error": "campaign not found"}), 404
        db.delete(campaign)
        db.commit()
        return "", 204
    finally:
        db.close()
