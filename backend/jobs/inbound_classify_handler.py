"""CLASSIFY_INBOUND job handler (MASTER Phase 4 / Step 4.3). Registered into
jobs/worker.py (sequential poller, same as OUTREACH_EMAIL/OUTREACH_WA) -- classification
volume is comparable to outreach volume, and a human being alerted to a hot reply
promptly matters more than concurrent throughput here.
"""
import json
import logging
import uuid

from agents.inbound_agent import classify_intent
from agents.quality_controller_agent import review_draft
from cognition.agent_events import log_agent_event
from cognition.decision_engine import route_action
from cognition.hard_classifiers import looks_pricing_or_legal
from config import Config
from database.models import InboundConversation, Lead, LeadReviewInsight, OutreachLog, Product
from jobs.registry import register_handler
from services.outreach.email_service import send_email
from services.outreach.suppression import add_suppression, is_suppressed
from services.system_settings import get_bool, AUTO_REPLY_ENABLED

logger = logging.getLogger(__name__)


@register_handler("CLASSIFY_INBOUND")
def handle_classify_inbound(db, payload):
    conv = db.get(InboundConversation, payload["inbound_conversation_id"])
    if not conv:
        raise ValueError(f"inbound_conversation {payload['inbound_conversation_id']} not found")

    lead = db.get(Lead, conv.lead_id)
    product = db.get(Product, lead.product_id)
    product_brief = {
        "title": product.title,
        "description": product.description,
        "value_proposition": product.value_proposition,
    }

    history = [
        {"sender": c.sender_type, "content": c.message_content}
        for c in db.query(InboundConversation)
        .filter(InboundConversation.lead_id == lead.id, InboundConversation.id != conv.id)
        .order_by(InboundConversation.created_at.desc()).limit(5).all()
    ]

    # Same verified-evidence source outreach_handler.py drafts from -- without this, the
    # AI has nothing lead-specific to ground suggested_reply in and will infer generic
    # framing from the product brief alone (see tracker.md Step 4.3 GameZone Visnagar bug).
    insight = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.lead_id == lead.id)
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []

    result = classify_intent(db, lead.id, conv.message_content, history, product_brief, pain_points)

    # The AI can catch a subtler opt-out than Step 4.2's keyword match did -- if it says
    # so, suppress for real, same as the deterministic path (still the 100% rule).
    if result["suppress_immediately"]:
        identifier = lead.primary_email if conv.channel == "EMAIL" else (lead.whatsapp_number or lead.primary_phone)
        if identifier:
            add_suppression(db, conv.channel, identifier, "STOP")
        result["intent"] = "STOP"

    conv.intent_detected = result["intent"]
    conv.confidence = result["confidence"]
    conv.ai_suggested_response = result["suggested_reply"]
    db.commit()

    if result["intent"] in ("STOP", "AUTO_REPLY"):
        logger.info("CLASSIFY_INBOUND %s -> %s, nothing further to do", lead.company_name, result["intent"])
        return conv.id

    is_high_risk = looks_pricing_or_legal(conv.message_content)
    route = route_action("INBOUND_REPLY", result["confidence"], is_high_risk=is_high_risk)
    # INTERESTED/DEMO_REQUESTED always escalate regardless of confidence -- the highest-
    # value moment in the whole pipeline never gets left to an AI auto-reply.
    force_escalate = (
        result["intent"] in ("INTERESTED", "DEMO_REQUESTED")
        or result["escalate_to_human"]
        or route == "HUMAN_ESCALATION"
    )

    if force_escalate:
        lead.status = "HOT_LEAD"
        db.commit()
        log_agent_event(db, "INBOUND", lead.id, "ESCALATE", result["confidence"], "HIGH", "HUMAN_ESCALATION")
        logger.info("CLASSIFY_INBOUND %s -> escalated to human (intent=%s, confidence=%.2f)",
                   lead.company_name, result["intent"], result["confidence"])
        return conv.id

    # Only a low-risk, high-confidence OBJECTION reaches here. Even then, nothing gets
    # sent unless the dashboard's auto-reply switch is explicitly on (default off, same
    # posture as AUTONOMOUS_OUTREACH_ENABLED) -- see tracker.md Step 4.3.
    if not get_bool(db, AUTO_REPLY_ENABLED, default=False):
        logger.info("CLASSIFY_INBOUND %s -> low-risk (%s) but auto-reply is off, left for manual review",
                   lead.company_name, result["intent"])
        return conv.id

    # QC's veto is absolute over ANY outbound content, not just fresh outreach drafts --
    # the AI's suggested_reply gets the same review a brand-new draft would.
    draft = {"subject": f"Re: {product.title}", "body": result["suggested_reply"]}
    qc_result = review_draft(db, lead.id, draft, pain_points, product_brief=product_brief)
    if not qc_result["approved"]:
        logger.info("CLASSIFY_INBOUND %s -> QC rejected the auto-reply, left for manual review", lead.company_name)
        return conv.id

    # Email only for now -- a WhatsApp free-form auto-reply needs its own send function
    # (whatsapp_service.py currently only sends templates) and is deliberately deferred,
    # not built in this step.
    if conv.channel == "EMAIL":
        if is_suppressed(db, "EMAIL", lead.primary_email):
            return conv.id
        unsubscribe_url = f"{Config.PUBLIC_BASE_URL}/unsubscribe/{lead.id}"
        send_email(lead.primary_email, draft["subject"], draft["body"], unsubscribe_url)
        db.add(OutreachLog(
            id=str(uuid.uuid4()), lead_id=lead.id, channel="EMAIL",
            message_subject=draft["subject"], message_body=draft["body"], status="SENT",
        ))
        db.commit()
        log_agent_event(db, "OUTREACH", lead.id, "AUTO_REPLY_EMAIL", qc_result["confidence_score"],
                        "MEDIUM", "EXECUTE")
        logger.info("CLASSIFY_INBOUND %s -> auto-replied via email", lead.company_name)

    return conv.id
