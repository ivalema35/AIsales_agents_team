from __future__ import annotations
"""EOD executive report (MASTER Phase 4 / Step 4.5). Aggregates real, already-computed
metrics for one IST calendar day, has a narrowly-scoped LLM call turn them into a short
narrative summary, writes a daily_reports row, and emails it -- scheduled the same way
jobs/discovery_scheduler.py already schedules its own ticks (no n8n/external cron).

DB timestamps are UTC (SQLite CURRENT_TIMESTAMP); "today" for this report is an IST
calendar date, so every query window is converted to the matching UTC range rather than
just taking naive UTC day boundaries.
"""
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from cognition.llm_client import call_json, LLMError
from cognition.prompts import EOD_SUMMARY_SYSTEM_PROMPT
from config import Config
from database.models import AgentEvent, DailyReport, InboundConversation, Lead, LeadScore, OutreachLog
from services.outreach.email_service import send_internal_email
from services.outreach.whatsapp_service import send_free_form_message
from services.phone_utils import normalize_phone
from services.system_settings import get_str, EOD_REPORT_RECIPIENTS, EOD_REPORT_WHATSAPP_RECIPIENTS

logger = logging.getLogger(__name__)

IST_OFFSET = timedelta(hours=5, minutes=30)


def _ist_day_bounds_utc(report_date_str: str):
    """report_date_str: 'YYYY-MM-DD', an IST calendar date. Returns the (start, end) UTC
    datetime range spanning that IST day -- IST 00:00 is UTC 18:30 the previous day."""
    d = datetime.strptime(report_date_str, "%Y-%m-%d")
    start_utc = d - IST_OFFSET
    return start_utc, start_utc + timedelta(days=1)


def _collect_metrics(db, report_date_str: str) -> dict:
    start, end = _ist_day_bounds_utc(report_date_str)

    leads_discovered = db.query(Lead).filter(Lead.created_at >= start, Lead.created_at < end).count()

    tier_counts = {"HOT": 0, "WARM": 0, "COLD": 0}
    for tier, count in (
        db.query(LeadScore.tier, func.count(LeadScore.id))
        .filter(LeadScore.evaluated_at >= start, LeadScore.evaluated_at < end)
        .group_by(LeadScore.tier).all()
    ):
        tier_counts[tier] = count

    channel_status_counts = {}
    total_sent, bounced = 0, 0
    for channel, status, count in (
        db.query(OutreachLog.channel, OutreachLog.status, func.count(OutreachLog.id))
        .filter(OutreachLog.sent_at >= start, OutreachLog.sent_at < end)
        .group_by(OutreachLog.channel, OutreachLog.status).all()
    ):
        channel_status_counts.setdefault(channel, {})[status] = count
        total_sent += count
        if status == "BOUNCED":
            bounced += count

    replies_received = db.query(InboundConversation).filter(
        InboundConversation.created_at >= start, InboundConversation.created_at < end).count()

    high_intent_replies = db.query(InboundConversation).filter(
        InboundConversation.created_at >= start, InboundConversation.created_at < end,
        InboundConversation.intent_detected.in_(["INTERESTED", "DEMO_REQUESTED"])).count()

    human_escalations = db.query(AgentEvent).filter(
        AgentEvent.created_at >= start, AgentEvent.created_at < end,
        AgentEvent.routed_to == "HUMAN_ESCALATION").count()

    return {
        "report_date": report_date_str,
        "leads_discovered": leads_discovered,
        "leads_scored_by_tier": tier_counts,
        "outreach_sent_by_channel": channel_status_counts,
        "replies_received": replies_received,
        "high_intent_replies": high_intent_replies,
        "human_escalations": human_escalations,
        "kpis": {
            # None means "nothing sent today" or "not tracked yet" -- never a fabricated
            # 0/100%. Spam-complaint and human-verified-intent-accuracy signals aren't
            # wired up anywhere in the system yet, so those two stay permanently null
            # until a real signal exists to compute them from.
            "bounce_rate": round(bounced / total_sent, 4) if total_sent else None,
            "bounce_rate_target": 0.02,
            "spam_rate": None,
            "spam_rate_target": 0.001,
            "intent_classification_accuracy": None,
        },
    }


