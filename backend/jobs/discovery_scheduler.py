"""Discovery scheduler (tracker.md A.2) -- replaces n8n entirely for Step 3.5. A small
dedicated always-on process (same "one process per concern" pattern as scraper_worker/
async_runner.py vs jobs/worker.py -- MASTER §9 process topology), owns two jobs:

1. Autonomous discovery targeting: keep each active product's ICP Strategy fresh (via
   agents/icp_strategy_agent.py) and fire paced DISCOVER jobs across
   search_queries x target_regions -- no human types a city/keyword combo in daily.
2. Outreach pacing tick: claim SCORED leads for outreach up to the daily per-channel cap,
   staggered via run_after so a day's worth of sends doesn't burst all at once (the
   "pacing caps" item flagged open under DoD Gate P3).
3. EOD report tick (Step 4.5): once per day, after 23:50 IST, generates and emails the
   daily_reports row via services/reporting_service.py if today's doesn't already exist.
4. Stuck-state alert tick (Step 6.4): every tick, checks for a DOWN process, a lead stranded
   in OUTREACHING, a job stuck CLAIMED, or a DEAD pile-up, and emails the admin -- at most
   once per cooldown window -- if anything is wrong. Detection only; nothing here fixes what
   it finds (that's a deliberately separate, riskier capability -- see tracker.md Step 6.4).
5. Engagement escalation tick (Step 9.4): a lead that opens an email repeatedly but never
   replies gets escalated to HOT_LEAD for a human to look at -- real signal only, structurally
   can never fire for WhatsApp (no open-tracking webhook exists for it).

Run as `python -m jobs.discovery_scheduler`, alongside (not instead of) jobs/worker.py and
scraper_worker/async_runner.py.
"""
from __future__ import annotations
import json
import logging
import time
from datetime import datetime, timedelta

from sqlalchemy import func, text

from config import Config
from database.db_config import SessionLocal
from database.models import (
    Product, ProductStrategy, DiscoveryRun, Lead, LeadScore, DailyReport, OutreachSequence, Campaign, TodoItem)
from jobs.job_queue import enqueue
from agents.icp_strategy_agent import generate_strategy
from services.lead_service import claim_lead_for_outreach
from services.sequence_service import process_due_followup
from services.outreach.whatsapp_template_service import poll_all_pending
from services.engagement_escalation_service import find_engagement_escalations
from services.reporting_service import generate as generate_eod_report, IST_OFFSET
from services.campaign_service import (
    generate_campaign_todo, generate_campaign_suggestion, eligible_campaigns_for_discovery,
    todo_signal_fingerprint)
from services.strategy_reflection_service import run_reflection_cycle
from services.system_settings import (
    get_bool, get_int, get_str, set_str, DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED,
    OUTREACH_DAILY_CAP_EMAIL, OUTREACH_DAILY_CAP_WHATSAPP, DISCOVERY_COOLDOWN_HOURS,
    STUCK_ALERT_ENABLED, STUCK_ALERT_COOLDOWN_MINUTES, STUCK_ALERT_LAST_SENT_AT,
    EOD_REPORT_RECIPIENTS, DAILY_PLAN_LAST_RUN_DATE,
    STRATEGY_REFLECTION_ENABLED, STRATEGY_REFLECTION_LAST_RUN_DATE)
from services.heartbeat import beat, beat_standalone
from services.system_health import (
    get_process_states, find_stuck_leads, find_stuck_jobs, count_dead_jobs)
from services.outreach.email_service import send_internal_email

logger = logging.getLogger(__name__)

HEARTBEAT_NAME = "jobs.discovery_scheduler"


def _active_strategy_queries(db, product_id):
    """Union of the latest ACTIVE AI_GENERATED strategy's queries + all ACTIVE
    HUMAN_ADDED queries (a human can add extra queries without losing the AI's own).
    Returns (deduped query list, most recent AI_GENERATED row's created_at or None).
    """
    rows = (
        db.query(ProductStrategy)
        .filter(ProductStrategy.product_id == product_id, ProductStrategy.status == "ACTIVE")
        .all()
    )
    queries, seen = [], set()
    latest_ai_at = None
    for row in rows:
        for q in json.loads(row.search_queries or "[]"):
            if q not in seen:
                seen.add(q)
                queries.append(q)
        if row.source == "AI_GENERATED" and (latest_ai_at is None or row.created_at > latest_ai_at):
            latest_ai_at = row.created_at
    return queries, latest_ai_at


