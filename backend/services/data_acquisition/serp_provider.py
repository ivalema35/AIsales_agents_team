import logging
import re
from urllib.parse import urlparse

import requests

from config import Config
from services.data_acquisition.base import LeadSourceProvider, empty_lead
from services.data_acquisition.website_scraper import (
    normalize_mobile,
    EMAIL_RE,
    is_valid_contact_email,
    belongs_to_company,
    TEXT_MOBILE_RE as MOBILE_RE,  # reuse the one fixed pattern, don't fork a second copy
)

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


def _name_matches_blob(company_name, blob):
    """True if the business's own name is actually present in this result -- a raw
    substring check (spaces/punctuation stripped) on the first 1-2 significant words,
    not loose token overlap.

    This exists because plain majority-vote over phone numbers found in search results
    is exploitable by coincidence: for "Infinity Gaming Zone PS5", two DIFFERENT
    competing businesses' promo reels both mentioned the same number and outvoted the
    one snippet that was actually Infinity Gaming Zone's own Instagram bio. Loose token
    overlap (e.g. matching on "gaming" or "zone" alone) doesn't fix this -- those words
    are the category, not the business -- so this requires the name's own word(s) to
    appear as a contiguous chunk.
    """
    words = [w for w in re.split(r"[^a-z0-9]+", (company_name or "").lower()) if len(w) > 2]
    if not words:
        return False
    needle = "".join(words[:2])
    haystack = re.sub(r"[^a-z0-9]+", "", (blob or "").lower())
    return needle in haystack


# Platforms where "the first path segment is the account handle" is a reliable
# structural assumption. Deliberately NOT extended to directories/listings (JustDial,
# Trip.com, etc.) -- their URL slugs routinely embed a business name inside a listing
# page that belongs to the DIRECTORY, not the business.
SOCIAL_PROFILE_HOSTS = {"instagram.com", "facebook.com", "m.facebook.com"}


