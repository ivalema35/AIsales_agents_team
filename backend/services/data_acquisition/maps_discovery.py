"""2026-09-10 real live gap: Serper's shared credit pool (Places AND Search both) is
fully exhausted ("Not enough credits" on both endpoints, confirmed live) -- with nothing
left, discover() finds zero new companies and every enrichment function
(find_website/find_phone/find_email/find_social_profiles/etc.) also fails, so even an
existing lead can't be enriched. This is a free (no API key, no billing account) stopgap
discovery source that reads Google Maps' own search-results feed directly via
Playwright, reusing maps_scraper.py's exact "read-only, no evasion" posture (no login,
no proxy rotation, no CAPTCHA solving) and its block-signal detection -- just extended
from "read one already-known place's phone" to "read a whole results feed of NEW places".

Real, disclosed risk, higher than maps_scraper.py's single-place lookup: scraping a
LISTING page (many businesses, scrolled feed) is a bigger footprint than one detail-panel
read, so this deliberately runs at a small scale (few queries at a time, real delays
between each place's detail-panel visit, same block-signal abort) -- a manual/occasional
stopgap tool, not meant to replace Serper's own steady, larger-volume, ToS-compliant API
once real credits are available again.
"""
from __future__ import annotations
import asyncio
import logging
import random

from playwright.async_api import async_playwright

from services.data_acquisition.base import empty_lead
from services.data_acquisition.website_scraper import normalize_mobile

logger = logging.getLogger(__name__)

MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 6

_BLOCK_SIGNALS = ("unusual traffic", "recaptcha", "g-recaptcha", "/sorry/index")


def _clean_panel_text(raw):
    """Maps' detail-panel buttons render a Material Symbols icon glyph (Private Use
    Area codepoints, e.g. U+E0C8) inside the same element as the visible text --
    innerText includes it as leading junk. Verified live: a real address came back as
    a stray glyph + newline + the actual address text -- strip those codepoints out
    rather than guessing at the text."""
    if not raw:
        return raw
    cleaned = "".join(ch for ch in raw if not (0xE000 <= ord(ch) <= 0xF8FF))
    return cleaned.strip() or None


async def _discover_async(query: str, location: str | None, max_results: int):
    search_text = f"{query} in {location}" if location else query
    url = f"https://www.google.com/maps/search/{search_text.replace(' ', '+')}"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900}, locale="en-IN")
        page = await context.new_page()
        try:
            await page.goto(url, timeout=25000)
            await page.wait_for_timeout(2500)

            body_text = (await page.inner_text("body")).lower()
            if any(signal in body_text for signal in _BLOCK_SIGNALS):
                raise RuntimeError("block signal detected in page content")

            feed = await page.query_selector('div[role="feed"]')
            if not feed:
                logger.info("maps discover '%s': no results feed (single auto-opened place, or zero results)", search_text)
                return results

            # Google Maps lazy-loads more cards as the feed scrolls -- a few scrolls
            # surface a realistic batch without an unbounded scroll loop.
            for _ in range(5):
                await feed.evaluate("el => el.scrollBy(0, 1200)")
                await page.wait_for_timeout(1200)

            cards = await feed.query_selector_all('a[href*="/maps/place/"]')
            hrefs = []
            seen = set()
            for card in cards:
                href = await card.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    hrefs.append(href)
                if len(hrefs) >= max_results:
                    break

            logger.info("maps discover '%s': %d candidate listing(s) found in feed", search_text, len(hrefs))

            for href in hrefs:
                await asyncio.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))
                try:
                    await page.goto(href, timeout=20000)
                    await page.wait_for_timeout(2000)

                    body_text = (await page.inner_text("body")).lower()
                    if any(signal in body_text for signal in _BLOCK_SIGNALS):
                        raise RuntimeError("block signal detected mid-batch")

                    name_el = await page.query_selector("h1")
                    name = (await name_el.inner_text()).strip() if name_el else None
                    if not name:
                        continue

                    phone_btn = await page.query_selector('button[data-item-id^="phone"]')
                    phone = normalize_mobile((await phone_btn.inner_text()).strip()) if phone_btn else None

                    website_link = await page.query_selector('a[data-item-id="authority"]')
                    website = (await website_link.get_attribute("href")) if website_link else None

                    address_btn = await page.query_selector('button[data-item-id="address"]')
                    address = _clean_panel_text(await address_btn.inner_text()) if address_btn else None

                    category = None
                    category_el = await page.query_selector('button[jsaction*="category"]')
                    if category_el:
                        category = (await category_el.inner_text()).strip()

                    results.append(empty_lead(
                        company_name=name,
                        website_url=website,
                        primary_phone=phone,
                        region_location=address,
                        source="GOOGLE_MAPS_MANUAL",
                        category=category,
                    ))
                except Exception as exc:  # noqa: BLE001 - one bad card must not kill the whole batch
                    logger.warning("maps discover: one listing failed (%s), continuing", exc)
                    continue
        finally:
            await page.close()
            await context.close()
            await browser.close()

    logger.info("maps discover '%s' -> %d lead(s) extracted", search_text, len(results))
    return results


def discover_via_maps(query: str, location: str | None = None, max_results: int = 15):
    """Sync entrypoint -- same calling convention as SerperProvider.discover(), so a
    caller can use this as a drop-in alternative when Serper is unavailable."""
    return asyncio.run(_discover_async(query, location, max_results))
