from __future__ import annotations
from __future__ import annotations
"""CLASSIFY_INBOUND job handler (MASTER Phase 4 / Step 4.3). Registered into
jobs/worker.py (sequential poller, same as OUTREACH_EMAIL/OUTREACH_WA) -- classification
volume is comparable to outreach volume, and a human being alerted to a hot reply
promptly matters more than concurrent throughput here.
"""
import json
import logging
import uuid

from agents.inbound_agent import classify_intent, redraft_reply
from agents.quality_controller_agent import review_draft
from cognition.agent_events import log_agent_event
from cognition.decision_engine import route_action
from cognition.hard_classifiers import looks_pricing_or_legal
from config import Config
from database.models import InboundConversation, Lead, LeadReviewInsight, OutreachLog, Product
from jobs.registry import register_handler
from services.outreach.email_service import send_email, extract_resend_id
from services.outreach.suppression import add_suppression, is_suppressed
from services.outreach.whatsapp_service import send_free_form_message, extract_wamid
from services.phone_utils import normalize_phone
from services.system_settings import get_bool, AUTO_REPLY_ENABLED, ACKNOWLEDGMENT_REPLY_ENABLED

logger = logging.getLogger(__name__)

MAX_REDRAFT_ATTEMPTS = 2

# Used only when the AI can't produce a QC-approved reply after MAX_REDRAFT_ATTEMPTS --
# fixed, never LLM-generated, so it is safe by construction (no hallucination risk) and
# guarantees a real lead is NEVER met with total silence (tracker.md Step 4.3: "reply
# karna jaruri he").
FALLBACK_REPLY = ("Thanks for your message -- we've received it and someone from our "
                   "team will personally follow up with you shortly.")


def _send_reply_message(db, conv, lead, subject, body, event_type):
    """Channel-dispatching send + suppression check + OutreachLog, shared by both the
    escalation reply and the low-risk-OBJECTION auto-reply below -- WhatsApp used to be
    email-only here because send_free_form_message() didn't exist yet; it does now."""
    if conv.channel == "EMAIL":
        if not lead.primary_email or is_suppressed(db, "EMAIL", lead.primary_email):
            return False
        unsubscribe_url = f"{Config.PUBLIC_BASE_URL}/unsubscribe/{lead.id}"
        send_response = send_email(lead.primary_email, subject, body, unsubscribe_url)
        db.add(OutreachLog(
            id=str(uuid.uuid4()), lead_id=lead.id, channel="EMAIL",
            message_subject=subject, message_body=body, status="SENT",
            provider_message_id=extract_resend_id(send_response),
        ))
    else:
        # Country-aware (tracker.md 2026-08-17 -- see outreach_wa_handler.py for the real
        # bug this fixes): parse against the lead's own product's target_country, not a
        # hardcoded India assumption.
        product = db.get(Product, lead.product_id)
        raw_phone = lead.whatsapp_number or lead.primary_phone
        to_phone = normalize_phone(raw_phone, country_hint=product.target_country) if raw_phone else None
        if not to_phone or is_suppressed(db, "WHATSAPP", to_phone):
            return False
        send_response = send_free_form_message(to_phone, body)
        db.add(OutreachLog(
            id=str(uuid.uuid4()), lead_id=lead.id, channel="WHATSAPP",
            message_subject=subject, message_body=body, status="SENT",
            provider_message_id=extract_wamid(send_response),
        ))

    db.commit()
    log_agent_event(db, "OUTREACH", lead.id, event_type, 1.0, "LOW", "EXECUTE",
                    payload={"channel": conv.channel})
    logger.info("CLASSIFY_INBOUND %s -> %s sent via %s", lead.company_name, event_type, conv.channel)
    return True


def _send_escalation_reply(db, conv, lead, message, result, pain_points, product_brief):
    """A real, grounded reply for a message that just escalated to a human -- adaptively
    answers what the lead asked using ONLY their verified pain points and the product
    brief, closes with a promise the team will follow up, and never leaves the lead in
    silence. If QC rejects the draft, asks the AI to fix the SPECIFIC issues raised
    (up to MAX_REDRAFT_ATTEMPTS times) before falling back to a fixed, guaranteed-safe
    message -- a reply must always go out, it just must never be the QC already caught."""
    if not get_bool(db, ACKNOWLEDGMENT_REPLY_ENABLED, default=False):
        return

    subject = "Re: your message"
    draft_body = result.get("suggested_reply", "").strip() or FALLBACK_REPLY
    qc_result = review_draft(db, lead.id, {"subject": subject, "body": draft_body}, pain_points,
                             product_brief=product_brief)

    attempts = 0
    while not qc_result["approved"] and attempts < MAX_REDRAFT_ATTEMPTS:
        attempts += 1
        redrafted = redraft_reply(db, lead.id, message, draft_body, qc_result["rejection_reasons"],
                                  qc_result["suggested_corrections"], pain_points, product_brief)
        if not redrafted:
            break
        draft_body = redrafted
        qc_result = review_draft(db, lead.id, {"subject": subject, "body": draft_body}, pain_points,
                                 product_brief=product_brief)

    if not qc_result["approved"]:
        logger.info("CLASSIFY_INBOUND %s -> AI reply never got QC approval after %d attempt(s), "
                   "sending the fixed fallback instead", lead.company_name, attempts)
        draft_body = FALLBACK_REPLY

    _send_reply_message(db, conv, lead, subject, draft_body, "ESCALATION_REPLY")


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
        _send_escalation_reply(db, conv, lead, conv.message_content, result, pain_points, product_brief)
        return conv.id

    # Only a low-risk, high-confidence OBJECTION reaches here. Even then, nothing gets
    # sent unless the dashboard's auto-reply switch is explicitly on (default off, same
    # posture as AUTONOMOUS_OUTREACH_ENABLED) -- see tracker.md Step 4.3.
    if not get_bool(db, AUTO_REPLY_ENABLED, default=False):
        logger.info("CLASSIFY_INBOUND %s -> low-risk (%s) but auto-reply is off, left for manual review",
                   lead.company_name, result["intent"])
        return conv.id

    # QC's veto is absolute over ANY outbound content, not just fresh outreach drafts --
    # the AI's suggested_reply gets the same review a brand-new draft would. Unlike the
    # escalation path above, a low-risk OBJECTION isn't urgent enough to warrant a forced
    # fallback send on rejection -- QC saying no here just leaves it for manual review.
    subject = f"Re: {product.title}"
    qc_result = review_draft(db, lead.id, {"subject": subject, "body": result["suggested_reply"]},
                             pain_points, product_brief=product_brief)
    if not qc_result["approved"]:
        logger.info("CLASSIFY_INBOUND %s -> QC rejected the auto-reply, left for manual review", lead.company_name)
        return conv.id

    _send_reply_message(db, conv, lead, subject, result["suggested_reply"], "AUTO_REPLY")
    return conv.id
