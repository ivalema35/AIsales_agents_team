"""OUTREACH_EMAIL job handler (MASTER Phase 3).

Registered here rather than inline in jobs/worker.py so worker.py stays a generic poll
loop with zero business logic -- same separation already used for scraper_worker's own
handlers. Runs in jobs/worker.py (NOT scraper_worker/async_runner.py) deliberately:
outreach needs controlled PACING (send N per hour, sequential), not async_runner's
concurrent fan-out, which is right for scraping but wrong for a channel where sending
too fast looks like spam. Importing this module is what registers the handler --
jobs/worker.py's __main__ (or a test) must `import jobs.outreach_handler` for it to
take effect, the same requirement register_handler already has for any handler module.
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime

from agents.outreach_agent import draft_email
from agents.quality_controller_agent import review_draft
from cognition.agent_events import log_agent_event
from config import Config
from database.models import Lead, Product, LeadReviewInsight, OutreachLog
from jobs.registry import register_handler
from services.message_format_service import resolve_active_format, get_available_assets
from services.outreach.email_service import send_email, extract_resend_id
from services.outreach.suppression import is_suppressed
from services.sequence_service import create_sequence_for_send

logger = logging.getLogger(__name__)

MAX_DRAFT_ATTEMPTS = 2  # one retry with QC's feedback if rejected, then escalate -- never loop forever


@register_handler("OUTREACH_EMAIL")
def handle_outreach_email(db, payload):
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    if not lead.primary_email:
        logger.info("OUTREACH_EMAIL %s -> no email on file, skipping", lead.company_name)
        return lead.id

    # The 100% rule: checked here, before drafting even starts, AND again immediately
    # before the actual send below -- a single check this far upstream of the network
    # call is not enough on its own.
    if is_suppressed(db, "EMAIL", lead.primary_email):
        logger.info("OUTREACH_EMAIL %s -> suppressed, aborting before draft", lead.company_name)
        lead.status = "REJECTED"
        db.commit()
        return lead.id

    product = db.get(Product, lead.product_id)
    if not product:
        raise ValueError(f"product {lead.product_id} not found for lead {lead.id}")

    insight = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.lead_id == lead.id)
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []

    product_brief = {
        "title": product.title,
        "description": product.description,
        "value_proposition": product.value_proposition,
    }
    lead_profile = {
        "company_name": lead.company_name,
        "contact_person_name": lead.contact_person_name,
        "contact_person_role": lead.contact_person_role,
    }

    # Phase 8 Steps 8.1/8.2 (tracker.md A.7) -- resolve an admin-defined format/content
    # library for this product+EMAIL, if one exists. Both are None when nothing has been
    # configured, which keeps draft_email()'s prompt byte-identical to before Phase 8.
    fmt_row = resolve_active_format(db, lead.product_id, "EMAIL")
    format_sections = json.loads(fmt_row.sections) if fmt_row else None
    content_assets = get_available_assets(db, lead.product_id) or None

    # Phase 9 Step 9.3 -- present only when jobs/discovery_scheduler.py's follow-up tick
    # (via services/sequence_service.py) enqueued this as touch 2+, never on a fresh
    # touch-1 send. Tells the agent to write a brief nudge, not repeat the full pitch.
    is_followup = bool(payload.get("sequence_id"))

    draft = None
    qc_result = None
    qc_feedback = None
    for attempt in range(1, MAX_DRAFT_ATTEMPTS + 1):
        draft = draft_email(db, lead.id, product_brief, lead_profile, pain_points,
                            qc_feedback=qc_feedback, format_sections=format_sections,
                            content_assets=content_assets, is_followup=is_followup)
        if not draft:
            break
        qc_result = review_draft(db, lead.id, draft, pain_points, product_brief=product_brief,
                                 is_followup=is_followup, format_sections=format_sections,
                                 content_assets=content_assets)
        if qc_result["approved"]:
            break
        logger.info("OUTREACH_EMAIL %s -> QC rejected draft %d/%d: %s",
                   lead.company_name, attempt, MAX_DRAFT_ATTEMPTS, qc_result["rejection_reasons"])
        qc_feedback = qc_result["suggested_corrections"] or "; ".join(qc_result["rejection_reasons"])
        draft = None

    if not draft or not qc_result or not qc_result["approved"]:
        # QC's veto is absolute -- no draft means no send, ever. The lead stays exactly
        # where it was (OUTREACHING) rather than being pushed into an unrelated status;
        # the HUMAN_ESCALATION agent_events row is the actual signal for a human to act on.
        logger.info("OUTREACH_EMAIL %s -> no QC-approved draft after %d attempt(s), escalating",
                   lead.company_name, MAX_DRAFT_ATTEMPTS)
        log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_EMAIL", 0.0, "MEDIUM", "HUMAN_ESCALATION")
        return lead.id

    # Re-check suppression immediately before the network call -- the whole point of
    # the 100% rule is that it applies right up to the send, not just once earlier.
    if is_suppressed(db, "EMAIL", lead.primary_email):
        logger.info("OUTREACH_EMAIL %s -> suppressed between draft and send, aborting", lead.company_name)
        lead.status = "REJECTED"
        db.commit()
        return lead.id

    unsubscribe_url = f"{Config.PUBLIC_BASE_URL}/unsubscribe/{lead.id}"
    send_response = send_email(lead.primary_email, draft["subject"], draft["body"], unsubscribe_url)

    db.add(OutreachLog(
        id=str(uuid.uuid4()),
        lead_id=lead.id,
        channel="EMAIL",
        message_subject=draft["subject"],
        message_body=draft["body"],
        status="SENT",
        provider_message_id=extract_resend_id(send_response),
        # Phase 8 Step 8.4 -- every subject candidate generated, not just the one sent,
        # so Phase 9 can measure them retrospectively once real reply/open data exists.
        subject_candidates=json.dumps(draft.get("subject_candidates", [draft["subject"]])),
        # Phase 9 Step 9.1 (tracker.md A.8) -- which message_format version drafted this,
        # so Step 9.2 can roll up real reply/open rates per variant later. "FREE_FORM" is
        # an explicit sentinel (this codebase's own convention, e.g. Lead.sales_route's
        # "UNASSIGNED") rather than a bare NULL, so a report reads clearly either way.
        variant_id=fmt_row.id if fmt_row else "FREE_FORM",
    ))
    lead.status = "OUTREACHED"
    db.commit()

    # Phase 9 Step 9.3 -- only on a fresh touch 1 (never on a follow-up touch itself,
    # which would otherwise create a second, competing sequence for the same lead).
    # A no-op if the product has no cadence configured (today's behavior, unchanged).
    if not is_followup:
        create_sequence_for_send(db, lead, "EMAIL", datetime.utcnow())

    log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_EMAIL",
                    qc_result["confidence_score"], "MEDIUM", "EXECUTE")
    logger.info("OUTREACH_EMAIL %s -> sent to %s", lead.company_name, lead.primary_email)
    return lead.id
