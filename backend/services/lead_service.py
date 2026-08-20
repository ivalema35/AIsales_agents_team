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
from __future__ import annotations
from sqlalchemy import text

from cognition.decision_engine import route_action
from database.models import Lead, LeadScore
from jobs.job_queue import enqueue

ELIGIBLE_TIERS = {"HOT", "WARM"}


def claim_lead_for_outreach(db, lead_id, run_after=None, allowed_channels=None, enqueue_jobs=True,
                            force=False):
    """Atomically move a SCORED, outreach-eligible lead to OUTREACHING and enqueue one
    OUTREACH_EMAIL and/or OUTREACH_WA job per channel the lead actually has contact info
    for -- both if both exist, deliberately not "pick one channel". Safe to call
    concurrently for the same lead_id: only the caller that wins the atomic status flip
    enqueues anything.

    `run_after`: optional datetime forwarded to both enqueue() calls -- lets a caller
    (jobs/discovery_scheduler.py's outreach tick) stagger a batch instead of bursting all
    of it at once.

    `allowed_channels`: optional set restricting which channels may be enqueued THIS call
    (e.g. {"EMAIL"} when the WhatsApp daily cap is already used up for today). None means
    no restriction. If this narrows a lead down to zero usable channels, the lead is left
    at SCORED (not claimed) rather than claimed with nothing queued -- it's a legitimate
    candidate for a later tick once budget frees up, not a dead lead.

    `enqueue_jobs=False`: skip creating OUTREACH_EMAIL/OUTREACH_WA jobs -- for a caller
    that only wants this function's atomic SCORED->OUTREACHING claim + eligible-channel
    list and is about to process those channels itself, synchronously, in the same
    request (api/leads.py's manual "Send Outreach Now" trigger). Without this, that
    endpoint's own synchronous handler calls AND jobs.worker picking up the queued jobs
    both send -- a guaranteed real duplicate send every time the worker is running, not
    just an occasional race (see tracker.md Step 4.4 duplicate-outreach bug).

    Returns the list of channels queued (e.g. ["EMAIL"], ["EMAIL", "WHATSAPP"]), or None
    if the lead wasn't eligible (no usable channel, wrong tier, low confidence) or was
    already claimed by someone else.

    Eligibility:
      - has at least one contact channel (email or phone/WhatsApp), not excluded by
        `allowed_channels` -- otherwise there's nothing to queue right now.
      - tier is HOT or WARM -- COLD leads are not autonomously outreached.
      - the scoring confidence must not have been low enough that SCORING itself routed
        to HUMAN_ESCALATION (re-derived via the same route_action() used at scoring time,
        not persisted separately). An AI should not draft outreach off a signal it
        wasn't confident enough to act on without a human already reviewing it.

    `force=True`: a human, looking at this ONE specific lead, deliberately overrides the
    tier/confidence judgment call above (e.g. a COLD lead they have outside context on).
    Only for api/leads.py's manual single-lead trigger -- never passed by the autonomous
    scheduler tick, which has no human in the loop to be making this call. Does NOT bypass
    the contact-channel check (there's nowhere to send with none), and does NOT touch QC or
    suppression -- those still run, unconditionally, exactly as for any other send. Forcing
    past a low-confidence/COLD judgment call is a business decision; forcing past QC's veto
    or a suppression entry would be a compliance one, and this flag has no reach into either.
    """
    lead = db.get(Lead, lead_id)
    if not lead:
        return None

    has_email = bool(lead.primary_email) and (allowed_channels is None or "EMAIL" in allowed_channels)
    has_phone = bool(lead.primary_phone or lead.whatsapp_number) and (
        allowed_channels is None or "WHATSAPP" in allowed_channels)
    if not has_email and not has_phone:
        return None

    if not force:
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
        if enqueue_jobs:
            enqueue(db, "OUTREACH_EMAIL", {"lead_id": lead_id}, run_after=run_after)
        channels_queued.append("EMAIL")
    if has_phone:
        if enqueue_jobs:
            enqueue(db, "OUTREACH_WA", {"lead_id": lead_id}, run_after=run_after)
        channels_queued.append("WHATSAPP")

    return channels_queued
