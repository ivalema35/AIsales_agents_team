"""Last-resort phone recovery: read Google Maps' own detail panel via Playwright.

Only reached when both the free website scrape (website_scraper.scrape_phones) and the
Serper organic-snippet search (SerperProvider.find_phone) have already come up empty --
this is the most expensive and the riskiest of the three (closer to a Maps ToS problem
than reading a company's own site, per the discussion with the user + Gemini's review).

No evasion: no login, no proxy rotation, no CAPTCHA solving, no fingerprint spoofing --
same "read-only, no tricks" rule as playwright_fallback.py. What this module adds on top
is a circuit breaker, because unlike a one-off fetch, this is meant to be called across a
whole batch of leads and must not hammer Maps if something starts going wrong.
"""
import asyncio
import logging
import random
import threading

from playwright.async_api import async_playwright

from services.data_acquisition.serp_provider import _name_matches_blob
from services.data_acquisition.website_scraper import normalize_mobile

logger = logging.getLogger(__name__)

MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 5

# Strings that show up when Google has decided we're a bot -- if we ever see one of
# these, that's a hard signal to stop hitting Maps for the rest of this run, not just
# skip this one lookup.
_BLOCK_SIGNALS = ("unusual traffic", "recaptcha", "g-recaptcha", "/sorry/index")


async def _read_maps_phone(company_name: str, location: str | None):
    """One Maps lookup. Returns a normalized mobile number, or None if genuinely not
    found. Raises only for signals the circuit breaker should count against it
    (suspected blocking) -- an ordinary "no phone on this listing" is NOT an error.
    """
    query = f"{company_name} {location}" if location else company_name
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900}, locale="en-IN")
        page = await context.new_page()
        try:
            await page.goto(url, timeout=20000)
            await page.wait_for_timeout(2500)  # Maps hydrates client-side, no clean "loaded" event

            body_text = (await page.inner_text("body")).lower()
            if any(signal in body_text for signal in _BLOCK_SIGNALS):
                raise RuntimeError("block signal detected in page content")

            phone_btn = await page.query_selector('button[data-item-id^="phone"]')
            if not phone_btn:
                # a results LIST loaded instead of a single auto-opened place
                first_result = await page.query_selector('div[role="feed"] a[href*="/maps/place/"]')
                if first_result:
                    await first_result.click()
                    await page.wait_for_timeout(2000)
                    phone_btn = await page.query_selector('button[data-item-id^="phone"]')

            if not phone_btn:
                return None  # legitimately nothing on Maps -- not a failure

            name_el = await page.query_selector("h1")
            panel_name = (await name_el.inner_text()).strip() if name_el else ""
            if not _name_matches_blob(company_name, panel_name):
                logger.info("maps phone: panel name %r doesn't match %r, discarding",
                            panel_name, company_name)
                return None  # landed on the wrong listing -- discard, don't guess

            raw = (await phone_btn.inner_text()).strip()
            return normalize_mobile(raw)
        finally:
            await page.close()
            await context.close()
            await browser.close()


class MapsPhoneCircuitBreaker:
    """Bounds one batch of Maps lookups: a hard cap on total attempts, a random delay
    between each, and a trip switch that permanently disables the rest of the batch
    after repeated failures -- so one bad run degrades to "no more Maps lookups" rather
    than hammering Google while blocked.

    One instance is meant to be shared across an entire scraper run (async_runner.py
    processes multiple leads concurrently, each in its own worker thread), so the
    counters are guarded by a plain threading.Lock -- this crosses real OS threads via
    asyncio.to_thread, not just coroutines on one event loop, so an asyncio.Lock alone
    would not be enough.
    """

    def __init__(self, max_batch=8, trip_after_consecutive_failures=3):
        self.max_batch = max_batch
        self.trip_after = trip_after_consecutive_failures
        self.calls_made = 0
        self.consecutive_failures = 0
        self.tripped = False
        self._lock = threading.Lock()

    def _reserve_slot(self) -> bool:
        """Thread-safe check-and-increment. True means this caller may proceed and has
        already been counted against max_batch; False means skip without a request."""
        with self._lock:
            if self.tripped or self.calls_made >= self.max_batch:
                return False
            self.calls_made += 1
            return True

    def _record_outcome(self, success: bool) -> bool:
        """Returns True if this outcome tripped the breaker."""
        with self._lock:
            if success:
                self.consecutive_failures = 0
                return False
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.trip_after:
                self.tripped = True
                return True
            return False

    async def find_phone(self, company_name: str, location: str | None = None):
        if not self._reserve_slot():
            logger.info("maps circuit breaker: skipping %s (tripped=%s, calls_made=%d/%d)",
                        company_name, self.tripped, self.calls_made, self.max_batch)
            return None

        await asyncio.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

        try:
            result = await _read_maps_phone(company_name, location)
            self._record_outcome(success=True)
            return result
        except Exception as exc:  # noqa: BLE001 - a Maps failure must never crash the batch
            tripped_now = self._record_outcome(success=False)
            logger.warning("maps phone lookup failed for %s (%d/%d consecutive): %s",
                           company_name, self.consecutive_failures, self.trip_after, exc)
            if tripped_now:
                logger.warning("maps circuit breaker TRIPPED -- no more Maps lookups this batch")
            return None
