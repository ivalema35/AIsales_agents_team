import json

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Lead, LeadReviewInsight, LeadScore, OutreachLog, Product
from services.lead_service import claim_lead_for_outreach
from jobs.outreach_handler import handle_outreach_email
from jobs.outreach_wa_handler import handle_outreach_wa

leads_bp = Blueprint("leads", __name__, url_prefix="/api/v1/leads")

VALID_STATUSES = {
    "DISCOVERED", "ENRICHED", "REVIEWED", "SCORED", "OUTREACHING",
    "OUTREACHED", "ENGAGED", "HOT_LEAD", "CONVERTED", "REJECTED",
}


def _serialize(lead, score=None):
    return {
        "id": lead.id,
        "product_id": lead.product_id,
        "company_name": lead.company_name,
        "website_url": lead.website_url,
        "primary_email": lead.primary_email,
        "primary_phone": lead.primary_phone,
        "whatsapp_number": lead.whatsapp_number,
        "contact_person_name": lead.contact_person_name,
        "contact_person_role": lead.contact_person_role,
        "status": lead.status,
        "source": lead.source,
        "region_location": lead.region_location,
        "sales_route": lead.sales_route,
        "created_at": str(lead.created_at),
        "updated_at": str(lead.updated_at),
        "score": None if score is None else {
            "tier": score.tier,
            "score": score.score,
            "confidence": score.confidence,
            "justification": score.justification,
        },
    }


@leads_bp.route("", methods=["GET"])
def list_leads():
    db = SessionLocal()
    try:
        query = db.query(Lead)
        product_id = request.args.get("product_id")
        if product_id:
            query = query.filter(Lead.product_id == product_id)
        status = request.args.get("status")
        if status:
            if status not in VALID_STATUSES:
                return jsonify({"error": [f"status must be one of {sorted(VALID_STATUSES)}"]}), 422
            query = query.filter(Lead.status == status)
        leads = query.order_by(Lead.created_at.desc()).limit(500).all()

        scores = {
            s.lead_id: s for s in
            db.query(LeadScore).filter(LeadScore.lead_id.in_([l.id for l in leads])).all()
        } if leads else {}
        return jsonify([_serialize(lead, scores.get(lead.id)) for lead in leads])
    finally:
        db.close()


@leads_bp.route("/<lead_id>", methods=["GET"])
def get_lead(lead_id):
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        score = db.query(LeadScore).filter(LeadScore.lead_id == lead_id).first()
        insight = (
            db.query(LeadReviewInsight)
            .filter(LeadReviewInsight.lead_id == lead_id)
            .order_by(LeadReviewInsight.analyzed_at.desc())
            .first()
        )
        body = _serialize(lead, score)
        body["pain_points"] = json.loads(insight.pain_points_extracted) if insight else []
        return jsonify(body)
    finally:
        db.close()


@leads_bp.route("", methods=["POST"])
def create_lead():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if not data.get("product_id"):
        errors.append("product_id is required")
    if not data.get("company_name"):
        errors.append("company_name is required")
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        product = db.get(Product, data["product_id"])
        if not product:
            return jsonify({"error": [f"product_id '{data['product_id']}' does not exist"]}), 422

        lead = Lead(
            product_id=data["product_id"],
            company_name=data["company_name"],
            website_url=data.get("website_url"),
            primary_email=data.get("primary_email"),
            primary_phone=data.get("primary_phone"),
            whatsapp_number=data.get("whatsapp_number"),
            contact_person_name=data.get("contact_person_name"),
            contact_person_role=data.get("contact_person_role"),
            source=data.get("source"),
            region_location=data.get("region_location"),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return jsonify(_serialize(lead)), 201
    finally:
        db.close()


@leads_bp.route("/<lead_id>/outreach", methods=["POST"])
def trigger_outreach(lead_id):
    """Manual, human-initiated outreach trigger (dashboard "Send Outreach Now" button) --
    runs the real draft->QC->send flow synchronously so the click gets a real result back
    immediately, instead of enqueueing and hoping the background worker picks it up in
    time for a live demo. This is a deliberate single-lead human action, not the
    scheduler's autonomous tick -- it is NOT gated by system_settings.autonomous_outreach_
    enabled (that switch only governs the scheduler's own automatic claiming; see
    tracker.md A.3 / services/system_settings.py).
    """
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404

        score = db.query(LeadScore).filter(LeadScore.lead_id == lead_id).first()
        if not score:
            return jsonify({"error": ["lead has not been scored yet -- nothing to act on"]}), 422

        # OUTREACHING means a send is ACTIVELY in flight right now (claim_lead_for_outreach
        # sets this immediately, before the slow LLM-draft+QC+send work even starts) --
        # forcing it back to SCORED here would let a second concurrent click bypass that
        # atomic claim's own protection and fire a real duplicate send. This isn't
        # hypothetical: the dashboard polls every 15s and a lead mid-send visibly moves
        # Kanban columns, which remounts its card with fresh (unblocked) button state --
        # so a second click during that window looks perfectly safe to a real user and
        # produced 4 duplicate real email/WhatsApp sends before this guard existed.
        if lead.status == "OUTREACHING":
            return jsonify({
                "error": ["outreach is already in progress for this lead -- wait for it to finish"]
            }), 409

        # A deliberate manual re-trigger (e.g. for a demo) should still work regardless of
        # whatever TERMINAL state a previous run left the lead in -- reset to SCORED so
        # claim_lead_for_outreach's atomic claim has something to claim.
        if lead.status != "SCORED":
            lead.status = "SCORED"
            db.commit()

        channels = claim_lead_for_outreach(db, lead_id)
        if not channels:
            return jsonify({
                "error": ["lead is not outreach-eligible (tier must be HOT/WARM and "
                          "confidence high enough, and it needs at least one contact channel)"]
            }), 422

        # Snapshot existing log ids per channel BEFORE processing -- this may not be the
        # lead's first outreach attempt (e.g. a repeated demo), so "a log exists" isn't
        # enough to tell a fresh send from a stale one; only a NEW id counts.
        existing_ids = {
            channel: {row.id for row in db.query(OutreachLog.id).filter(
                OutreachLog.lead_id == lead_id, OutreachLog.channel == channel)}
            for channel in channels
        }

        handlers = {"EMAIL": handle_outreach_email, "WHATSAPP": handle_outreach_wa}
        for channel in channels:
            handlers[channel](db, {"lead_id": lead_id})

        results = {}
        for channel in channels:
            log = (
                db.query(OutreachLog)
                .filter(OutreachLog.lead_id == lead_id, OutreachLog.channel == channel,
                        ~OutreachLog.id.in_(existing_ids[channel]))
                .order_by(OutreachLog.sent_at.desc())
                .first()
            )
            results[channel] = (
                {"status": log.status, "subject": log.message_subject}
                if log else {"status": "ESCALATED", "reason": "QC/validation rejected the draft -- needs a human"}
            )

        db.refresh(lead)
        return jsonify({"lead_id": lead_id, "lead_status": lead.status, "results": results})
    finally:
        db.close()


@leads_bp.route("/<lead_id>/status", methods=["PATCH"])
def patch_lead_status(lead_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("status"):
        return jsonify({"error": ["status is required"]}), 422
    if data["status"] not in VALID_STATUSES:
        return jsonify({"error": [f"status must be one of {sorted(VALID_STATUSES)}"]}), 422

    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        lead.status = data["status"]
        db.commit()
        db.refresh(lead)
        return jsonify(_serialize(lead))
    finally:
        db.close()