def _refresh_strategy_if_stale(db, product):
    _, latest_ai_at = _active_strategy_queries(db, product.id)
    if latest_ai_at is not None:
        if datetime.utcnow() - latest_ai_at < timedelta(days=Config.ICP_STRATEGY_REFRESH_DAYS):
            return  # still fresh, nothing to do

    product_brief = {
        "title": product.title,
        "description": product.description,
        "target_keywords": json.loads(product.target_keywords or "[]"),
        "value_proposition": product.value_proposition,
        "pain_point_mappings": json.loads(product.pain_point_mappings or "{}"),
        # Phase 7 Step 7.2: a human-set category boundary (empty by default -- means
        # "unchanged from today", the prompt itself only constrains when this is non-empty).
        "target_business_categories": json.loads(product.target_business_categories or "[]"),
    }
    result = generate_strategy(db, product.id, product_brief)
    if not result:
        logger.warning("ICP strategy generation failed/empty for product %s", product.title)
        return

    # Supersede the previous AI_GENERATED row(s) only -- HUMAN_ADDED rows stay untouched.
    db.query(ProductStrategy).filter(
        ProductStrategy.product_id == product.id,
        ProductStrategy.status == "ACTIVE",
        ProductStrategy.source == "AI_GENERATED",
    ).update({"status": "SUPERSEDED"})

    db.add(ProductStrategy(
        product_id=product.id,
        icp=json.dumps(result["icp"]),
        search_queries=json.dumps(result["search_queries"]),
        target_complaints=json.dumps(result["target_complaints"]),
        source="AI_GENERATED",
        status="ACTIVE",
    ))
    db.commit()
    logger.info("ICP strategy refreshed for product %s -> %d queries",
               product.title, len(result["search_queries"]))


