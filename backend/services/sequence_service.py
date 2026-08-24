"""Phase 9 Step 9.3 -- multi-touch follow-up sequences (tracker.md). Every existing
outreach rule still applies at every touch, not just the first: suppression re-checked
immediately before each real send (inside the OUTREACH_EMAIL/OUTREACH_WA handlers this
enqueues into, unchanged), OPT_OUT absolute, daily pacing caps respected by the caller
(jobs/discovery_scheduler.py's follow-up tick), and the whole thing sits behind
`autonomous_outreach_enabled` -- a follow-up is still an autonomous real send.
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta

from sqlalchemy import text

from database.models import InboundConversation, Lead, OutreachSequence, Product
from jobs.job_queue import enqueue
from services.outreach.suppression import is_suppressed

# Phase 13 Step 13.1 -- how many distinct follow-up "levels" exist (re-present / ask /
# standing offer). A product's own followup_cadence_days could in principle have more
# entries than this, but only three distinct conversations are defined -- a touch beyond
# level 3 repeats level 3's own evergreen "standing offer" framing (deliberately written
# to be repeatable) rather than inventing an undefined level 4. Shared by both
# jobs/outreach_handler.py (EMAIL) and jobs/outreach_wa_handler.py (WhatsApp), which both
# derive their level from the SAME touch_number this module enqueues below.
MAX_FOLLOWUP_LEVEL = 3


def touch_number_to_followup_level(touch_number: int) -> int:
    return min(max(1, touch_number - 1), MAX_FOLLOWUP_LEVEL)


def create_sequence_for_send(db, lead, channel, sent_at):
    """Called right after a TOUCH 1 (fresh, non-follow-up) send succeeds. Only creates a
    row if the lead's product actually has a cadence configured -- an empty/absent
    cadence means no follow-ups at all, today's single-touch behavior unchanged. Also a
    no-op if a sequence already exists for this lead+channel (never duplicate one).
    """
    product = db.get(Product, lead.product_id)
    cadence = json.loads(product.followup_cadence_days or "[]") if product else []
    if not cadence:
        return None

    existing = db.query(OutreachSequence).filter(
        OutreachSequence.lead_id == lead.id, OutreachSequence.channel == channel,
    ).first()
    if existing:
        return None

    seq = OutreachSequence(
        lead_id=lead.id,
        channel=channel,
        original_sent_at=sent_at,
        next_step=2,
        max_steps=len(cadence) + 1,
        next_run_at=sent_at + timedelta(days=cadence[0]),
        status="ACTIVE",
    )
    db.add(seq)
    db.commit()
    return seq


def process_due_followup(db, sequence_id):
    """Atomically claims ONE due sequence row (rowcount-checked UPDATE, same pattern as
    services/lead_service.py's claim_lead_for_outreach -- safe under concurrent scheduler
    ticks), then: exits the sequence if the lead already replied since touch 1 (a
    replied lead needs no more nudging), stops it if the lead is now suppressed (an
    opt-out mid-sequence must halt every subsequent touch immediately), or advances the
    sequence's own state and enqueues the next real touch through the EXACT same
    OUTREACH_EMAIL/OUTREACH_WA job handlers a fresh send uses -- suppression is
    re-checked AGAIN immediately before that actual send, inside those handlers,
    unchanged from today.

    Returns "SENT", "SKIPPED_REPLIED", "SKIPPED_SUPPRESSED", or None (already claimed by
    a concurrent call, or no longer ACTIVE).
    """
    claimed = db.execute(text(
        "UPDATE outreach_sequences SET status='CLAIMED', updated_at=CURRENT_TIMESTAMP "
        "WHERE id=:id AND status='ACTIVE'"), {"id": sequence_id})
    db.commit()
    if claimed.rowcount == 0:
        return None

    # The claim above is a raw SQL UPDATE (text()), which the ORM's identity map never
    # sees -- db.get() would otherwise hand back a STALE cached object still showing the
    # pre-claim status. Refreshing here is required, not optional: without it, a later
    # `seq.status = "ACTIVE"` (the same value the stale cache already believes is
    # current) registers as no real change to SQLAlchemy's dirty-attribute tracking, so
    # the flush silently skips writing it -- the row is left stuck on 'CLAIMED' forever,
    # a real bug caught live testing THIS function, not a hypothetical.
    seq = db.get(OutreachSequence, sequence_id)
    db.refresh(seq)
    lead = db.get(Lead, seq.lead_id)
    if not lead:
        seq.status = "STOPPED"
        seq.terminal_reason = "SUPPRESSED"
        db.commit()
        return "SKIPPED_SUPPRESSED"

    replied = db.query(InboundConversation).filter(
        InboundConversation.lead_id == lead.id,
        InboundConversation.channel == seq.channel,
        InboundConversation.sender_type == "LEAD",
        InboundConversation.created_at > seq.original_sent_at,
    ).first() is not None
    if replied:
        seq.status = "COMPLETED"
        seq.terminal_reason = "REPLIED"
        db.commit()
        return "SKIPPED_REPLIED"

    identifier = lead.primary_email if seq.channel == "EMAIL" else (lead.whatsapp_number or lead.primary_phone)
    if not identifier or is_suppressed(db, seq.channel, identifier):
        seq.status = "STOPPED"
        seq.terminal_reason = "SUPPRESSED"
        db.commit()
        return "SKIPPED_SUPPRESSED"

    # Advance state BEFORE enqueueing -- matches touch-1's own claim-then-enqueue order
    # (services/lead_service.py), so a concurrent tick can never re-claim this touch.
    this_touch = seq.next_step
    seq.next_step += 1
    if seq.next_step > seq.max_steps:
        seq.status = "COMPLETED"
        seq.terminal_reason = "MAX_STEPS_REACHED"
    else:
        product = db.get(Product, lead.product_id)
        cadence = json.loads(product.followup_cadence_days or "[]") if product else []
        offset_days = cadence[seq.next_step - 2]  # cadence[0] = touch1->2, [1] = touch2->3, ...
        seq.next_run_at = datetime.utcnow() + timedelta(days=offset_days)
        seq.status = "ACTIVE"
    db.commit()

    job_type = "OUTREACH_EMAIL" if seq.channel == "EMAIL" else "OUTREACH_WA"
    enqueue(db, job_type, {"lead_id": lead.id, "sequence_id": seq.id, "touch_number": this_touch})
    return "SENT"
