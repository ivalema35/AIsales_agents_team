"""OUTREACH_WA job handler (MASTER Phase 3 / Step 3.4).

Registered into jobs/worker.py for the same pacing reason as OUTREACH_EMAIL
(jobs/outreach_handler.py): sequential, controlled-rate sending, not async_runner's
concurrent fan-out.

Unlike email, WhatsApp first-contact is TEMPLATE-based, not free-form-drafted: no
Outreach Agent LLM call here, no QC-veto LLM call either -- Meta already reviewed and
approved the template's actual wording, so there's no creative content left to review.
`validate_variables()` is the deterministic stand-in for QC: sanity-checking the filled
values, not judging prose.
"""
import json
import logging
import uuid

from cognition.agent_events import log_agent_event
from database.models import Lead, LeadReviewInsight, OutreachLog
from jobs.worker import register_handler
from services.data_acquisition.website_scraper import normalize_mobile
from services.outreach.suppression import is_suppressed
from services.outreach.whatsapp_service import send_template_message
from services.outreach.whatsapp_templates import (
    TEMPLATE_LIBRARY,
    select_template,
    fill_variables,
    validate_variables,
)

logger = logging.getLogger(__name__)


@register_handler("OUTREACH_WA")
def handle_outreach_wa(db, payload):
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    raw_phone = lead.whatsapp_number or lead.primary_phone
    phone = normalize_mobile(raw_phone) if raw_phone else None
    if not phone:
        logger.info("OUTREACH_WA %s -> no usable phone on file, skipping", lead.company_name)
        return lead.id

    if is_suppressed(db, "WHATSAPP", phone):
        logger.info("OUTREACH_WA %s -> suppressed, aborting before send", lead.company_name)
        lead.status = "REJECTED"
        db.commit()
        return lead.id

    insight = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.lead_id == lead.id)
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []

    lead_profile = {
        "company_name": lead.company_name,
        "contact_person_name": lead.contact_person_name,
    }

    template_key = select_template(pain_points)
    spec = TEMPLATE_LIBRARY[template_key]
    values = fill_variables(template_key, lead_profile, pain_points)

    if not validate_variables(values):
        logger.info("OUTREACH_WA %s -> filled variables failed validation, escalating", lead.company_name)
        log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_WHATSAPP", 0.0, "MEDIUM", "HUMAN_ESCALATION")
        return lead.id

    # Re-check suppression immediately before the network call -- the 100% rule applies
    # right up to the send, not just once earlier in this function.
    if is_suppressed(db, "WHATSAPP", phone):
        logger.info("OUTREACH_WA %s -> suppressed between selection and send, aborting", lead.company_name)
        lead.status = "REJECTED"
        db.commit()
        return lead.id

    # Meta's international-format convention: country code + number, no leading '+'.
    # normalize_mobile() always returns a clean 10-digit Indian mobile, so this is safe.
    to_phone = f"91{phone}"
    send_template_message(to_phone, spec["name"], spec["language"], values)

    db.add(OutreachLog(
        id=str(uuid.uuid4()),
        lead_id=lead.id,
        channel="WHATSAPP",
        message_subject=spec["name"],
        message_body=json.dumps({"template": spec["name"], "variables": values}),
        status="SENT",
    ))
    lead.status = "OUTREACHED"
    db.commit()

    log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_WHATSAPP", 1.0, "MEDIUM", "EXECUTE",
                    payload={"template": spec["name"]})
    logger.info("OUTREACH_WA %s -> sent template '%s' to %s", lead.company_name, spec["name"], to_phone)
    return lead.id
