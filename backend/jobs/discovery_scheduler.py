"""Discovery scheduler (tracker.md A.2) -- replaces n8n entirely for Step 3.5. A small
dedicated always-on process (same "one process per concern" pattern as scraper_worker/
async_runner.py vs jobs/worker.py -- MASTER §9 process topology), owns two jobs:

1. Autonomous discovery targeting: keep each active product's ICP Strategy fresh (via
   agents/icp_strategy_agent.py) and fire paced DISCOVER jobs across
   search_queries x target_regions -- no human types a city/keyword combo in daily.
2. Outreach pacing tick: claim SCORED leads for outreach up to the daily per-channel cap,
   staggered via run_after so a day's worth of sends doesn't burst all at once (the
   "pacing caps" item flagged open under DoD Gate P3).

Run as `python -m jobs.discovery_scheduler`, alongside (not instead of) jobs/worker.py and
scraper_worker/async_runner.py.
"""
import json
import logging
import time
from datetime import datetime, timedelta

from sqlalchemy import text

from config import Config
from database.db_config import SessionLocal
from database.models import Product, ProductStrategy, DiscoveryRun, Lead, LeadScore
from jobs.job_queue import enqueue
from agents.icp_strategy_agent import generate_strategy
from services.lead_service import claim_lead_for_outreach

logger = logging.getLogger(__name__)


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
    same search isn't repeated needlessly (and so API budget isn't burned in one burst)."""
    fired = 0
    for product in db.query(Product).filter(Product.is_active == 1).all():
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
                if run and datetime.utcnow() - run.last_run_at < timedelta(hours=Config.DISCOVERY_COOLDOWN_HOURS):
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
    staggering each claimed lead's run_after so sends trickle out instead of bursting."""
    remaining = {
        "EMAIL": Config.OUTREACH_DAILY_CAP_EMAIL - _queued_today(db, "OUTREACH_EMAIL"),
        "WHATSAPP": Config.OUTREACH_DAILY_CAP_WHATSAPP - _queued_today(db, "OUTREACH_WA"),
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


def run_forever(poll_interval=None):
    poll_interval = poll_interval or Config.SCHEDULER_POLL_INTERVAL_SECONDS
    last_outreach_tick = 0.0
    logger.info("discovery scheduler started (poll=%ds, outreach tick every %ds)",
               poll_interval, Config.OUTREACH_TICK_INTERVAL_SECONDS)

    while True:
        db = SessionLocal()
        try:
            _run_discovery_tick(db)
            now = time.monotonic()
            if now - last_outreach_tick >= Config.OUTREACH_TICK_INTERVAL_SECONDS:
                _run_outreach_tick(db)
                last_outreach_tick = now
        except Exception:  # noqa: BLE001 - one bad tick must not kill the scheduler
            logger.exception("scheduler tick failed")
        finally:
            db.close()
        time.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_forever()
