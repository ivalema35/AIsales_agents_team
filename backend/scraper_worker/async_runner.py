"""Dedicated async scraper process -- one process, one asyncio loop, a semaphore cap.

Runs SEPARATELY from jobs/worker.py (`python -m scraper_worker.async_runner`). The two
never share a process: this one is I/O-bound and fans out concurrently, the job worker
is sequential and owns pacing. Keeping them apart is what stops scraper stalls from
blocking outreach pacing and vice versa (MASTER §9 process topology).

Handles DISCOVER, ENRICH, REVIEW, and SCORE -- REVIEW/SCORE are the first two job types
in this whole project that make an LLM call.
"""
import asyncio
import json
import logging
import uuid
from urllib.parse import urlparse

from database.db_config import SessionLocal
from database.models import Lead, Product, LeadReviewInsight, LeadScore
from jobs.job_queue import enqueue, claim_next, mark_done, mark_failed
from services.data_acquisition.serp_provider import SerperProvider
from services.data_acquisition.b2b_provider import HunterProvider
from services.data_acquisition.website_scraper import (
    scrape_emails,
    scrape_phones,
    rank_candidates,
    is_role_account,
)
from services.data_acquisition.maps_scraper import MapsPhoneCircuitBreaker
from agents.review_analyst_agent import analyze_reviews
from agents.scoring_agent import score_lead

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 5
POLL_INTERVAL = 3

# Shared across the whole runner process (not per-lead) -- that's the entire point of a
# circuit breaker: it tracks consecutive failures and a batch cap across every ENRICH
# job this run processes, not just one. Thread-safe internally (see maps_scraper.py).
_maps_breaker = MapsPhoneCircuitBreaker()


def extract_domain(website_url):
    """example: 'https://www.foo.co.in/about' -> 'foo.co.in'. None if unusable."""
    if not website_url:
        return None
    netloc = urlparse(website_url).netloc or urlparse(f"//{website_url}").netloc
    if not netloc:
        return None
    return netloc.split(":")[0].removeprefix("www.") or None


def _handle_discover(db, payload):
    """Serper search -> new lead rows -> one ENRICH job each.

    Dedupes on (product_id, company_name): a repeated search for the same area is the
    normal case, not an error, and must not fan out duplicate leads or duplicate ENRICH
    jobs (each of which would burn a Hunter credit).
    """
    product_id = payload["product_id"]
    query = payload["query"]
    location = payload.get("location")

    results = SerperProvider().discover(query, location=location)

    created = 0
    for row in results:
        if not row.get("company_name"):
            continue
        exists = db.query(Lead).filter(
            Lead.product_id == product_id,
            Lead.company_name == row["company_name"],
        ).first()
        if exists:
            continue

        lead = Lead(
            id=str(uuid.uuid4()),
            product_id=product_id,
            company_name=row["company_name"],
            website_url=row.get("website_url"),
            primary_phone=row.get("primary_phone"),
            region_location=row.get("region_location"),
            source=row.get("source"),
            status="DISCOVERED",
        )
        db.add(lead)
        db.commit()
        created += 1

        enqueue(db, "ENRICH", {"lead_id": lead.id})

    logger.info("DISCOVER '%s' -> %d results, %d new leads", query, len(results), created)
    return created


def _enrich_email(db, lead, domain):
    """Waterfall, cheapest/most-trustworthy first:
    1. company's own website (free)
    2. Hunter domain-search (paid, 50/month) -- only when the free scrape found nothing
       or only a role account, since Hunter can't improve on a named website contact
    3. Serper search-snippet recovery (1 credit) -- last resort, covers both "has a
       domain but nothing crawlable on it" and "no domain at all" (Instagram/FB-only)

    Website-first is deliberate: Hunter's domain-search can only return `@thatdomain`
    addresses, so an SMB whose real contact is a gmail address comes back empty from it.
    In live testing 2 of 4 sampled companies had NO domain email at all and would have
    ended up uncontactable -- their real address was sitting in their own site footer.
    """
    website_emails = scrape_emails(domain) if domain else []

    hunter_contacts = []
    only_role_accounts = website_emails and all(is_role_account(e) for e in website_emails)
    if domain and (not website_emails or only_role_accounts):
        try:
            hunter_contacts = HunterProvider().enrich_domain(domain)
        except Exception as exc:  # noqa: BLE001 - quota/network failure must not lose the free result
            logger.warning("Hunter lookup failed for %s: %s", domain, exc)

    candidates = rank_candidates(website_emails, hunter_contacts, domain=domain)
    if candidates:
        return candidates[0]

    try:
        found = SerperProvider().find_email(lead.company_name, lead.region_location, domain=domain)
    except Exception as exc:  # noqa: BLE001 - last-resort lookup failing must not fail the job
        logger.warning("find_email failed for %s: %s", lead.company_name, exc)
        found = None

    if found:
        return {"email": found, "source": "SERPER_SNIPPET", "first_name": None,
                "last_name": None, "position": None}
    return None


