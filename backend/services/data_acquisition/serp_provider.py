import logging
import re
from urllib.parse import urlparse

import requests

from config import Config
from services.data_acquisition.base import LeadSourceProvider, empty_lead

logger = logging.getLogger(__name__)

SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_SEARCH_URL = "https://google.serper.dev/search"

# Sites that rank for a business name but are never the business's own site. Picking one
# of these as `website_url` would send enrichment scraping a directory's contact page and
# harvest the directory's email instead of the lead's.
DIRECTORY_DOMAINS = {
    "instagram.com", "facebook.com", "m.facebook.com", "twitter.com", "x.com",
    "youtube.com", "linkedin.com", "pinterest.com", "threads.net", "whatsapp.com",
    "justdial.com", "sulekha.com", "indiamart.com", "tradeindia.com", "yelp.com",
    "tripadvisor.com", "tripadvisor.in", "zomato.com", "swiggy.com", "magicpin.in",
    "nearbuy.com", "district.in", "bookmyshow.com", "insider.in", "eventbrite.com",
    "google.com", "maps.google.com", "goo.gl", "wikipedia.org", "quora.com",
    "ambitionbox.com", "glassdoor.co.in", "yellowpages.in", "grotal.com",
}


def _root_domain(url):
    netloc = urlparse(url).netloc.lower()
    return netloc.removeprefix("www.").split(":")[0]


def _is_directory(url):
    root = _root_domain(url)
    return any(root == d or root.endswith(f".{d}") for d in DIRECTORY_DOMAINS)


def _name_tokens(company_name):
    """'Fun Blast - SBR | Trampoline Park' -> {'funblast', 'fun', 'blast', 'sbr', ...}"""
    words = [w for w in re.split(r"[^a-z0-9]+", (company_name or "").lower()) if len(w) > 2]
    tokens = set(words)
    if len(words) >= 2:
        tokens.add("".join(words[:2]))   # 'funblast' matches funblast.co
    return tokens


class SerperProvider(LeadSourceProvider):
    """Company discovery via Serper.dev's Google Places search -- returns real
    business listings (name, website, phone, address), not raw web-search links."""

    def __init__(self, api_key=None, timeout=15):
        self.api_key = api_key or Config.SERPER_API_KEY
        self.timeout = timeout

    def discover(self, query, location=None):
        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY not configured")

        search_query = f"{query} in {location}" if location else query
        resp = requests.post(
            SERPER_PLACES_URL,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": search_query},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        return [
            empty_lead(
                company_name=place.get("title"),
                website_url=place.get("website"),
                primary_phone=place.get("phoneNumber"),
                region_location=place.get("address"),
                source="SERPER_PLACES",
                # carried through, not stored on `leads` -- the review agent (Step 2.4)
                # writes rating/review count into lead_review_insights, and `cid` is the
                # Google Maps id needed to pull the actual review text later
                rating=place.get("rating"),
                rating_count=place.get("ratingCount"),
                category=place.get("category"),
                google_cid=place.get("cid"),
            )
            for place in data.get("places", [])
        ]

    def find_website(self, company_name, location=None):
        """Recover a company's own website via regular web search.

        Google's local pack often carries no website at all -- verified stable, not
        flaky: the same Ahmedabad gaming-zone query returned 0/10 websites on three
        consecutive runs. This is the `Places -> SerpAPI` fallback tier the build spec
        calls for. Costs one extra Serper credit per lead, so callers decide when it's
        worth spending.

        Returns a URL only when the domain plausibly belongs to the company; returns
        None rather than guessing, since a wrong site poisons every downstream step.
        """
        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY not configured")

        query = f"{company_name} {location}".strip() if location else company_name
        resp = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "in", "num": 10},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # Google's own knowledge panel is the strongest signal when present
        kg_site = (data.get("knowledgeGraph") or {}).get("website")
        if kg_site and not _is_directory(kg_site):
            logger.info("find_website %s -> %s (knowledge graph)", company_name, kg_site)
            return kg_site

        tokens = _name_tokens(company_name)
        for result in data.get("organic", []):
            link = result.get("link")
            if not link or _is_directory(link):
                continue
            root = _root_domain(link)
            stem = root.split(".")[0]
            # accept only when the domain echoes the business name -- otherwise a
            # blog post about the company would be stored as the company's site
            if stem in tokens or any(t in stem for t in tokens if len(t) > 3):
                url = f"https://{root}/"
                logger.info("find_website %s -> %s (organic)", company_name, url)
                return url

        logger.info("find_website %s -> nothing confident enough", company_name)
        return None