def _run_discovery_tick(db):
    """Fires at most MAX_DISCOVER_PER_TICK DISCOVER jobs this tick, oldest-due product
    first, then each of that product's eligible campaigns (Step 17.7, 2026-09-02 --
    discovery is campaign-driven: a campaign's own target_segment IS the query/region,
    not the product's standing config), respecting each campaign's own cooldown so the
    same search isn't repeated needlessly (and so API budget isn't burned in one burst).

    Dashboard kill-switch: does nothing unless system_settings.discovery_enabled is
    true (default false). Checked fresh from the DB every tick so a dashboard toggle
    takes effect within one poll interval, no process restart needed."""
    if not get_bool(db, DISCOVERY_ENABLED, default=False):
        return 0

    # Product whose most recent DiscoveryRun is oldest (or has NONE at all) goes first --
    # NOT insertion order. Without this, a product with enough due (query, region) combos
    # to fill the whole per-tick budget on its own (an easy bar: a few queries x several
    # regions) permanently starves every product after it in the list, since the loop
    # always restarts from the same first product and breaks as soon as the cap is hit
    # (found live, 2026-08-17 -- a brand new product got zero discovery activity across 3
    # ticks while an older one kept firing). A product with zero DiscoveryRun rows ever
    # (freshly created) has a NULL last-run, which SQLite sorts before any real
    # timestamp -- so a new product is correctly treated as maximally overdue and wins
    # the very next tick. (`Product.updated_at` was tried first and rejected: a NEW
    # product's updated_at is its own creation moment, the MOST recent timestamp of all,
    # which would sort it LAST under "oldest first" -- the opposite of what's needed.)
    last_run_subq = (
        db.query(DiscoveryRun.product_id, func.max(DiscoveryRun.last_run_at).label("last_run"))
        .group_by(DiscoveryRun.product_id)
        .subquery()
    )
    products = (
        db.query(Product)
        .filter(Product.is_active == 1)
        .outerjoin(last_run_subq, last_run_subq.c.product_id == Product.id)
        .order_by(last_run_subq.c.last_run.asc().nullsfirst())
        .all()
    )

    cooldown_hours = get_int(db, DISCOVERY_COOLDOWN_HOURS, default=Config.DISCOVERY_COOLDOWN_HOURS)

    fired = 0
    for product in products:
        if fired >= Config.MAX_DISCOVER_PER_TICK:
            break

        # Step 17.7 (2026-09-02, MASTER_DEVELOPMENT_PRD.md §5C.0 revision, supersedes
        # Step 17.6's own product-level gate): discovery is now campaign-DRIVEN, not just
        # campaign-gated -- each active campaign with a real target_segment runs its OWN
        # search, using its OWN industry+location, not the product's standing target_
        # regions/ICP-strategy queries (that machinery, `_refresh_strategy_if_stale`/
        # `_active_strategy_queries` below, stays defined but is no longer called from
        # here -- Products page's own "AI targeting strategy" tab still reads product_
        # strategies directly, dead-code-kept, not deleted). A product with zero eligible
        # campaigns (none active, or none with a real target yet, or all goals already
        # met) is silently skipped -- not an error, just nothing to search for right now.
        campaigns = eligible_campaigns_for_discovery(db, product.id)

        for campaign in campaigns:
            if fired >= Config.MAX_DISCOVER_PER_TICK:
                break

            target = json.loads(campaign.target_segment or "{}")
            region = target["location"]
            # 2026-09-07, user-caught real bug: a campaign targeting MULTIPLE business types
            # (industry as a list, see _clean_proposal) needs each one run as its OWN real
            # search -- a single vague summary string ("multiple local business types") used
            # to be the only option and produced a search term nothing could be found for.
            # DiscoveryRun is already keyed by (campaign_id, query, region), so each list
            # entry gets its own independent cooldown for free, no schema change needed.
            industries = target["industry"]
            queries = industries if isinstance(industries, list) else [industries]

            for query in queries:
                if fired >= Config.MAX_DISCOVER_PER_TICK:
                    break

                # Cooldown tracked per campaign now (Step 17.7) -- two campaigns for the same
                # product never share one clock, and a campaign whose target changes later
                # (a strategy-refinement to-do) starts a fresh, unblocked cooldown for its new
                # (query, region) pair rather than inheriting the old one's timer.
                run = db.query(DiscoveryRun).filter(
                    DiscoveryRun.campaign_id == campaign.id,
                    DiscoveryRun.query == query,
                    DiscoveryRun.region == region,
                ).first()
                if run and datetime.utcnow() - run.last_run_at < timedelta(hours=cooldown_hours):
                    continue

                enqueue(db, "DISCOVER", {
                    "product_id": product.id, "campaign_id": campaign.id, "query": query, "location": region,
                })
                if run:
                    run.last_run_at = datetime.utcnow()
                else:
                    db.add(DiscoveryRun(product_id=product.id, campaign_id=campaign.id, query=query, region=region))
                db.commit()
                fired += 1
                logger.info("DISCOVER queued: product=%s campaign=%s query=%r region=%s",
                           product.title, campaign.name, query, region)

    return fired


def _queued_today(db, job_type):
    row = db.execute(text(
        "SELECT COUNT(*) AS c FROM jobs WHERE job_type=:t AND date(created_at)=date('now')"
    ), {"t": job_type}).fetchone()
    return row.c


