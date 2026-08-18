"""HOT-lead alerts for the dashboard (MASTER PRD §5 Step 4.4's AlertsPanel).

Two genuinely different situations, kept as two sections rather than one merged list:

1. `needs_response` -- a lead just replied showing real interest (INTERESTED/
   DEMO_REQUESTED) and Step 4.3's inbound classifier auto-escalated it to HOT_LEAD.
   Nobody has acted on it yet. This is the most time-sensitive thing on the whole
   dashboard -- a real prospect is waiting on a human reply -- so it's its own,
   top-billed section.
2. `ready_to_claim` -- a lead scored HOT by the scoring agent but hasn't been picked up
   by anyone yet (the original v1 alert). "Claiming" one just moves it to HOT_LEAD via
   the existing PATCH /api/v1/leads/<id>/status endpoint.

Bug this fixes: the original single-list version excluded ANY lead already in HOT_LEAD
status, on the assumption that HOT_LEAD == "already claimed by a human." That assumption
predates Step 4.3's auto-escalation -- a lead that auto-escalates because it replied
"yes, tell me more" has NOT been seen by anyone, and was silently disappearing from this
exact list, the one place meant to surface it (found live, user-reported).

A `needs_response` lead stops showing here the moment a human moves it out of HOT_LEAD
(e.g. the Lead Detail page's "Mark as Contacted" action, which sets it to ENGAGED) --
no separate "resolved" flag needed.
"""
import json

from flask import Blueprint, jsonify

from database.db_config import SessionLocal
from database.models import InboundConversation, Lead, LeadReviewInsight, LeadScore

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")

# A HOT-tier lead already in one of these statuses isn't something a rep needs to claim:
# CONVERTED/REJECTED are terminal, HOT_LEAD means it's already escalated one way or
# another (surfaced instead under needs_response if that's specifically why).
_EXCLUDED_FROM_CLAIM = {"CONVERTED", "REJECTED", "HOT_LEAD"}

_INTEREST_INTENTS = ("INTERESTED", "DEMO_REQUESTED")


def _needs_response(db):
    hot_leads = db.query(Lead).filter(Lead.status == "HOT_LEAD").all()
    if not hot_leads:
        return []
    lead_ids = [l.id for l in hot_leads]

    # Small result set in practice (HOT_LEAD is a rare, actively-worked status, not a
    # bulk one like SCORED) -- fetching every conversation and reducing to "latest per
    # lead" in Python is simpler and just as correct as a windowed SQL query here.
    convs = (
        db.query(InboundConversation)
        .filter(InboundConversation.lead_id.in_(lead_ids))
        .order_by(InboundConversation.created_at.asc())
        .all()
    )
    latest_by_lead = {}
    for c in convs:
        latest_by_lead[c.lead_id] = c  # last write wins -- ascending order, so it's the latest

    insights = {
        i.lead_id: i for i in
        db.query(LeadReviewInsight).filter(LeadReviewInsight.lead_id.in_(lead_ids)).all()
    }

    result = []
    for lead in hot_leads:
        conv = latest_by_lead.get(lead.id)
        if not conv or conv.intent_detected not in _INTEREST_INTENTS:
            continue
        insight = insights.get(lead.id)
        result.append({
            "lead_id": lead.id,
            "product_id": lead.product_id,
            "company_name": lead.company_name,
            "primary_email": lead.primary_email,
            "primary_phone": lead.primary_phone,
            "channel": conv.channel,
            "intent": conv.intent_detected,
            "message": conv.message_content,
            "replied_at": str(conv.created_at),
            "pain_points": json.loads(insight.pain_points_extracted) if insight else [],
        })
    result.sort(key=lambda r: r["replied_at"], reverse=True)
    return result


def _ready_to_claim(db):
    rows = (
        db.query(Lead, LeadScore)
        .join(LeadScore, LeadScore.lead_id == Lead.id)
        .filter(LeadScore.tier == "HOT", ~Lead.status.in_(_EXCLUDED_FROM_CLAIM))
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
    return result


@alerts_bp.route("", methods=["GET"])
def list_alerts():
    db = SessionLocal()
    try:
        return jsonify({
            "needs_response": _needs_response(db),
            "ready_to_claim": _ready_to_claim(db),
        })
    finally:
        db.close()
