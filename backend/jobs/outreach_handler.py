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

from agents.outreach_agent import draft_structured_email, draft_followup_email
from agents.quality_controller_agent import review_draft
from cognition.agent_events import log_agent_event
from config import Config
from database.models import Lead, Product, LeadReviewInsight, OutreachLog
from jobs.registry import register_handler
from services.message_format_service import get_available_assets
from services.outreach.company_contact import build_contact_section
from services.outreach.cross_sell import get_cross_sell_products, build_services_list_section
from services.outreach.interest_links import build_interest_urls
from services.outreach.email_service import send_email, extract_resend_id
from services.outreach.suppression import is_suppressed
from services.sequence_service import create_sequence_for_send, touch_number_to_followup_level

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

    content_assets = get_available_assets(db, lead.product_id) or None

    # Phase 13 Step 13.1 -- replaces the old is_followup boolean. jobs/discovery_
    # scheduler.py's follow-up tick (via services/sequence_service.py) enqueues the real
    # touch number (2, 3, 4, ...) alongside sequence_id; level 1 = touch 2 (re-present),
    # level 2 = touch 3 (ask), level 3 = touch 4+ (standing offer, repeatable). None means
    # a fresh touch-1 send, unchanged.
    followup_level = (
        touch_number_to_followup_level(payload.get("touch_number", 2))
        if payload.get("sequence_id") else None
    )

    # Phase 11 (tracker.md A.10 + Steps 11.1-11.6) + Phase 13 Step 13.1 -- EVERY email
    # send, touch-1 or any follow-up level, now goes through the designed, section-based
    # engine built in Phase 11. This supersedes Phase 8's admin-format-driven free-form
    # path for EMAIL entirely (tracker.md A.12): that path (draft_email(), format_
    # sections, resolve_active_format()) is no longer called from anywhere in this
    # handler -- left in place as dead code rather than deleted, a separate cleanup
    # decision, not one this phase makes unilaterally.
    draft = None
    qc_result = None
    qc_feedback = None
    for attempt in range(1, MAX_DRAFT_ATTEMPTS + 1):
        if followup_level:
            draft = draft_followup_email(db, lead.id, product_brief, lead_profile, pain_points,
                                         followup_level, qc_feedback=qc_feedback,
                                         content_assets=content_assets)
        else:
            cross_sell_products = get_cross_sell_products(db, lead.product_id)
            draft = draft_structured_email(db, lead.id, product_brief, lead_profile, pain_points,
                                           qc_feedback=qc_feedback, content_assets=content_assets,
                                           cross_sell_products=cross_sell_products)
        if not draft:
            break
        qc_result = review_draft(db, lead.id, draft, pain_points, product_brief=product_brief,
                                 is_followup=bool(followup_level), followup_level=followup_level,
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

    # Pre-generated (not left to OutreachLog's own column default) so Phase 12 Step 12.2's
    # signed Yes/No links -- which need this exact id -- can be built and embedded in the
    # email BEFORE the row exists, rather than sending first and patching the row after.
    outreach_log_id = str(uuid.uuid4())

    # Phase 11 Step 11.4 / Phase 12 Step 12.2 / Phase 13 Step 13.1 -- interest, contact,
    # and (level 3 only) the real services list are all system-supplied, appended AFTER QC
    # review: none of them carry agent-authored content, so there is nothing in any of
    # them for QC to judge, and handing QC more surface it was never told about is exactly
    # what produced the Step 11.6 bug (it once misread the CTA section as an unreviewed
    # extra). Every EMAIL draft now carries `sections` (touch-1 and every follow-up level
    # alike), so this always runs.
    sections = draft.get("sections")
    if sections is not None:
        sections = sections + [{"type": "INTEREST", **build_interest_urls(lead.id, outreach_log_id)}]
        if followup_level == 3:
            services_section = build_services_list_section(db)
            if services_section:
                sections = sections + [services_section]
        contact_section = build_contact_section(db)
        if contact_section:
            sections = sections + [contact_section]

    unsubscribe_url = f"{Config.PUBLIC_BASE_URL}/unsubscribe/{lead.id}"
    send_response = send_email(lead.primary_email, draft["subject"], draft["body"], unsubscribe_url,
                               content_assets=content_assets, sections=sections)

    db.add(OutreachLog(
        id=outreach_log_id,
        lead_id=lead.id,
        channel="EMAIL",
        message_subject=draft["subject"],
        message_body=draft["body"],
        status="SENT",
        provider_message_id=extract_resend_id(send_response),
        # Phase 8 Step 8.4 -- every subject candidate generated, not just the one sent,
        # so Phase 9 can measure them retrospectively once real reply/open data exists.
        subject_candidates=json.dumps(draft.get("subject_candidates", [draft["subject"]])),
        # Phase 9 Step 9.1 (tracker.md A.8) -- a distinct, queryable value per real variant,
        # so Step 9.2's rollup can compare them from real SQL, no new counter needed
        # (Step 13.3). "STRUCTURED_EMAIL" = fresh touch-1; "FOLLOWUP_LEVEL_1/2/3" = which
        # of Phase 13's three follow-up conversations this was.
        variant_id=f"FOLLOWUP_LEVEL_{followup_level}" if followup_level else "STRUCTURED_EMAIL",
        # Phase 14 Step 14.4 -- the exact same section list this send was rendered from,
        # sections+INTEREST+SERVICES_LIST+CONTACT already merged above -- the one
        # canonical content object every later cross-channel copy reads from.
        content_sections=json.dumps(sections) if sections is not None else None,
    ))
    lead.status = "OUTREACHED"
    db.commit()

    # Phase 9 Step 9.3 -- only on a fresh touch 1 (never on a follow-up touch itself,
    # which would otherwise create a second, competing sequence for the same lead).
    # A no-op if the product has no cadence configured (today's behavior, unchanged).
    if not followup_level:
        create_sequence_for_send(db, lead, "EMAIL", datetime.utcnow())

    log_agent_event(db, "OUTREACH", lead.id, "DISPATCH_EMAIL",
                    qc_result["confidence_score"], "MEDIUM", "EXECUTE")
    logger.info("OUTREACH_EMAIL %s -> sent to %s", lead.company_name, lead.primary_email)
    return lead.id