def _run_outreach_tick(db):
    """Claims eligible SCORED leads up to the remaining per-channel daily budget,
    staggering each claimed lead's run_after so sends trickle out instead of bursting.

    Safety kill-switch: does nothing at all unless system_settings.autonomous_outreach_enabled
    is explicitly true (dashboard-toggleable; .env's Config.AUTONOMOUS_OUTREACH_ENABLED is
    only the seed default the first time, before any dashboard row exists). Discovery/
    scoring can run autonomously against real businesses, but real sends to a real third
    party require an explicit opt-in -- this is the project's own non-negotiable rule,
    not just a cautious default (tracker.md A.3)."""
    if not get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=Config.AUTONOMOUS_OUTREACH_ENABLED):
        return 0

    cap_email = get_int(db, OUTREACH_DAILY_CAP_EMAIL, default=Config.OUTREACH_DAILY_CAP_EMAIL)
    cap_whatsapp = get_int(db, OUTREACH_DAILY_CAP_WHATSAPP, default=Config.OUTREACH_DAILY_CAP_WHATSAPP)
    remaining = {
        "EMAIL": cap_email - _queued_today(db, "OUTREACH_EMAIL"),
        "WHATSAPP": cap_whatsapp - _queued_today(db, "OUTREACH_WA"),
    }
    if remaining["EMAIL"] <= 0 and remaining["WHATSAPP"] <= 0:
        return 0

    candidates = (
        db.query(Lead)
        .join(LeadScore, LeadScore.lead_id == Lead.id)
        .filter(Lead.status == "SCORED", LeadScore.tier.in_(("HOT", "WARM")))
        .order_by(Lead.created_at.asc())
        .limit(200)
        .all()
    )

    # Phase 20 Step 20.3 -- Execution Watchdog: a campaign with an active alert (3
    # consecutive real send failures/bounces, see services/campaign_service.py
    # evaluate_execution_watchdog()) is paused for further claims until a human clears it.
    # Every other campaign's leads are claimed exactly as normal -- this never touches
    # AUTONOMOUS_OUTREACH_ENABLED, it only ever narrows what this tick claims.
    paused_campaign_ids = {
        row[0] for row in db.query(Campaign.id).filter(Campaign.watchdog_alert.isnot(None)).all()
    }

    claimed_count = 0
    for lead in candidates:
        if remaining["EMAIL"] <= 0 and remaining["WHATSAPP"] <= 0:
            break
        if lead.campaign_id and lead.campaign_id in paused_campaign_ids:
            continue
        allowed = {ch for ch in ("EMAIL", "WHATSAPP") if remaining[ch] > 0}
        run_after = datetime.utcnow() + timedelta(seconds=claimed_count * Config.OUTREACH_STAGGER_SECONDS)
        channels = claim_lead_for_outreach(db, lead.id, run_after=run_after, allowed_channels=allowed)
        if channels:
            claimed_count += 1
            for ch in channels:
                remaining[ch] -= 1

    if claimed_count:
        logger.info("outreach tick -> claimed %d lead(s)", claimed_count)
    return claimed_count


def _run_followup_tick(db):
    """Phase 9 Step 9.3 -- sends the next due touch for every ACTIVE outreach_sequences
    row whose next_run_at has arrived. Shares the exact same daily per-channel budget as
    _run_outreach_tick above (a follow-up is still a real send counting against the same
    cap) and the exact same autonomous_outreach_enabled kill-switch -- a follow-up is
    still an autonomous real send to a real business, not a lesser action.
    """
    if not get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=Config.AUTONOMOUS_OUTREACH_ENABLED):
        return 0

    cap_email = get_int(db, OUTREACH_DAILY_CAP_EMAIL, default=Config.OUTREACH_DAILY_CAP_EMAIL)
    cap_whatsapp = get_int(db, OUTREACH_DAILY_CAP_WHATSAPP, default=Config.OUTREACH_DAILY_CAP_WHATSAPP)
    remaining = {
        "EMAIL": cap_email - _queued_today(db, "OUTREACH_EMAIL"),
        "WHATSAPP": cap_whatsapp - _queued_today(db, "OUTREACH_WA"),
    }
    if remaining["EMAIL"] <= 0 and remaining["WHATSAPP"] <= 0:
        return 0

    due = (
        db.query(OutreachSequence)
        .filter(OutreachSequence.status == "ACTIVE", OutreachSequence.next_run_at <= datetime.utcnow())
        .order_by(OutreachSequence.next_run_at.asc())
        .limit(200)
        .all()
    )

    sent_count = 0
    for seq in due:
        if remaining.get(seq.channel, 0) <= 0:
            continue
        result = process_due_followup(db, seq.id)
        if result == "SENT":
            sent_count += 1
            remaining[seq.channel] -= 1

    if sent_count:
        logger.info("follow-up tick -> queued %d follow-up(s)", sent_count)
    return sent_count


def _run_eod_report_tick(db):
    """Once per IST calendar day, after 23:50 -- generate() is idempotent per report_date
    (checks daily_reports itself), so a poll interval well under 24h just means this is a
    cheap no-op check most ticks, not a duplicate-report risk."""
    now_ist = datetime.utcnow() + IST_OFFSET
    if (now_ist.hour, now_ist.minute) < (23, 50):
        return
    report_date_str = now_ist.strftime("%Y-%m-%d")
    if db.query(DailyReport).filter(DailyReport.report_date == report_date_str).first():
        return
    generate_eod_report(db, report_date_str)