def _is_own_profile_link(company_name, link):
    """True if the URL's account HANDLE (the first path segment on a known social
    platform, e.g. instagram.com/<handle>) names the business -- i.e. this looks like
    the business's own profile page, not a third party merely mentioning it.

    This is a stronger trust signal than `_name_matches_blob` alone catches. Verified
    live: for "Sparrk", the correct email tied 1-1 (by plain vote count) against a wrong
    one -- but the correct email came from `facebook.com/sparrkgamezone/` (their own
    profile: the handle IS the business name) while the wrong one came from
    `facebook.com/cityshor/posts/newinahmedabad-sparrk-gaming-zone-.../` (a city-events
    aggregator account whose POST SLUG happened to mention Sparrk's name).

    Real bug caught during testing THIS function: checking the whole path (not just the
    first segment) made the cityshor URL above a false positive too -- "sparrk" appears
    in the post slug even though the actual account is "cityshor", not Sparrk's own. It
    matched the same "generic substring, not the actual identity" trap that
    `_name_matches_blob` exists to avoid for review/snippet text -- URL paths need the
    identical discipline, checking the handle specifically, not the whole path.
    """
    parsed = urlparse(link or "")
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in SOCIAL_PROFILE_HOSTS:
        return False
    segments = [s for s in parsed.path.split("/") if s]
    if not segments:
        return False
    handle = re.sub(r"[^a-z0-9]+", "", segments[0].lower())

    words = [w for w in re.split(r"[^a-z0-9]+", (company_name or "").lower()) if len(w) > 2]
    if not words:
        return False
    needle = "".join(words[:2])
    return needle in handle


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

        Real bug found live (2026-08-12): the original version accepted a domain if
        ANY single significant word of the business name (>3 chars) appeared as a
        substring of the domain -- for "Game Zone | Nexus Gaming Hub", the word "game"
        matched inside "timezonegames.com" (an unrelated business, Timezone), and every
        downstream field -- email, contact name, role -- got silently overwritten with
        Timezone's data. Same bug class as the find_phone/find_email name-match fix,
        just never applied here. Now uses `_name_matches_blob()` -- the FULL first-1-2-
        word signature must appear contiguously, not any one generic category word.
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

        # Google's own knowledge panel is a strong signal, but still name-checked --
        # ambiguous/generic business names can resolve the panel to the wrong entity.
        kg_site = (data.get("knowledgeGraph") or {}).get("website")
        if kg_site and not _is_directory(kg_site) and _name_matches_blob(company_name, _root_domain(kg_site)):
            logger.info("find_website %s -> %s (knowledge graph)", company_name, kg_site)
            return kg_site

        for result in data.get("organic", []):
            link = result.get("link")
            if not link or _is_directory(link):
                continue
            root = _root_domain(link)
            if _name_matches_blob(company_name, root):
                url = f"https://{root}/"
                logger.info("find_website %s -> %s (organic)", company_name, url)
                return url

        logger.info("find_website %s -> nothing confident enough", company_name)
        return None

    def find_phone(self, company_name, location=None, domain=None):
        """Recover a phone/WhatsApp number via organic search snippets, when the
        company's own website (website_scraper.scrape_phones) found nothing.

        Verified live (2026-08-12): Google's Places listing frequently has no phone for
        smaller businesses, but the organic web (their own contact page, a social bio)
        usually does. One recovered number was cross-confirmed against the same number
        found independently via a Google Maps detail-panel read -- same digits, two
        unrelated sources. Costs 1 Serper credit; call only after the free website
        scrape has already come up empty.

        Accuracy note: a single top hit is NOT trustworthy on its own -- different
        branches, stale numbers, and unrelated businesses all show up across results.
        Majority vote across all snippets, with a hit on the company's own domain
        breaking ties, beats "take the first match" -- BUT plain majority vote is itself
        exploitable: two different competing businesses' promo posts can coincidentally
        share a number and outvote the one genuine hit. Verified live -- for "Infinity
        Gaming Zone PS5", two unrelated PS5-gaming reels (different names, different
        addresses) both mentioned the same number and would have outvoted the number on
        the business's own Instagram bio. Fix: only snippets where the business's own
        name actually appears are counted at all; a numeric majority from unrelated
        results is discarded rather than trusted.

        Second bug, found the same way (live-tested against a known-good number, not
        just "the code ran"): even with name-matching, a single result mentioning
        SEVERAL different numbers together (a "call us on X, Y, or Z" round-up post,
        common when a page covers multiple venues) can tie against a result that
        cleanly mentions ONE number -- and a raw count-based tie-break is arbitrary,
        effectively "whichever Google happened to rank first that day". Verified live
        for "SSJ CAFE AND PLAY": their own Instagram profile cleanly states one number
        (their real one), while an unrelated round-up post mentions that SAME real
        number ALONGSIDE three other unrelated numbers in one cluttered snippet -- a
        1-vote-each tie that could have gone either way. Fix: a result contributing
        MORE THAN ONE distinct number is ambiguous -- which one is actually theirs?
        -- and is excluded from voting entirely, not just partially discounted.
        """
        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY not configured")

        query = f"{company_name} {location or ''} contact mobile".strip()
        resp = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "in", "num": 10},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        votes = {}
        own_domain_hits = set()
        own_profile_hits = set()
        skipped_unmatched = 0
        skipped_ambiguous = 0
        for result in data.get("organic", []):
            blob = f"{result.get('title', '')} {result.get('snippet', '')}"
            link = result.get("link", "")
            link_root = _root_domain(link)
            is_own_profile = _is_own_profile_link(company_name, link)
            has_numbers = MOBILE_RE.search(blob)
            if has_numbers and not _name_matches_blob(company_name, blob):
                skipped_unmatched += 1
                continue

            distinct_numbers = {normalize_mobile(m.group(0)) for m in MOBILE_RE.finditer(blob)}
            distinct_numbers.discard(None)
            if len(distinct_numbers) > 1:
                # multiple different numbers crammed into one result -- can't tell
                # which is actually theirs, so none of them earn a vote from this result
                skipped_ambiguous += 1
                continue
            for mobile in distinct_numbers:
                votes[mobile] = votes.get(mobile, 0) + 1
                if domain and link_root == domain:
                    own_domain_hits.add(mobile)
                if is_own_profile:
                    own_profile_hits.add(mobile)

        if not votes:
            logger.info("find_phone %s -> nothing found (skipped %d unmatched-name, "
                        "%d ambiguous-multi-number results)",
                         company_name, skipped_unmatched, skipped_ambiguous)
            return None

        # own domain/profile beats plain vote count -- "this is literally their page"
        # is stronger evidence than "this number was mentioned more times"
        trusted = own_domain_hits | own_profile_hits
        ranked = sorted(votes, key=lambda p: (p not in trusted, -votes[p]))
        winner = ranked[0]
        logger.info("find_phone %s -> %s (votes=%d, trusted_source=%s, all=%s, skipped_ambiguous=%d)",
                     company_name, winner, votes[winner], winner in trusted, votes, skipped_ambiguous)
        return winner

    def find_email(self, company_name, location=None, domain=None):
        """Recover a contact email via organic search snippets -- specifically for
        businesses with NO independent website (Instagram/Facebook page only), where
        website_scraper.scrape_emails() has nothing to scrape in the first place.

        Deliberately does NOT open Instagram/Facebook's own page (login walls, heavy
        JS, and closer to a ToS problem than reading a company's own site or even Maps).
        Instead it reads what Google already indexed from those pages -- the same
        public snippet text find_phone() reads, just filtered for emails instead.

        Three safeguards, all required (the first two were here from the start; the
        third was missing until a real bug proved it was needed too):
          1. name-match -- a result's email only counts if the business's own name is
             actually in that result (the exact bug class found while building find_phone).
          2. platform-address rejection -- help@instagram.com / support@facebook.com etc.
             are real, valid-shaped emails that would otherwise pass every other check;
             they belong to the platform, never the business, so they're excluded outright
             regardless of how often they appear.
          3. ambiguous multi-email results are excluded entirely. Verified live: for
             "Sparrk", the correct email (`sparrk24@gmail.com`, from their own official
             Facebook page's labeled "Contact info" field) tied 1-1 against a wrong one
             (`funzillasurat@gmail.com`) pulled from a city-events listicle post that
             names several different venues' contacts in one paragraph. Same root cause
             as the SSJ CAFE AND PLAY phone bug (tracker.md), just never ported to this
             function until this run exposed it: a source listing multiple different
             contacts can't tell you which one is this business's, so none of them vote.
          4. own-profile-link trust (`_is_own_profile_link`) -- that same "Sparrk" case
             had only ONE email per result (safeguard 3 alone didn't catch it), so vote
             count still tied 1-1. The real signal: the correct email's result URL was
             `facebook.com/sparrkgamezone/` (their own profile -- the business name IS
             the path), the wrong one was `facebook.com/cityshor/posts/...` (an events
             aggregator account). A result from the business's own profile page now
             outranks plain vote count entirely, not just breaks ties on top of it.
        """
        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY not configured")

        query = f"{company_name} {location or ''} contact email".strip()
        resp = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "in", "num": 10},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        votes = {}
        own_domain_hits = set()
        own_profile_hits = set()
        skipped_unmatched = 0
        skipped_ambiguous = 0
        for result in data.get("organic", []):
            blob = f"{result.get('title', '')} {result.get('snippet', '')}"
            link = result.get("link", "")
            link_root = _root_domain(link)
            is_own_profile = _is_own_profile_link(company_name, link)
            candidates = EMAIL_RE.findall(blob)
            if candidates and not _name_matches_blob(company_name, blob):
                skipped_unmatched += 1
                continue

            valid_emails = set()
            for raw in candidates:
                email = raw.lower().strip(".,;:)('\"")
                if not is_valid_contact_email(email):
                    continue
                email_domain = email.partition("@")[2]
                if _is_directory(f"https://{email_domain}"):
                    continue  # e.g. help@instagram.com -- the platform, not the business
                if domain and not belongs_to_company(email, domain):
                    continue
                valid_emails.add(email)

            if len(valid_emails) > 1:
                # multiple different emails crammed into one result (a listicle covering
                # several businesses, a "contact any of these" page) -- can't tell which
                # is actually theirs, so none of them earn a vote from this result
                skipped_ambiguous += 1
                continue
            for email in valid_emails:
                votes[email] = votes.get(email, 0) + 1
                if domain and link_root == domain:
                    own_domain_hits.add(email)
                if is_own_profile:
                    own_profile_hits.add(email)

        if not votes:
            logger.info("find_email %s -> nothing found (skipped %d unmatched-name, "
                        "%d ambiguous-multi-email results)",
                         company_name, skipped_unmatched, skipped_ambiguous)
            return None

        # own domain/profile beats plain vote count -- "this is literally their page"
        # is stronger evidence than "this email was mentioned more times"
        trusted = own_domain_hits | own_profile_hits
        ranked = sorted(votes, key=lambda e: (e not in trusted, -votes[e]))
        winner = ranked[0]
        logger.info("find_email %s -> %s (votes=%d, trusted_source=%s, all=%s, skipped_ambiguous=%d)",
                     company_name, winner, votes[winner], winner in trusted, votes, skipped_ambiguous)
        return winner

    def find_review_signals(self, company_name, location=None, max_snippets=6):
        """Pull public-web snippets that MIGHT contain genuine customer complaints, for
        the Review Analyst LLM agent to judge. Deliberately does NOT try to detect
        complaint language itself with keywords/regex -- "is this a real complaint or
        just marketing copy" is exactly the kind of qualitative judgment an LLM is good
        at and regex is bad at. This just gathers name-matched candidate text and lets
        the agent decide; an empty or irrelevant result is expected and must be handled
        gracefully downstream, not treated as an error.

        Verified live (2026-08-12): works for some businesses (found genuine "poor
        maintenance of arcade games", "billing mistakes and malfunctioning VR games"
        via review-aggregator sites Google indexes) and returns nothing usable for
        others in the same run -- roughly 1 in 3 in a small sample. This uneven
        coverage is why scoring/outreach must degrade gracefully rather than depend
        on review data being present.
        """
        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY not configured")

        query = f"{company_name} {location or ''} review complaint".strip()
        resp = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "in", "num": 10},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        snippets = []
        for result in data.get("organic", []):
            blob = f"{result.get('title', '')} {result.get('snippet', '')}".strip()
            if not blob or not _name_matches_blob(company_name, blob):
                continue
            snippets.append(blob)
            if len(snippets) >= max_snippets:
                break

        logger.info("find_review_signals %s -> %d name-matched snippets", company_name, len(snippets))
        return snippets