def _enrich_phone(db, lead, domain):
    """Waterfall, cheapest/least-risky first:
    1. company's own website tel:/wa.me links (free)
    2. Serper search-snippet recovery (1 credit) -- Places' own phone field is
       frequently empty for smaller businesses (verified stable, not flaky)
    3. Google Maps detail-panel read via the shared circuit breaker (last resort --
       closer to a ToS risk than the other two, so batch-capped and rate-limited)
    """
    website_phones = scrape_phones(domain) if domain else []
    if website_phones:
        return website_phones[0]["phone"]

    try:
        found = SerperProvider().find_phone(lead.company_name, lead.region_location, domain=domain)
    except Exception as exc:  # noqa: BLE001
        logger.warning("find_phone failed for %s: %s", lead.company_name, exc)
        found = None
    if found:
        return found

    try:
        # _handle_enrich runs inside a worker thread (via asyncio.to_thread), which has
        # no event loop of its own -- asyncio.run() here is safe and scoped to this call.
        return asyncio.run(_maps_breaker.find_phone(lead.company_name, lead.region_location))
    except Exception as exc:  # noqa: BLE001 - Maps failing must not fail the ENRICH job
        logger.warning("maps phone fallback failed for %s: %s", lead.company_name, exc)
        return None


def _handle_enrich(db, payload):
    """Full contact-enrichment waterfall -> best email + phone onto the lead -> ENRICHED.

    A lead with no website and nothing recoverable anywhere still advances to ENRICHED
    rather than failing, so it isn't stranded out of the pipeline; scoring downstream
    just sees no contact and weighs reachability accordingly.
    """
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    domain = extract_domain(lead.website_url)

    # Google's local pack frequently carries no website at all (verified stable, not
    # flaky: an Ahmedabad gaming-zone search returned 0/10 websites three runs running).
    if not domain:
        recovered = SerperProvider().find_website(lead.company_name, lead.region_location)
        if recovered:
            lead.website_url = recovered
            db.commit()
            domain = extract_domain(recovered)
            logger.info("ENRICH %s -> recovered website %s", lead.company_name, recovered)

    if not lead.primary_email:
        best_email = _enrich_email(db, lead, domain)
        if best_email:
            lead.primary_email = best_email["email"]
            full_name = " ".join(p for p in (best_email.get("first_name"), best_email.get("last_name")) if p)
            # only overwrite with something we actually know -- never invent a contact name
            if full_name:
                lead.contact_person_name = full_name
            if best_email.get("position"):
                lead.contact_person_role = best_email["position"]
            logger.info("ENRICH %s -> email %s [%s]", lead.company_name,
                       best_email["email"], best_email["source"])

    # Serper Places sometimes already supplied a phone at DISCOVER time -- don't
    # re-spend credits/Maps attempts re-deriving something we already have.
    if not lead.primary_phone:
        best_phone = _enrich_phone(db, lead, domain)
        if best_phone:
            lead.primary_phone = best_phone
            logger.info("ENRICH %s -> phone %s", lead.company_name, best_phone)

    if not lead.primary_email and not lead.primary_phone:
        logger.info("ENRICH %s (%s) -> no contacts found anywhere", lead.company_name, domain)

    lead.status = "ENRICHED"
    db.commit()

    enqueue(db, "REVIEW", {"lead_id": lead.id})
    return lead.id


