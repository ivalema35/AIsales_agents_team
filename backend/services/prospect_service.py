"""Phase 15 Step 15(B) -- standalone, criteria-driven prospect discovery. Real spend is
tracked per search run (prospect_searches.spend, from the admin-configured cost-per-
search) and checked BEFORE every new search -- a configured monthly budget genuinely
blocks the next run, never just warns after spend already happened (MASTER_DEVELOPMENT_
PRD.md Phase 15 Step 15(B).2's own DoD line, learned the hard way from Hunter's free
quota running out mid-verification, tracker.md Phase 7).
"""
from __future__ import annotations
import logging

from sqlalchemy import text

from config import Config
from database.models import Prospect, ProspectSearch
from services.data_acquisition.b2b_provider import HunterProvider
from services.data_acquisition.serp_provider import SerperProvider
from services.data_acquisition.website_scraper import domain_from_url, scrape_emails
from services.system_settings import (
    PROSPECT_SEARCH_COST_PER_SEARCH, PROSPECT_SEARCH_MONTHLY_BUDGET, get_float)

logger = logging.getLogger(__name__)


class ProspectSearchBlocked(Exception):
    """Raised when running this search would exceed the configured monthly budget -- a
    real, hard refusal. Step 15(B).2's own DoD requires this be distinguishable from a
    real search that simply found nobody, so a blocked search never returns an empty
    result -- it never runs at all."""


def _current_month_spend(db) -> float:
    row = db.execute(text(
        "SELECT COALESCE(SUM(spend), 0.0) FROM prospect_searches "
        "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
    )).fetchone()
    return float(row[0] or 0.0)


def run_prospect_search(db, criteria_text, role_keywords, location=None, extra_keywords=None,
                        max_results=10) -> ProspectSearch:
    """Real spend check BEFORE the real Serper call -- a search that would exceed the
    monthly budget never happens at all. Deduplicates against every prospect ever found
    (by linkedin_url), across every past search, not just this run -- the same real
    person found again is never a new row."""
    if not Config.SERPER_API_KEY:
        raise RuntimeError("SERPER_API_KEY not configured -- no provider available for prospect search")

    budget = get_float(db, PROSPECT_SEARCH_MONTHLY_BUDGET, default=0.0)
    cost_per_search = get_float(db, PROSPECT_SEARCH_COST_PER_SEARCH, default=0.01)
    spent = _current_month_spend(db)
    if spent + cost_per_search > budget:
        raise ProspectSearchBlocked(
            f"Monthly prospect-search budget would be exceeded (spent so far this month: "
            f"{spent:.2f}, budget: {budget:.2f}, this search costs: {cost_per_search:.2f}). "
            f"Raise the budget in Settings to run more searches this month."
        )

    results = SerperProvider().find_prospects_by_criteria(
        role_keywords, location=location, extra_keywords=extra_keywords, max_results=max_results)

    search = ProspectSearch(
        criteria_text=criteria_text,
        role_keywords=", ".join(role_keywords),
        location=location,
        provider="SERPER_XRAY",
        result_count=len(results),
        spend=cost_per_search,
    )
    db.add(search)
    db.flush()  # need search.id before creating the Prospect rows below

    saved = 0
    for r in results:
        if db.query(Prospect).filter(Prospect.linkedin_url == r["linkedin_url"]).first():
            continue
        db.add(Prospect(
            search_id=search.id,
            full_name=r.get("full_name"),
            headline=r.get("headline"),
            linkedin_url=r["linkedin_url"],
            current_company=r.get("current_company"),
            location_text=location,
            source="SERPER_XRAY",
            confidence=r.get("confidence"),
        ))
        saved += 1

    db.commit()
    logger.info("PROSPECT_SEARCH '%s' -> %d found, %d new (this run's spend: %.2f)",
               criteria_text, len(results), saved, cost_per_search)
    return search


def enrich_prospect_contact(db, prospect: Prospect) -> Prospect:
    """Step 15(B).3 -- reuses the SAME real enrichment waterfall Phase 2/7 already use
    for companies (find_website -> Hunter domain-search -> website scraping), never a
    parallel path. A prospect with no current_company has nothing to resolve a domain
    from and is left NO_CONTACT_FOUND, not guessed at."""
    if not prospect.current_company:
        prospect.enrichment_status = "NO_CONTACT_FOUND"
        db.commit()
        return prospect

    website = SerperProvider().find_website(prospect.current_company, prospect.location_text)
    domain = domain_from_url(website) if website else None
    if not domain:
        prospect.enrichment_status = "NO_CONTACT_FOUND"
        db.commit()
        return prospect

    matched_email = None
    if Config.HUNTER_API_KEY:
        try:
            for contact in HunterProvider().enrich_domain(domain):
                full = f"{contact.get('first_name') or ''} {contact.get('last_name') or ''}".strip()
                if full and prospect.full_name and full.lower() == prospect.full_name.lower():
                    matched_email = contact.get("email")
                    break
        except Exception:  # noqa: BLE001 -- Hunter being unavailable must not fail enrichment
            logger.warning("Hunter domain-search failed for %s", domain, exc_info=True)

    if not matched_email and prospect.full_name:
        # Tier 2 fallback: a firstname.lastname@domain pattern match against real,
        # already-scraped website emails -- never a synthesized/guessed address.
        try:
            scraped = scrape_emails(domain)
        except Exception:  # noqa: BLE001
            scraped = []
        name_parts = prospect.full_name.lower().split()
        if len(name_parts) >= 2 and scraped:
            first, last = name_parts[0], name_parts[-1]
            for email in scraped:
                local = email.split("@")[0].lower()
                if first in local and last in local:
                    matched_email = email
                    break

    prospect.email = matched_email
    prospect.enrichment_status = "ENRICHED" if matched_email else "NO_CONTACT_FOUND"
    db.commit()
    return prospect
