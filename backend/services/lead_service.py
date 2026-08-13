"""Atomic lead claiming for outreach (MASTER §5 Phase 3 / non-negotiable rule: atomic
claims everywhere concurrency can double-process something).

Deliberately NOT auto-chained from the SCORE handler. Every other stage in this pipeline
(DISCOVER->ENRICH->REVIEW->SCORE) auto-advances the moment the previous stage finishes --
but once Step 3.3/3.4 wire up real email/WhatsApp sending, auto-chaining this one step
too would mean every SCORE test run starts actually messaging people. Keeping this as a
standalone, explicitly-triggered function is the safety boundary: nothing goes to
outreach until something (a scheduler, a human, a deliberate test call) calls this on
purpose.
"""
from sqlalchemy import text

from cognition.decision_engine import route_action
from database.models import Lead, LeadScore
from jobs.job_queue import enqueue

ELIGIBLE_TIERS = {"HOT", "WARM"}


def claim_lead_for_outreach(db, lead_id):
    """Atomically move a SCORED, outreach-eligible lead to OUTREACHING and enqueue one
    OUTREACH_EMAIL and/or OUTREACH_WA job per channel the lead actually has contact info
    for -- both if both exist, deliberately not "pick one channel". Safe to call
    concurrently for the same lead_id: only the caller that wins the atomic status flip
    enqueues anything.

    Returns the list of channels queued (e.g. ["EMAIL"], ["EMAIL", "WHATSAPP"]), or None
    if the lead wasn't eligible or was already claimed by someone else.

    Eligibility:
      - has at least one contact channel (email or phone/WhatsApp) -- otherwise there's
        nothing to queue and OUTREACHING would be a dead-end status with no job to move
        it forward, so such leads are left at SCORED rather than claimed.
      - tier is HOT or WARM -- COLD leads are not autonomously outreached.
      - the scoring confidence must not have been low enough that SCORING itself routed
        to HUMAN_ESCALATION (re-derived via the same route_action() used at scoring time,
        not persisted separately). An AI should not draft outreach off a signal it
        wasn't confident enough to act on without a human already reviewing it.
    """
    lead = db.get(Lead, lead_id)
    if not lead:
        return None

    has_email = bool(lead.primary_email)
    has_phone = bool(lead.primary_phone or lead.whatsapp_number)
    if not has_email and not has_phone:
        return None

    score = db.query(LeadScore).filter(LeadScore.lead_id == lead_id).first()
    if not score or score.tier not in ELIGIBLE_TIERS:
        return None
    if route_action("SCORING", score.confidence) == "HUMAN_ESCALATION":
        return None

    claimed = db.execute(text(
        "UPDATE leads SET status='OUTREACHING', updated_at=CURRENT_TIMESTAMP "
        "WHERE id=:id AND status='SCORED'"), {"id": lead_id})
    db.commit()
    if claimed.rowcount == 0:
        return None  # not SCORED, or already claimed (by this call or a concurrent one)

    channels_queued = []
    if has_email:
        enqueue(db, "OUTREACH_EMAIL", {"lead_id": lead_id})
        channels_queued.append("EMAIL")
    if has_phone:
        enqueue(db, "OUTREACH_WA", {"lead_id": lead_id})
        channels_queued.append("WHATSAPP")

    return channels_queued