def _write_executive_summary(metrics: dict) -> str:
    prompt = EOD_SUMMARY_SYSTEM_PROMPT + f"""
METRICS: {json.dumps(metrics, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
        summary = str(data.get("executive_summary", "")).strip()
        if summary:
            return summary[:1000]
    except LLMError:
        logger.exception("EOD summary LLM call failed -- falling back to a plain metrics line")

    total_outreach = sum(sum(v.values()) for v in metrics["outreach_sent_by_channel"].values())
    return (f"Automated summary unavailable today (LLM error). Raw metrics: "
           f"{metrics['leads_discovered']} leads discovered, "
           f"{sum(metrics['leads_scored_by_tier'].values())} scored, "
           f"{total_outreach} outreach sent, {metrics['replies_received']} replies, "
           f"{metrics['human_escalations']} escalations.")


def _format_report_body(metrics: dict, summary: str) -> str:
    kpis = metrics["kpis"]
    bounce_line = (f"Bounce rate: {kpis['bounce_rate']:.2%} (target < {kpis['bounce_rate_target']:.0%})"
                   if kpis["bounce_rate"] is not None else "Bounce rate: no sends today")
    return "\n".join([
        f"AI-BOS Daily Report -- {metrics['report_date']}",
        "",
        summary,
        "",
        "---",
        f"Leads discovered: {metrics['leads_discovered']}",
        f"Scored by tier: HOT={metrics['leads_scored_by_tier'].get('HOT', 0)} "
        f"WARM={metrics['leads_scored_by_tier'].get('WARM', 0)} "
        f"COLD={metrics['leads_scored_by_tier'].get('COLD', 0)}",
        f"Outreach sent by channel: {json.dumps(metrics['outreach_sent_by_channel'])}",
        f"Replies received: {metrics['replies_received']}",
        f"High-intent replies (INTERESTED/DEMO_REQUESTED): {metrics['high_intent_replies']}",
        f"Human escalations: {metrics['human_escalations']}",
        bounce_line,
        "Spam rate: not tracked yet (no spam-complaint signal wired up)",
        "Intent classification accuracy: not tracked yet (no human-verified ground truth)",
    ])


def generate(db, report_date_str: str | None = None) -> DailyReport:
    """Idempotent per report_date -- if a report for that IST date already exists, returns
    it unchanged instead of generating (and emailing) a duplicate."""
    report_date_str = report_date_str or (datetime.utcnow() + IST_OFFSET).strftime("%Y-%m-%d")

    existing = db.query(DailyReport).filter(DailyReport.report_date == report_date_str).first()
    if existing:
        logger.info("EOD report for %s already exists, skipping", report_date_str)
        return existing

    metrics = _collect_metrics(db, report_date_str)
    summary = _write_executive_summary(metrics)

    report = DailyReport(
        report_date=report_date_str,
        metrics_summary=json.dumps(metrics),
        executive_summary_text=summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    body = _format_report_body(metrics, summary)
    subject = f"AI-BOS Daily Report -- {report_date_str}"

    # Dashboard-editable (CRM_UI_UX_PLAN.md Phase 2) -- Config's env-var value is only the
    # fallback default now, used until a human ever sets this from the dashboard.
    email_recipients = [e.strip() for e in
                        get_str(db, EOD_REPORT_RECIPIENTS, default=",".join(Config.EOD_REPORT_RECIPIENTS)).split(",")
                        if e.strip()]
    whatsapp_recipients = [p.strip() for p in
                           get_str(db, EOD_REPORT_WHATSAPP_RECIPIENTS,
                                  default=",".join(Config.EOD_REPORT_WHATSAPP_RECIPIENTS)).split(",")
                           if p.strip()]

    # Each recipient/channel is independent and best-effort -- one failing (e.g. a
    # WhatsApp free-form send outside Meta's 24h customer-service window, which isn't
    # guaranteed open at an unattended 23:50 tick) must not roll back the already-written
    # report row or block delivery to everyone else.
    for recipient in email_recipients:
        try:
            send_internal_email(recipient, subject, body)
        except Exception:  # noqa: BLE001
            logger.exception("EOD report email to %s failed", recipient)

    for phone in whatsapp_recipients:
        # These are internal team numbers (not a lead's), so there's no product to derive
        # a country from -- "IN" is the right default hint (same reasoning restated in
        # normalize_phone's own docstring: it's a hint for numbers with no explicit
        # country code, not a hard requirement the number BE Indian).
        to_phone = normalize_phone(phone, country_hint="IN")
        if not to_phone:
            logger.warning("EOD report WhatsApp recipient %r did not parse to a valid number, skipping", phone)
            continue
        try:
            send_free_form_message(to_phone, body)
        except Exception:  # noqa: BLE001
            logger.exception("EOD report WhatsApp to %s failed", to_phone)

    logger.info("EOD report generated for %s", report_date_str)
    return report
