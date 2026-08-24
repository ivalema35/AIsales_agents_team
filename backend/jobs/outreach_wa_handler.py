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
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime

from cognition.agent_events import log_agent_event
from database.models import Lead, LeadReviewInsight, OutreachLog, Product
from jobs.registry import register_handler
from services.outreach.suppression import is_suppressed
from services.phone_utils import normalize_phone
from services.outreach.whatsapp_service import send_template_message, extract_wamid
from services.outreach.whatsapp_templates import (
    TEMPLATE_LIBRARY,
    select_template,
    fill_variables,
    fill_variables_for_labels,
    validate_variables,
)
from services.outreach.whatsapp_template_service import get_approved_followup_template
from services.sequence_service import create_sequence_for_send, touch_number_to_followup_level

logger = logging.getLogger(__name__)


@register_handler("OUTREACH_WA")
def handle_outreach_wa(db, payload):
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    # Country-aware: normalize_mobile() (still used elsewhere for India-only enrichment
    # checks) assumed every lead was Indian, which real Canadian leads' numbers only
    # avoided by accident (tracker.md, 2026-08-17 -- a Canadian toll-free number matched
    # the old 10-digit-starting-6-9 heuristic and would have gotten "91" prepended,
    # sending to a fabricated, unrelated number). Product.target_country tells us which
    # region this specific lead's number should be parsed against.
    product = db.get(Product, lead.product_id)
    raw_phone = lead.whatsapp_number or lead.primary_phone
    to_phone = normalize_phone(raw_phone, country_hint=product.target_country) if raw_phone else None
    if not to_phone:
        logger.info("OUTREACH_WA %s -> no usable phone on file, skipping", lead.company_name)
        return lead.id

    if is_suppressed(db, "WHATSAPP", to_phone):
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

    # Phase 13 Step 13.1/13.2 -- same touch-number -> level derivation as jobs/outreach_
    # handler.py's EMAIL path (level 1 = touch 2, level 2 = touch 3, level 3 = touch 4+).
    followup_level = (
        touch_number_to_followup_level(payload.get("touch_number", 2))
        if payload.get("sequence_id") else None
    )

    if followup_level:
        # Phase 13 Step 13.2 -- STRICT per-level matching, no fallback. A missing
        # approved template for THIS level means this touch sends nothing on WhatsApp
        # (real behavior change from before: it used to resend touch 1's own template
        # verbatim, which read as the wrong conversation entirely -- sending the wrong
        # level's real, approved text is worse than sending nothing, MASTER §5B).
        followup_template = get_approved_followup_template(db, followup_level, product_id=lead.product_id)
        if not followup_template:
            logger.info("OUTREACH_WA %s -> no approved Level %d template, skipping WhatsApp for this touch",
                       lead.company_name, followup_level)
            log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_WHATSAPP", 0.0, "LOW", "SKIPPED_NO_TEMPLATE",
                            payload={"followup_level": followup_level})
            return lead.id
        spec = {"name": followup_template.name, "language": followup_template.language}
        variable_labels = json.loads(followup_template.variable_labels or "[]")
        values = fill_variables_for_labels(variable_labels, lead_profile, pain_points)
    else:
        template_key = select_template(pain_points)
        spec = TEMPLATE_LIBRARY[template_key]
        values = fill_variables(template_key, lead_profile, pain_points)

    if not validate_variables(values):
        logger.info("OUTREACH_WA %s -> filled variables failed validation, escalating", lead.company_name)
        log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_WHATSAPP", 0.0, "MEDIUM", "HUMAN_ESCALATION")
        return lead.id

    # Re-check suppression immediately before the network call -- the 100% rule applies
    # right up to the send, not just once earlier in this function.
    if is_suppressed(db, "WHATSAPP", to_phone):
        logger.info("OUTREACH_WA %s -> suppressed between selection and send, aborting", lead.company_name)
        lead.status = "REJECTED"
        db.commit()
        return lead.id

    # to_phone is already Meta's international-format convention (country code + number,
    # no leading '+') via normalize_phone() -- no manual prefixing needed.
    send_response = send_template_message(to_phone, spec["name"], spec["language"], values)

    db.add(OutreachLog(
        id=str(uuid.uuid4()),
        lead_id=lead.id,
        channel="WHATSAPP",
        message_subject=spec["name"],
        message_body=json.dumps({"template": spec["name"], "variables": values}),
        status="SENT",
        provider_message_id=extract_wamid(send_response),
        # Phase 9 Step 9.1 (tracker.md A.8) -- the real Meta template name, in its own
        # queryable column instead of only inside the JSON message_body blob, so Step
        # 9.2 can roll up real reply rates per template without parsing JSON per row.
        variant_id=spec["name"],
    ))
    lead.status = "OUTREACHED"
    db.commit()

    # Phase 9 Step 9.3 -- only on a fresh touch 1 (never on a follow-up touch, which
    # would otherwise create a second, competing sequence for this lead+channel). A
    # no-op if the product has no cadence configured (today's behavior, unchanged).
    if not followup_level:
        create_sequence_for_send(db, lead, "WHATSAPP", datetime.utcnow())

    log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_WHATSAPP", 1.0, "MEDIUM", "EXECUTE",
                    payload={"template": spec["name"]})
    logger.info("OUTREACH_WA %s -> sent template '%s' to %s", lead.company_name, spec["name"], to_phone)
    return lead.id
