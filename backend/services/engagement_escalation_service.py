"""Phase 9 Step 9.4 -- engagement-based escalation. A lead that opens an email
repeatedly but never replies is a real signal being wasted today: the system just
keeps waiting. This surfaces it to a human via the exact same HOT_LEAD path Step 4.3
already built for inbound escalation -- no new UI, no new alert channel, just a new
real reason a lead can land there.

Real signal only, never inferred: this can only ever fire for EMAIL, because that is
the only channel with a real open-tracking webhook (services/outreach's WhatsApp path
has no read-receipt handling at all today) -- WhatsApp sends structurally can never
trigger this, not because of a special-case check, but because open_count never moves
for them in the first place.
"""
from __future__ import annotations

from cognition.agent_events import log_agent_event
from database.models import InboundConversation, Lead, OutreachLog

# How many real opens, with zero real replies, counts as "wasted signal" worth a human
# looking at. Deliberately conservative -- a lead opening 2-3 times isn't unusual
# (forwarded internally, re-read later); repeated opens beyond that is a real pattern.
DEFAULT_OPEN_THRESHOLD = 3


def find_engagement_escalations(db, open_threshold: int = DEFAULT_OPEN_THRESHOLD):
    """Escalates each real, qualifying lead to HOT_LEAD and returns the list of
    (lead, log) pairs escalated this call. Idempotent by construction: escalating
    changes lead.status away from 'OUTREACHED', which this function's own query
    filters on -- an already-escalated lead is structurally excluded from being
    found again on a later call, no separate "already alerted" flag needed.
    """
    candidates = (
        db.query(OutreachLog, Lead)
        .join(Lead, OutreachLog.lead_id == Lead.id)
        .filter(
            OutreachLog.channel == "EMAIL",
            OutreachLog.status == "SENT",
            OutreachLog.open_count >= open_threshold,
            Lead.status == "OUTREACHED",
        )
        .all()
    )

    escalated = []
    for log, lead in candidates:
        replied = db.query(InboundConversation).filter(
            InboundConversation.lead_id == lead.id,
            InboundConversation.sender_type == "LEAD",
            InboundConversation.created_at > log.sent_at,
        ).first() is not None
        if replied:
            continue  # a real reply already exists -- not a wasted signal, nothing to escalate

        lead.status = "HOT_LEAD"
        db.commit()
        log_agent_event(
            db, "ENGAGEMENT", lead.id, "ESCALATE_HIGH_ENGAGEMENT", 0.8, "MEDIUM",
            "HUMAN_ESCALATION",
            payload={"open_count": log.open_count, "outreach_log_id": log.id, "channel": "EMAIL"},
        )
        escalated.append((lead, log))

    return escalated
