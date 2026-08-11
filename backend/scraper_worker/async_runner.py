"""Dedicated async scraper process -- one process, one asyncio loop, a semaphore cap.

Runs SEPARATELY from jobs/worker.py (`python -m scraper_worker.async_runner`). The two
never share a process: this one is I/O-bound and fans out concurrently, the job worker
is sequential and owns pacing. Keeping them apart is what stops scraper stalls from
blocking outreach pacing and vice versa (MASTER §9 process topology).

Handles DISCOVER and ENRICH. REVIEW stays PENDING until Step 2.4 registers its handler
-- the queue tolerates a job type with no handler by design.
"""
import asyncio
import json
import logging
import uuid
from urllib.parse import urlparse

from database.db_config import SessionLocal
from database.models import Lead
from jobs.job_queue import enqueue, claim_next, mark_done, mark_failed
from services.data_acquisition.serp_provider import SerperProvider
from services.data_acquisition.b2b_provider import HunterProvider
from services.data_acquisition.website_scraper import (
    scrape_emails,
    rank_candidates,
    is_role_account,
)

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 5
POLL_INTERVAL = 3


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


def _handle_enrich(db, payload):
    """Website scrape (free) + Hunter (paid) -> best contact onto the lead -> ENRICHED.

    Website first, deliberately: Hunter's domain-search can only return `@thatdomain`
    addresses, so an SMB whose real contact is a gmail address comes back empty from it.
    In live testing 2 of 4 sampled companies had NO domain email at all and would have
    ended up uncontactable -- their real address was sitting in their own site footer.

    A lead with no website (common for small businesses) still advances to ENRICHED
    rather than failing, so it isn't stranded out of the pipeline; scoring downstream
    just sees no contact and weighs reachability accordingly.
    """
    lead = db.get(Lead, payload["lead_id"])
    if not lead:
        raise ValueError(f"lead {payload['lead_id']} not found")

    domain = extract_domain(lead.website_url)

    # Google's local pack frequently carries no website at all (verified stable, not
    # flaky: an Ahmedabad gaming-zone search returned 0/10 websites three runs running).
    # Without this recovery step those leads would skip contact discovery entirely, since
    # both the website scrape and Hunter need a domain to work from.
    if not domain:
        recovered = SerperProvider().find_website(lead.company_name, lead.region_location)
        if recovered:
            lead.website_url = recovered
            db.commit()
            domain = extract_domain(recovered)
            logger.info("ENRICH %s -> recovered website %s", lead.company_name, recovered)

    if not domain:
        logger.info("ENRICH %s -> no usable domain, skipping contact lookup", lead.company_name)
        lead.status = "ENRICHED"
        db.commit()
        enqueue(db, "REVIEW", {"lead_id": lead.id})
        return lead.id

    website_emails = scrape_emails(domain)

    # Hunter is the paid, quota-limited source (25/month on the free plan) -- skip the
    # call entirely when the free scrape already found a named (non-role) address, since
    # Hunter can't improve on that. Still call it when we only have info@/admin@, because
    # a named decision-maker is worth the credit.
    hunter_contacts = []
    only_role_accounts = all(is_role_account(e) for e in website_emails)
    if not website_emails or only_role_accounts:
        try:
            hunter_contacts = HunterProvider().enrich_domain(domain)
        except Exception as exc:  # noqa: BLE001 - quota/network failure must not lose the free result
            logger.warning("Hunter lookup failed for %s: %s", domain, exc)

    candidates = rank_candidates(website_emails, hunter_contacts, domain=domain)

    if candidates:
        best = candidates[0]
        lead.primary_email = best["email"]
        full_name = " ".join(p for p in (best.get("first_name"), best.get("last_name")) if p)
        # only overwrite with something we actually know -- never invent a contact name
        if full_name:
            lead.contact_person_name = full_name
        if best.get("position"):
            lead.contact_person_role = best["position"]
        logger.info(
            "ENRICH %s (%s) -> %s [%s] (%d candidates: %s)",
            lead.company_name, domain, best["email"], best["source"],
            len(candidates), [c["email"] for c in candidates],
        )
    else:
        logger.info("ENRICH %s (%s) -> no contacts found", lead.company_name, domain)

    lead.status = "ENRICHED"
    db.commit()

    enqueue(db, "REVIEW", {"lead_id": lead.id})
    return lead.id


HANDLERS = {
    "DISCOVER": _handle_discover,
    "ENRICH": _handle_enrich,
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
