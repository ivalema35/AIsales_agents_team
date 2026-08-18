"""Real-data aggregations for the Analytics page (CRM_UI_UX_PLAN.md Phase 3). Every
number here is computed from existing tables at query time -- nothing is pre-aggregated
or cached, so it's always current, and nothing is invented when a metric genuinely isn't
trackable yet (matches reporting_service.py's same KPI-honesty rule).
"""
from datetime import datetime, timedelta

from sqlalchemy import func

from database.models import InboundConversation, Lead, LeadScore, OutreachLog, Product
from services.reporting_service import IST_OFFSET

# Display order only (not a cumulative/"reached at least" ordering -- a first version of
# this DID compute it that way, and every early stage showed the same total, since almost
# every lead is processed straight through DISCOVERED->ENRICHED->REVIEWED->SCORED in one
# pass and doesn't linger at the intermediate statuses; a cumulative count made that look
# like a data bug. Fixed to a plain "how many leads are sitting at each status RIGHT NOW"
# distribution, straight off `leads.status` -- simpler, and it's literally what the column
# says, no interpretation layered on top).
FUNNEL_STAGES = ["DISCOVERED", "ENRICHED", "REVIEWED", "SCORED",
                 "OUTREACHING", "OUTREACHED", "ENGAGED", "HOT_LEAD", "CONVERTED"]


def get_funnel(db) -> dict:
    counts_by_status = dict(
        db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    )
    stages = [{"stage": stage, "count": counts_by_status.get(stage, 0)} for stage in FUNNEL_STAGES]
    return {
        "stages": stages,
        "rejected": counts_by_status.get("REJECTED", 0),
        "total_leads": sum(counts_by_status.values()),
    }


def get_channel_performance(db) -> dict:
    result = {}
    for channel in ("EMAIL", "WHATSAPP"):
        sent = db.query(OutreachLog).filter(
            OutreachLog.channel == channel, OutreachLog.status == "SENT").count()
        # Real read-receipt/email-open data only -- WhatsApp via Meta's status webhook,
        # EMAIL via Resend's email.opened/clicked webhook (see api/inbound.py's
        # _handle_one_status, api/webhooks.py). Both set OutreachLog.read_at from an
        # actual provider event, never estimated -- a send made before this tracking
        # existed (no provider_message_id captured yet) just can't match a read event
        # and correctly stays uncounted, not fabricated as 0 vs unknown.
        seen = db.query(OutreachLog).filter(
            OutreachLog.channel == channel, OutreachLog.status == "SENT",
            OutreachLog.read_at.isnot(None)).count()
        replies = db.query(InboundConversation).filter(
            InboundConversation.channel == channel).count()
        high_intent = db.query(InboundConversation).filter(
            InboundConversation.channel == channel,
            InboundConversation.intent_detected.in_(["INTERESTED", "DEMO_REQUESTED"])
        ).count()
        result[channel] = {
            "sent": sent,
            "seen": seen,
            "replies": replies,
            "seen_rate": round(seen / sent, 4) if sent else None,
            "reply_rate": round(replies / sent, 4) if sent else None,
            "high_intent_replies": high_intent,
        }
    return result


_GRANULARITY_DAYS = {"day": 1, "week": 7, "month": 30}


def get_trend(db, granularity: str = "day", periods: int = 30) -> list[dict]:
    """Buckets real counts into `periods` buckets of `granularity` size, most recent
    bucket last (chart-reading order: left = past, right = now). Buckets are anchored to
    IST midnight boundaries -- `created_at` is stored in UTC, but every "was this
    discovered today or yesterday" a human here actually asks is in IST, the business's
    own timezone (same reasoning already applied in reporting_service.py's EOD report).

    The old version bucketed as a rolling 24h window ending at whatever UTC instant the
    request happened to land on (`now - i*days` to `now - (i-1)*days`), relabeled with
    just the END timestamp's date -- so "today"'s bucket was never actually today's IST
    calendar day, it drifted with whatever time of day the chart was loaded, and a
    lead's real discovery day could land in the wrong bucket entirely. Found live: real
    counts looked spiky/wrong across the week view in a way that didn't match when
    discovery had actually run.
    """
    bucket_days = _GRANULARITY_DAYS.get(granularity, 1)
    now_ist = datetime.utcnow() + IST_OFFSET
    today_ist_midnight = datetime(now_ist.year, now_ist.month, now_ist.day)  # IST midnight, "today"

    buckets = []  # (start_utc, end_utc, label_ist_date)
    for i in range(periods - 1, -1, -1):
        end_ist_midnight = today_ist_midnight - timedelta(days=bucket_days * i) + timedelta(days=bucket_days)
        start_ist_midnight = end_ist_midnight - timedelta(days=bucket_days)
        buckets.append((start_ist_midnight - IST_OFFSET, end_ist_midnight - IST_OFFSET, start_ist_midnight))

    def _count_in_buckets(model, ts_column, status_filter=None):
        counts = []
        for start_utc, end_utc, _ in buckets:
            q = db.query(model).filter(ts_column >= start_utc, ts_column < end_utc)
            if status_filter is not None:
                q = q.filter(status_filter)
            counts.append(q.count())
        return counts

    leads_counts = _count_in_buckets(Lead, Lead.created_at)
    outreach_counts = _count_in_buckets(OutreachLog, OutreachLog.sent_at, OutreachLog.status == "SENT")
    reply_counts = _count_in_buckets(InboundConversation, InboundConversation.created_at)

    return [
        {
            "period_end": label.strftime("%Y-%m-%d"),
            "leads_discovered": leads_counts[i],
            "outreach_sent": outreach_counts[i],
            "replies_received": reply_counts[i],
        }
        for i, (_, _, label) in enumerate(buckets)
    ]