def _run_stuck_alert_tick(db):
    """Detect-and-alert only (Step 6.4) -- deliberately does not fix anything it finds.
    Auto-recovering a stuck lead or job is its own, riskier decision (retry it? just reset
    the status? what if the underlying cause is still ongoing?) that was explicitly kept out
    of this step's scope; a human acts on what this email reports.
    """
    if not get_bool(db, STUCK_ALERT_ENABLED, default=True):
        return

    down = [p for p in get_process_states(db) if p["state"] in ("DOWN", "ERROR")]
    stuck_leads = find_stuck_leads(db)
    stuck_jobs = find_stuck_jobs(db)
    dead_count = count_dead_jobs(db)

    if not (down or stuck_leads or stuck_jobs or dead_count):
        return  # nothing wrong -- don't touch the cooldown timestamp either

    cooldown_minutes = get_int(db, STUCK_ALERT_COOLDOWN_MINUTES, default=60)
    last_sent = get_str(db, STUCK_ALERT_LAST_SENT_AT, default="")
    if last_sent:
        try:
            elapsed = datetime.utcnow() - datetime.strptime(last_sent, "%Y-%m-%d %H:%M:%S")
            if elapsed < timedelta(minutes=cooldown_minutes):
                return  # already alerted recently; still broken, but not an email storm
        except ValueError:
            pass  # malformed stored value -- treat as "never sent", alert now

    lines = ["AI-BOS system check found the following:", ""]
    if down:
        lines.append(f"Processes needing attention ({len(down)}):")
        lines += [f"  - {p['name']}: {p['state']} (last seen {p['age_seconds']}s ago)"
                  for p in down]
        lines.append("")
    if stuck_leads:
        lines.append(f"Leads stuck in OUTREACHING ({len(stuck_leads)}):")
        lines += [f"  - {l['company_name']} ({l['minutes_stuck']} min)" for l in stuck_leads]
        lines.append("")
    if stuck_jobs:
        lines.append(f"Jobs stuck CLAIMED ({len(stuck_jobs)}):")
        lines += [f"  - {j['job_type']} ({j['minutes_stuck']} min)" for j in stuck_jobs]
        lines.append("")
    if dead_count:
        lines.append(f"Jobs that exhausted every retry (DEAD): {dead_count}")
        lines.append("")
    lines.append("This is a detection-only alert -- nothing was changed automatically. "
                 "Check the System page in the CRM.")

    recipients = get_str(db, EOD_REPORT_RECIPIENTS,
                         default=",".join(Config.EOD_REPORT_RECIPIENTS)).split(",")
    body = "\n".join(lines)
    sent_any = False
    for recipient in recipients:
        recipient = recipient.strip()
        if not recipient:
            continue
        try:
            send_internal_email(recipient, "AI-BOS: system needs attention", body)
            sent_any = True
        except Exception:  # noqa: BLE001 - one bad send must not block the others or crash the tick
            logger.exception("stuck-alert email failed for %s", recipient)

    # Only start the cooldown once something actually sent -- if every recipient failed
    # (e.g. Resend key misconfigured), retrying next tick is more useful than going quiet.
    if sent_any:
        set_str(db, STUCK_ALERT_LAST_SENT_AT, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        logger.warning("stuck-alert sent: %d down/error process(es), %d stuck lead(s), "
                       "%d stuck job(s), %d dead job(s)",
                       len(down), len(stuck_leads), len(stuck_jobs), dead_count)


def _run_template_poll_tick(db):
    """Phase 9 Step 9.5 -- periodic real Meta status check for every PENDING template,
    so an admin-submitted template goes PENDING -> APPROVED/REJECTED (and becomes usable
    by outreach_wa_handler.py) without anyone manually clicking "refresh" on the
    dashboard. A cheap no-op query when nothing is PENDING; only calls Meta's real API
    for rows that are.
    """
    changed = poll_all_pending(db)
    if changed:
        logger.info("template poll tick -> %d template(s) changed status", changed)


def _run_engagement_escalation_tick(db):
    """Phase 9 Step 9.4 -- a lead that opens an email repeatedly but never replies is a
    real signal being wasted. Detection-only via the exact same HOT_LEAD path Step 4.3
    already built (no new UI) -- structurally can only ever fire for EMAIL, since that's
    the only channel with a real open-tracking webhook (never inferred for WhatsApp).
    """
    escalated = find_engagement_escalations(db)
    if escalated:
        logger.info("engagement escalation tick -> %d lead(s) escalated (high opens, no reply)",
                   len(escalated))


def _run_daily_plan_tick(db):
    """Phase 18 Step 18.1 -- once per IST calendar day, after 06:00: the guaranteed DAILY
    FLOOR. Every live campaign gets a fresh to-do review even if nothing changed today, and
    every active product gets checked for a real campaign-suggestion, so the AI Manager Inbox
    is never silent for days. A campaign is ALWAYS human-created (2026-09-01 revision,
    tracker.md) -- nothing in this tick ever creates one.

    Phase 21 (2026-09-05): no more manual DAILY_AI_LOOP_ENABLED switch -- the user's own
    explicit ask was "no specific time or switch, the AI should speak up whenever it judges
    something needs attention." This tick is now unconditional (still gated by the 06:00
    time-of-day + once-per-day idempotency checks below, which exist for cost/ordering
    reasons, not as a human-facing on/off toggle). See also _run_signal_driven_todo_tick()
    right below, which covers the OTHER half of that ask -- same-day, event-triggered
    regeneration the moment something real changes, riding this same scheduler loop.
    """
    now_ist = datetime.utcnow() + IST_OFFSET
    if (now_ist.hour, now_ist.minute) < (6, 0):
        return
    today_str = now_ist.strftime("%Y-%m-%d")
    if get_str(db, DAILY_PLAN_LAST_RUN_DATE, default="") == today_str:
        return  # already ran today -- idempotent, same pattern as _run_eod_report_tick

    live_campaigns = db.query(Campaign).filter(Campaign.status.in_(("PROPOSED", "APPROVED", "RUNNING"))).all()
    for campaign in live_campaigns:
        try:
            generate_campaign_todo(db, campaign.id)
        except Exception:  # noqa: BLE001 - one bad campaign must not block the rest
            logger.exception("daily plan tick: failed to refresh todo for campaign %s", campaign.id)

    products = db.query(Product).filter(Product.is_active == 1).all()
    for product in products:
        try:
            generate_campaign_suggestion(db, product.id)
        except Exception:  # noqa: BLE001
            logger.exception("daily plan tick: failed to generate suggestion for product %s", product.id)

    set_str(db, DAILY_PLAN_LAST_RUN_DATE, today_str)
    logger.info("daily plan tick complete -> %d campaign(s) refreshed, %d product(s) checked for a suggestion",
               len(live_campaigns), len(products))


# Phase 21 -- how long a signal-driven regeneration must wait before re-checking the SAME
# campaign again, even if its signal keeps changing. Pure engineering cost/spam rail (never
# a human-facing switch) -- a burst of replies must not turn into a burst of LLM calls.
_TODO_SIGNAL_COOLDOWN = timedelta(hours=2)


def _run_signal_driven_todo_tick(db):
    """Phase 21 -- the event-triggered half of "no specific time or switch": rides this
    same scheduler loop (every real poll, no gate of its own) and regenerates a SPECIFIC
    campaign's to-do the moment something concrete changed since the last time -- a new
    reply, a new hot lead, a fresh watchdog alert, or a target that's still unset -- instead
    of making a human wait for tomorrow's daily-floor tick. Cheap: reuses the exact
    compute_campaign_metrics() every other surface already calls, diffed against
    campaign.last_todo_signal (a small JSON snapshot, updated inside generate_campaign_todo
    itself every time it actually runs, from EITHER tick)."""
    live_campaigns = db.query(Campaign).filter(Campaign.status.in_(("PROPOSED", "APPROVED", "RUNNING"))).all()
    now = datetime.utcnow()
    for campaign in live_campaigns:
        try:
            current_signal = todo_signal_fingerprint(db, campaign)
            last_signal = json.loads(campaign.last_todo_signal) if campaign.last_todo_signal else None
            if current_signal == last_signal:
                continue
            # Same-day human-review cues (Draft status, first leads arriving) must not wait
            # out the spam cooldown -- that was the "kal wait kyun" gap. Cooldown still
            # applies to ordinary metric noise (opens/replies churn).
            urgent_keys = ("campaign_status", "tagged_lead_count")
            urgent_change = last_signal is None or any(
                current_signal.get(k) != last_signal.get(k) for k in urgent_keys
            )
            most_recent_item = (
                db.query(TodoItem)
                .filter(TodoItem.campaign_id == campaign.id)
                .order_by(TodoItem.created_at.desc())
                .first()
            )
            if (not urgent_change) and most_recent_item and most_recent_item.created_at and \
                    now - most_recent_item.created_at < _TODO_SIGNAL_COOLDOWN:
                continue  # cooldown -- a burst of replies must not become a burst of LLM calls
            generate_campaign_todo(db, campaign.id)
            logger.info("signal-driven todo tick -> campaign %s regenerated (signal changed)", campaign.id)
        except Exception:  # noqa: BLE001 - one bad campaign must not block the rest
            logger.exception("signal-driven todo tick: failed for campaign %s", campaign.id)


def _run_strategy_reflection_tick(db):
    """Phase 19 Step 19.1-19.3 -- once per IST calendar day, after 07:00 (after the daily
    plan tick's own 06:00 gate, so a fresh day's telemetry reflects yesterday's approved
    changes before reflection runs against it -- not load-bearing, just sane ordering).
    Gated by STRATEGY_REFLECTION_ENABLED (default off), same fail-safe posture as
    DAILY_AI_LOOP_ENABLED -- run_reflection_cycle() itself also checks this and is a safe
    no-op either way, this tick-level check just avoids the idempotency bookkeeping when
    the feature is off."""
    if not get_bool(db, STRATEGY_REFLECTION_ENABLED, default=False):
        return

    now_ist = datetime.utcnow() + IST_OFFSET
    if (now_ist.hour, now_ist.minute) < (7, 0):
        return
    today_str = now_ist.strftime("%Y-%m-%d")
    if get_str(db, STRATEGY_REFLECTION_LAST_RUN_DATE, default="") == today_str:
        return  # already ran today -- idempotent, same pattern as _run_daily_plan_tick

    try:
        result = run_reflection_cycle(db)
        logger.info("strategy reflection tick complete -> %s", result)
    except Exception:  # noqa: BLE001 - one bad cycle must not crash the scheduler
        logger.exception("strategy reflection tick failed")
    set_str(db, STRATEGY_REFLECTION_LAST_RUN_DATE, today_str)


def run_forever(poll_interval=None):
    poll_interval = poll_interval or Config.SCHEDULER_POLL_INTERVAL_SECONDS
    last_outreach_tick = 0.0
    logger.info("discovery scheduler started (poll=%ds, outreach tick every %ds)",
               poll_interval, Config.OUTREACH_TICK_INTERVAL_SECONDS)

    # 300s by default -- far slower than the other processes, which is exactly why the
    # expected interval is stored per process instead of assumed globally.
    beat_standalone(HEARTBEAT_NAME, status="RUNNING", is_startup=True,
                    expected_interval_seconds=poll_interval)

    while True:
        db = SessionLocal()
        tick_status = "RUNNING"
        try:
            _run_discovery_tick(db)
            now = time.monotonic()
            if now - last_outreach_tick >= Config.OUTREACH_TICK_INTERVAL_SECONDS:
                _run_outreach_tick(db)
                _run_followup_tick(db)
                last_outreach_tick = now
            _run_eod_report_tick(db)
            _run_stuck_alert_tick(db)
            _run_template_poll_tick(db)
            _run_engagement_escalation_tick(db)
            _run_daily_plan_tick(db)
            _run_signal_driven_todo_tick(db)
            _run_strategy_reflection_tick(db)
        except Exception:  # noqa: BLE001 - one bad tick must not kill the scheduler
            logger.exception("scheduler tick failed")
            # Surface a failing tick to the monitor instead of only to the log -- a scheduler
            # that is alive but erroring every tick looks identical to a healthy one if the
            # heartbeat only ever reports RUNNING.
            tick_status = "ERROR"
        finally:
            # Inside the try/finally so a failed tick still beats -- the process IS alive, and
            # reporting it as stale would be wrong (and would mask the real ERROR status).
            beat(db, HEARTBEAT_NAME, status=tick_status,
                 force=(tick_status == "ERROR"),
                 expected_interval_seconds=poll_interval)
            db.close()
        time.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_forever()
