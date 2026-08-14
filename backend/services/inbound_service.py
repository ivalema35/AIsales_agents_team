"""Shared inbound-message handling (MASTER Phase 4 / Steps 4.1-4.3). Both the WhatsApp
webhook (api/inbound.py) and the email IMAP poller (jobs/inbound_poller.py) funnel
through record_inbound() so idempotency, lead-matching, and hard-classification logic
live in exactly one place, not duplicated per channel.

Step 4.2 hard classifiers (STOP/auto-reply) run inline here, synchronously, since
they're cheap rule-based checks. Step 4.3's AI classification is NOT run inline -- it's
enqueued as a CLASSIFY_INBOUND job instead, so a webhook call (which Meta expects a fast
200 from) or an IMAP poll cycle never blocks on an LLM call.
"""
import logging
import uuid

from sqlalchemy.exc import IntegrityError

from cognition.hard_classifiers import is_optout, is_autoreply
from database.models import InboundConversation, Lead
from jobs.job_queue import enqueue
from services.outreach.suppression import add_suppression

logger = logging.getLogger(__name__)


def find_lead_by_contact(db, channel: str, identifier: str):
    """Matches an inbound sender to an existing lead by contact info. Returns the most
    recently updated match if more than one lead somehow shares the identifier (can
    happen with role-account emails/shared front-desk numbers) -- picking the most
    recent conversation partner is a better default than an arbitrary one."""
    if not identifier:
        return None
    query = db.query(Lead)
    if channel == "EMAIL":
        query = query.filter(Lead.primary_email == identifier)
    else:
        query = query.filter(
            (Lead.primary_phone == identifier) | (Lead.whatsapp_number == identifier))
    return query.order_by(Lead.updated_at.desc()).first()


def record_inbound(db, channel: str, sender_identifier: str, provider_message_id: str,
                   message_content: str, email_headers: dict | None = None) -> str | None:
    """Idempotent insert -- relies on inbound_conversations' own UNIQUE(channel,
    provider_message_id) constraint (catch IntegrityError, not a race-prone
    check-then-insert), same pattern as suppression.py's add_suppression().

    Runs the Step 4.2 hard classifiers before anything else touches this message:
      - STOP/opt-out -> suppress the sender immediately (the 100% rule: this happens
        even before we'd know whether an AI classifier agreed -- there is no AI
        classifier in this path yet anyway, Step 4.3), tagged intent_detected='STOP'.
      - Auto-reply/out-of-office -> tagged intent_detected='AUTO_REPLY', never treated
        as a real signal.
      - Anything else -> intent_detected stays NULL and a CLASSIFY_INBOUND job is
        enqueued for Step 4.3's AI classifier to pick up asynchronously.

    Returns the new InboundConversation id, or None if this was a duplicate delivery,
    or None (logged) if no lead matches the sender -- lead_id is NOT NULL on this table,
    so an inbound message from someone we have no lead record for has nowhere to go yet.
    """
    lead = find_lead_by_contact(db, channel, sender_identifier)
    if not lead:
        logger.warning("inbound %s from %s -> no matching lead, dropping", channel, sender_identifier)
        return None

    intent = None
    if is_optout(message_content):
        intent = "STOP"
        add_suppression(db, channel, sender_identifier, "STOP")
        logger.info("inbound %s from %s -> STOP detected, suppressed", channel, sender_identifier)
    elif is_autoreply(message_content, email_headers=email_headers):
        intent = "AUTO_REPLY"
        logger.info("inbound %s from %s -> auto-reply detected, not a real signal", channel, sender_identifier)

    row = InboundConversation(
        id=str(uuid.uuid4()),
        lead_id=lead.id,
        channel=channel,
        provider_message_id=provider_message_id,
        sender_type="LEAD",
        message_content=message_content,
        intent_detected=intent,
    )
    db.add(row)
    # The row insert and the CLASSIFY_INBOUND enqueue must land in the SAME commit --
    # two separate commits here means a message could get durably recorded while its
    # job silently never gets created if the second commit ever fails, and no future
    # poll cycle would retry it (the row already exists, so it's just seen as a
    # duplicate and skipped forever).
    if intent is None:
        enqueue(db, "CLASSIFY_INBOUND", {"inbound_conversation_id": row.id}, commit=False)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.info("inbound %s %s -> duplicate delivery, ignored", channel, provider_message_id)
        return None

    logger.info("inbound %s from %s -> recorded for lead %s (intent=%s)",
               channel, sender_identifier, lead.company_name, intent)

    return row.id