def get_outreach_funnel(db, start_date: str | None = None, end_date: str | None = None) -> dict:
    """A real COHORT funnel for ONE selected period, broken out PER CHANNEL: of the
    EMAIL messages sent in that period, how many were later seen and how many got a
    reply -- and the same, separately, for WHATSAPP -- so "500 WhatsApp sent -> 250
    seen -> 100 replied" and "400 Email sent -> 200 seen -> 100 replied" both read in
    one view instead of a channel-blind combined number that hides which channel is
    actually converting. "Seen"/"replied" follow each message forward in time (a
    message sent on day 1 can be seen or replied to on day 3), not a same-period-only
    count. One period at a time (single day / week / month / custom range / all-time),
    not a multi-day series -- an earlier version charted 7 days side by side and that
    wasn't what was wanted either: one set of numbers per channel, for whichever single
    period is selected.

    `start_date`/`end_date` are IST calendar dates ("YYYY-MM-DD"), inclusive on both ends.
    Both None -> all-time (every SENT log ever). Only `start_date` given -> that single day.

    Real send volume is small (daily caps are 40/channel -- see
    OUTREACH_DAILY_CAP_EMAIL/WHATSAPP), so a per-row reply lookup is cheap even across a
    wide range; no need for the set-based bulk optimization other endpoints use at
    leads-table scale.
    """
    date_filters = []
    if start_date:
        start_ist = datetime.strptime(start_date, "%Y-%m-%d")
        end_ist = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date \
            else start_ist + timedelta(days=1)
        start_utc, end_utc = start_ist - IST_OFFSET, end_ist - IST_OFFSET
        date_filters = [OutreachLog.sent_at >= start_utc, OutreachLog.sent_at < end_utc]

    channels = {}
    for channel in ("EMAIL", "WHATSAPP"):
        logs = db.query(OutreachLog).filter(
            OutreachLog.status == "SENT", OutreachLog.channel == channel, *date_filters
        ).all()
        sent = len(logs)
        seen = 0
        replied = 0
        # Mutually-exclusive per-message classification -- each SENT message lands in
        # exactly ONE bucket, so the three bucket counts always sum to `sent` exactly
        # (what makes a pie/donut slice of these valid at all: real part-to-whole, not
        # three independent counts that happen to add up to something else). A reply
        # counts a message as "replied" even on the rare case its own read receipt/open
        # pixel never fired (a lead can reply from a client that blocks tracking) --
        # replying is the stronger, rarer signal, so it wins the bucket over "seen."
        buckets = {"replied": 0, "seen_no_reply": 0, "not_seen": 0}
        for log in logs:
            is_seen = log.read_at is not None
            is_replied = db.query(InboundConversation).filter(
                InboundConversation.lead_id == log.lead_id,
                InboundConversation.channel == log.channel,
                InboundConversation.sender_type == "LEAD",
                InboundConversation.created_at > log.sent_at,
            ).first() is not None

            if is_seen:
                seen += 1
            if is_replied:
                replied += 1

            if is_replied:
                buckets["replied"] += 1
            elif is_seen:
                buckets["seen_no_reply"] += 1
            else:
                buckets["not_seen"] += 1

        channels[channel] = {"sent": sent, "seen": seen, "replied": replied, "buckets": buckets}

    return {
        "start": start_date,
        "end": end_date or start_date,
        "channels": channels,
    }


def get_by_product(db) -> list[dict]:
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    result = []
    for p in products:
        lead_ids = [l.id for l in db.query(Lead.id).filter(Lead.product_id == p.id).all()]
        tier_counts = {"HOT": 0, "WARM": 0, "COLD": 0}
        if lead_ids:
            for tier, count in (
                db.query(LeadScore.tier, func.count(LeadScore.id))
                .filter(LeadScore.lead_id.in_(lead_ids))
                .group_by(LeadScore.tier).all()
            ):
                tier_counts[tier] = count
        outreached = db.query(Lead).filter(
            Lead.product_id == p.id,
            Lead.status.in_(["OUTREACHING", "OUTREACHED", "ENGAGED", "HOT_LEAD", "CONVERTED"])
        ).count()
        converted = db.query(Lead).filter(Lead.product_id == p.id, Lead.status == "CONVERTED").count()
        result.append({
            "product_id": p.id,
            "title": p.title,
            "target_country": p.target_country,
            "is_active": bool(p.is_active),
            "total_leads": len(lead_ids),
            "tier_counts": tier_counts,
            "outreached": outreached,
            "converted": converted,
        })
    return result
