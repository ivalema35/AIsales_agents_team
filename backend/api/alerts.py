"""HOT-lead alerts for the dashboard (MASTER PRD §5 Step 4.4's AlertsPanel).

v1 is read-mostly per the PRD ("AI owns transitions, humans act on HOT leads"): this
endpoint just surfaces HOT-tier leads that haven't already been claimed/converted/
rejected. "Claiming" one is a human clicking a button in the dashboard, which reuses the
existing PATCH /api/v1/leads/<id>/status endpoint to move it to HOT_LEAD -- once that
happens the lead naturally drops out of this list (excluded below), so nothing here
needs its own separate "claim" endpoint.
"""
import json

from flask import Blueprint, jsonify

from database.db_config import SessionLocal
from database.models import Lead, LeadReviewInsight, LeadScore

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")

# A HOT lead already in one of these statuses isn't something a rep needs to act on:
# CONVERTED/REJECTED are terminal, HOT_LEAD means someone already claimed it.
_EXCLUDED_STATUSES = {"CONVERTED", "REJECTED", "HOT_LEAD"}


@alerts_bp.route("", methods=["GET"])
def list_alerts():
    db = SessionLocal()
    try:
        rows = (
            db.query(Lead, LeadScore)
            .join(LeadScore, LeadScore.lead_id == Lead.id)
            .filter(LeadScore.tier == "HOT", ~Lead.status.in_(_EXCLUDED_STATUSES))
            .order_by(LeadScore.score.desc())
            .limit(100)
            .all()
        )

        lead_ids = [lead.id for lead, _ in rows]
        insights = {
            i.lead_id: i for i in
            db.query(LeadReviewInsight).filter(LeadReviewInsight.lead_id.in_(lead_ids)).all()
        } if lead_ids else {}

        result = []
        for lead, score in rows:
            insight = insights.get(lead.id)
            result.append({
                "lead_id": lead.id,
                "product_id": lead.product_id,
                "company_name": lead.company_name,
                "status": lead.status,
                "primary_email": lead.primary_email,
                "primary_phone": lead.primary_phone,
                "score": score.score,
                "confidence": score.confidence,
                "justification": score.justification,
                "pain_points": json.loads(insight.pain_points_extracted) if insight else [],
            })
        return jsonify(result)
    finally:
        db.close()
