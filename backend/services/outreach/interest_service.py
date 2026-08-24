"""Phase 12 Steps 12.3-12.6 -- what a real Yes/No click actually does once
api/interest.py has verified the token is genuine.

Step 12.3 (idempotent record), 12.4 (HOT_LEAD escalation reuse -- not a parallel status
system), 12.5 (admin alert), 12.6 (No stops the sequence but never touches suppression).
"""
from __future__ import annotations
import logging
import uuid

from sqlalchemy.exc import IntegrityError

from cognition.agent_events import log_agent_event
from config import Config
from database.models import InterestResponse, OutreachSequence
from services.outreach.email_service import send_internal_email
from services.outreach.whatsapp_service import send_free_form_message
from services.phone_utils import normalize_phone
from services.system_settings import get_str, EOD_REPORT_RECIPIENTS, EOD_REPORT_WHATSAPP_RECIPIENTS

logger = logging.getLogger(__name__)


def record_interest_response(db, lead, log, response: str) -> bool:
    """Idempotent insert -- relies on interest_responses' own UNIQUE(outreach_log_id,
    response) constraint (catch IntegrityError, not a race-prone check-then-insert), the
    exact pattern services/inbound_service.py's record_inbound() already uses for the
    same reason (a mail client's link-prefetch scanner or a real double-click must record
    once and alert once, not twice).

    Returns True the FIRST time this exact (send, response) is recorded -- callers must
    only escalate/alert/stop-sequence on True; a repeat click is silently a no-op.
    """
    row = InterestResponse(id=str(uuid.uuid4()), lead_id=lead.id, outreach_log_id=log.id, response=response)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.info("interest %s for outreach_log %s -> duplicate click, ignored", response, log.id)
        return False

    if response == "YES":
        _escalate_to_hot_lead(db, lead, log)
        _send_admin_alert(db, lead, log)
    else:
        _stop_sequence(db, lead, log)
    return True


def _escalate_to_hot_lead(db, lead, log):
    """Step 12.4 -- the SAME status transition Step 9.4's engagement escalation and Step
    4.3's inbound classifier already use, never a second parallel "interested" status. A
    declared Yes is the strongest signal this product can ever collect (unlike an
    inferred repeat-open), so confidence=1.0 / risk=HIGH, distinct from the 0.8/MEDIUM
    used for inferred engagement escalation.

    Also stops this lead's active follow-up sequence for this channel (Phase 13 Step
    13.4's own DoD: a real Yes click must exit the sequence at every level, not just
    level 1 -- a real, disclosed gap from Phase 12 itself, closed here rather than left
    open: a lead who already said Yes has no business still receiving a scheduled "did
    you get a chance to look?" nudge).
    """
    if lead.status != "HOT_LEAD":
        lead.status = "HOT_LEAD"
        db.commit()
    _stop_active_sequence(db, lead, log, "ESCALATED")
    log_agent_event(
        db, "INTEREST", lead.id, "YES_CLICK_ESCALATE", 1.0, "HIGH", "HUMAN_ESCALATION",
        payload={"outreach_log_id": log.id, "channel": log.channel},
    )


def _send_admin_alert(db, lead, log):
    """Step 12.5 -- reuses send_internal_email() (Step 4.5) exactly like the existing
    stuck-process alert does, plus an optional WhatsApp leg via send_free_form_message()
    (Step 4.5's EOD report already sends internal WhatsApp alerts the same way). Reuses
    the SAME recipient settings as every other internal alert in this codebase
    (EOD_REPORT_RECIPIENTS / _WHATSAPP_RECIPIENTS) rather than inventing a second,
    parallel "who gets notified" list -- already dashboard-editable, no new Settings UI
    needed.

    Rate-limited on the same principle as the stuck alert ("one alert per real event,
    never one per tick") -- but via a different, more direct mechanism: this only ever
    runs from inside record_interest_response()'s post-INSERT branch, which the UNIQUE
    constraint above already guarantees fires at most once per real click. No separate
    cooldown timestamp needed the way the tick-based stuck alert requires one.
    """
    subject = f"AI-BOS: {lead.company_name} said YES (Ref: {lead.reference_code})"
    body = (
        f"{lead.company_name} (Ref: {lead.reference_code}) just clicked \"Yes, interested\" "
        f"on the {log.channel.title()} sent {log.sent_at}.\n\n"
        f"Contact: {lead.contact_person_name or 'n/a'} "
        f"({lead.primary_email or lead.primary_phone or 'no contact info on file'})\n\n"
        f"View in CRM: {Config.FRONTEND_ORIGIN}/leads/{lead.id}"
    )

    email_recipients = [e.strip() for e in
                        get_str(db, EOD_REPORT_RECIPIENTS, default=",".join(Config.EOD_REPORT_RECIPIENTS)).split(",")
                        if e.strip()]
    for recipient in email_recipients:
        try:
            send_internal_email(recipient, subject, body)
        except Exception:  # noqa: BLE001 - one bad send must not block the others
            logger.exception("interest-click admin alert email to %s failed", recipient)

    whatsapp_recipients = [p.strip() for p in
                           get_str(db, EOD_REPORT_WHATSAPP_RECIPIENTS,
                                  default=",".join(Config.EOD_REPORT_WHATSAPP_RECIPIENTS)).split(",")
                           if p.strip()]
    for phone in whatsapp_recipients:
        to_phone = normalize_phone(phone, country_hint="IN")
        if not to_phone:
            logger.warning("interest-click alert WhatsApp recipient %r invalid, skipping", phone)
            continue
        try:
            send_free_form_message(to_phone, body)
        except Exception:  # noqa: BLE001
            logger.exception("interest-click admin alert WhatsApp to %s failed", to_phone)


def _stop_active_sequence(db, lead, log, terminal_reason: str):
    """Shared by both a No (Step 12.6) and a Yes (Step 13.4) -- either real click ends
    this lead's need for further scheduled follow-ups on this channel, immediately (not
    lazily waiting for the next scheduled touch's own claim-time checks to notice).
    """
    seq = db.query(OutreachSequence).filter(
        OutreachSequence.lead_id == lead.id,
        OutreachSequence.channel == log.channel,
        OutreachSequence.status == "ACTIVE",
    ).first()
    if seq:
        seq.status = "STOPPED"
        seq.terminal_reason = terminal_reason
        db.commit()


def _stop_sequence(db, lead, log):
    """Step 12.6 -- a No stops further follow-ups for this lead+channel, but is
    deliberately NOT written to the suppression list: declining one pitch is not a legal
    opt-out, and conflating the two would silently and permanently kill contactability
    the lead never actually revoked. The unsubscribe link stays the only path into
    suppression.
    """
    _stop_active_sequence(db, lead, log, "DECLINED")
    log_agent_event(
        db, "INTEREST", lead.id, "NO_CLICK_STOP_SEQUENCE", 1.0, "LOW", "EXECUTE",
        payload={"outreach_log_id": log.id, "channel": log.channel},
    )