def _handle_review(db, payload):
    """Serper snippet search -> Review Analyst LLM -> weakness codes -> lead_review_insights.

    Always advances to SCORE regardless of what (if anything) was found -- graceful
    degradation was the explicit design decision here (confirmed with the user after
    live-testing showed real review text is only reliably available for roughly 1 in 3
    businesses): a lead with zero pain points found is not a failure, it just scores
    without that signal.
    """
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    snippets = SerperProvider().find_review_signals(lead.company_name, lead.region_location)
    result, outcome = analyze_reviews(db, lead.id, lead.company_name, snippets)

    db.add(LeadReviewInsight(
        id=str(uuid.uuid4()),
        lead_id=lead.id,
        review_source="SERPER_SNIPPETS" if snippets else "NONE_FOUND",
        pain_points_extracted=json.dumps(result["pain_points"]),
        sentiment_score=result["sentiment_score"],
        raw_review_snippets=json.dumps(snippets),
    ))

    lead.status = "REVIEWED"
    db.commit()

    logger.info("REVIEW %s -> %d pain point(s) (confidence=%.2f, snippets=%d, outcome=%s)",
               lead.company_name, len(result["pain_points"]), result["confidence"],
               len(snippets), outcome)

    enqueue(db, "SCORE", {"lead_id": lead.id})
    return lead.id


def _handle_score(db, payload):
    """Scoring Agent -> lead_scores row -> status SCORED.

    Upserts rather than always inserting: lead_scores.lead_id is UNIQUE, and a job retry
    re-running this handler after a partial earlier success must not crash on that
    constraint.
    """
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    product = db.get(Product, lead.product_id)
    if not product:
        raise ValueError(f"product {lead.product_id} not found for lead {lead.id}")

    insight = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.lead_id == lead.id)
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []

    product_brief = {
        "title": product.title,
        "description": product.description,
        "target_keywords": json.loads(product.target_keywords or "[]"),
        "value_proposition": product.value_proposition,
    }
    lead_profile = {
        "company_name": lead.company_name,
        "region_location": lead.region_location,
        "has_email": bool(lead.primary_email),
        "has_phone": bool(lead.primary_phone),
    }

    result, route = score_lead(db, lead.id, product_brief, lead_profile, pain_points)

    existing = db.query(LeadScore).filter(LeadScore.lead_id == lead.id).first()
    if existing:
        existing.score = result["score"]
        existing.tier = result["tier"]
        existing.confidence = result["confidence"]
        existing.scoring_breakdown = json.dumps(result["scoring_breakdown"])
        existing.justification = result["justification"]
    else:
        db.add(LeadScore(
            id=str(uuid.uuid4()),
            lead_id=lead.id,
            score=result["score"],
            tier=result["tier"],
            confidence=result["confidence"],
            scoring_breakdown=json.dumps(result["scoring_breakdown"]),
            justification=result["justification"],
        ))

    lead.status = "SCORED"
    db.commit()

    logger.info("SCORE %s -> %d (%s), confidence=%.2f, route=%s",
               lead.company_name, result["score"], result["tier"], result["confidence"], route)
    return lead.id


HANDLERS = {
    "DISCOVER": _handle_discover,
    "ENRICH": _handle_enrich,
    "REVIEW": _handle_review,
    "SCORE": _handle_score,
}


def _process_claimed_job(job_type, job_id, payload):
    """Sync unit of work -- runs in a thread so the provider's blocking HTTP call never
    stalls the event loop. Owns its own session: sessions are not thread-safe."""
    db = SessionLocal()
    try:
        try:
            HANDLERS[job_type](db, payload)
            mark_done(db, job_id)
        except Exception as exc:  # noqa: BLE001 - one bad lead must not kill the runner
            logger.exception("job %s (%s) failed", job_id, job_type)
            mark_failed(db, job_id, str(exc))
    finally:
        db.close()


async def _run_one(job_type, semaphore):
    """Claim atomically, then process off-loop. Returns True if a job was claimed."""
    async with semaphore:
        db = SessionLocal()
        try:
            job_id = claim_next(db, job_type)
            if not job_id:
                return False
            from database.models import Job
            payload = json.loads(db.get(Job, job_id).payload)
        finally:
            db.close()

        await asyncio.to_thread(_process_claimed_job, job_type, job_id, payload)
        return True


async def run_forever(job_types=None, poll_interval=POLL_INTERVAL):
    job_types = job_types or list(HANDLERS.keys())
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    logger.info("scraper runner started (concurrency=%d, types=%s)", MAX_CONCURRENCY, job_types)

    while True:
        results = await asyncio.gather(
            *(_run_one(jt, semaphore) for jt in job_types for _ in range(MAX_CONCURRENCY))
        )
        if not any(results):
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_forever())
