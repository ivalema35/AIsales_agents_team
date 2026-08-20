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
from database.models import Product, ProductStrategy, DiscoveryRun, Lead, LeadScore, DailyReport
from jobs.job_queue import enqueue
from agents.icp_strategy_agent import generate_strategy
from services.lead_service import claim_lead_for_outreach
from services.reporting_service import generate as generate_eod_report, IST_OFFSET
from services.system_settings import (
    get_bool, get_int, get_str, set_str, DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED,
    OUTREACH_DAILY_CAP_EMAIL, OUTREACH_DAILY_CAP_WHATSAPP, DISCOVERY_COOLDOWN_HOURS,
    STUCK_ALERT_ENABLED, STUCK_ALERT_COOLDOWN_MINUTES, STUCK_ALERT_LAST_SENT_AT,
    EOD_REPORT_RECIPIENTS)
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
    """Fires at most MAX_DISCOVER_PER_TICK DISCOVER jobs this tick, oldest-due
    (product, query, region) combo first, respecting each combo's own cooldown so the
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

        regions = json.loads(product.target_regions or "[]")
        if not regions:
            continue  # nothing to do until the user sets at least one region for this product

        _refresh_strategy_if_stale(db, product)
        queries, _ = _active_strategy_queries(db, product.id)

        for query in queries:
            if fired >= Config.MAX_DISCOVER_PER_TICK:
                break
            for region in regions:
                if fired >= Config.MAX_DISCOVER_PER_TICK:
                    break

                run = db.query(DiscoveryRun).filter(
                    DiscoveryRun.product_id == product.id,
                    DiscoveryRun.query == query,
                    DiscoveryRun.region == region,
                ).first()
                if run and datetime.utcnow() - run.last_run_at < timedelta(hours=cooldown_hours):
                    continue

                enqueue(db, "DISCOVER", {"product_id": product.id, "query": query, "location": region})
                if run:
                    run.last_run_at = datetime.utcnow()
                else:
                    db.add(DiscoveryRun(product_id=product.id, query=query, region=region))
                db.commit()
                fired += 1
                logger.info("DISCOVER queued: product=%s query=%r region=%s", product.title, query, region)

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

    claimed_count = 0
    for lead in candidates:
        if remaining["EMAIL"] <= 0 and remaining["WHATSAPP"] <= 0:
            break
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


def run_forever(poll_interval=None):
    poll_interval = poll_interval or Config.SCHEDULER_POLL_INTERVAL_SECONDS
    last_outreach_tick = 0.0
    logger.info("discovery scheduler started (poll=%ds, outreach tick every %ds)",
               poll_interval, Config.OUTREACH_TICK_INTERVAL_SECONDS)

    # 300s by default -- far slower than the other processes, which is exactly why the
    # expected interval is stored per process instead of assumed globally.
    beat_standalone(HEARTBEAT_NAME, status="RUNNING", force=True,
                    expected_interval_seconds=poll_interval)

    while True:
        db = SessionLocal()
        tick_status = "RUNNING"
        try:
            _run_discovery_tick(db)
            now = time.monotonic()
            if now - last_outreach_tick >= Config.OUTREACH_TICK_INTERVAL_SECONDS:
                _run_outreach_tick(db)
                last_outreach_tick = now
            _run_eod_report_tick(db)
            _run_stuck_alert_tick(db)
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
