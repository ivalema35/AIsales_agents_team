from __future__ import annotations

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Lead, SocialMessageQueue
from services.outreach.social_queue_service import request_social_draft, mark_sent, dismiss

social_queue_bp = Blueprint("social_queue", __name__, url_prefix="/api/v1/social-queue")


def _serialize(row, lead_name=None):
    return {
        "id": row.id,
        "lead_id": row.lead_id,
        "lead_company_name": lead_name,
        "platform": row.platform,
        "message_text": row.message_text,
        "reasoning": row.reasoning,
        "status": row.status,
        "sent_at": str(row.sent_at) if row.sent_at else None,
        "created_at": str(row.created_at),
    }


@social_queue_bp.route("", methods=["GET"])
def list_queue():
    """Optional ?status=QUEUED and/or ?lead_id=... filters -- the dashboard's default
    queue view only wants QUEUED (what a human still needs to act on), but SENT/DISMISSED
    stay queryable for history; a lead's own detail page filters down to just that lead."""
    db = SessionLocal()
    try:
        query = db.query(SocialMessageQueue)
        status = request.args.get("status")
        if status:
            query = query.filter(SocialMessageQueue.status == status.upper())
        lead_id = request.args.get("lead_id")
        if lead_id:
            query = query.filter(SocialMessageQueue.lead_id == lead_id)
        rows = query.order_by(SocialMessageQueue.created_at.desc()).all()
        lead_ids = {row.lead_id for row in rows}
        leads = {lead.id: lead.company_name for lead in db.query(Lead).filter(Lead.id.in_(lead_ids))} if lead_ids else {}
        return jsonify([_serialize(row, leads.get(row.lead_id)) for row in rows])
    finally:
        db.close()


@social_queue_bp.route("/draft", methods=["POST"])
def draft():
    """Body: {"lead_id": "...", "platform": "LINKEDIN"|"INSTAGRAM"|"FACEBOOK"}. Drafts +
    QC-gates a message; only a QC-approved draft is ever saved and returned as "queued"."""
    data = request.get_json(silent=True) or {}
    lead_id = data.get("lead_id")
    platform = data.get("platform")
    if not lead_id or not platform:
        return jsonify({"error": ["lead_id and platform are both required"]}), 422

    db = SessionLocal()
    try:
        result = request_social_draft(db, lead_id, platform)
        if "error" in result:
            return jsonify({"error": [result["error"]]}), 422
        if "rejected" in result:
            return jsonify({"error": result["rejected"], "qc_rejected": True}), 422
        lead = db.get(Lead, lead_id)
        return jsonify(_serialize(result["queued"], lead.company_name if lead else None)), 201
    finally:
        db.close()


@social_queue_bp.route("/<queue_id>/sent", methods=["POST"])
def mark_as_sent(queue_id):
    db = SessionLocal()
    try:
        row = mark_sent(db, queue_id)
        if not row:
            return jsonify({"error": ["draft not found or not in QUEUED state"]}), 409
        lead = db.get(Lead, row.lead_id)
        return jsonify(_serialize(row, lead.company_name if lead else None))
    finally:
        db.close()


@social_queue_bp.route("/<queue_id>/dismiss", methods=["POST"])
def dismiss_draft(queue_id):
    db = SessionLocal()
    try:
        row = dismiss(db, queue_id)
        if not row:
            return jsonify({"error": ["draft not found or not in QUEUED state"]}), 409
        lead = db.get(Lead, row.lead_id)
        return jsonify(_serialize(row, lead.company_name if lead else None))
    finally:
        db.close()
