from playwright.async_api import async_playwright


async def fetch_rendered(url, wait_selector=None, timeout=30000):
    """Render a JS-heavy page and return its HTML. Last-resort fallback only --
    providers (Serper/Hunter) come first; point this at sites without an API.

    Evasion-free by design: no proxy rotation, no fingerprint spoofing, no CAPTCHA
    handling. The try/finally is the whole point -- a page/context/browser left open
    on an exception path leaks a chromium process, and 50 of those OOM the box.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            await page.goto(url, timeout=timeout)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=10000)
            return await page.content()
        finally:
            await page.close()
            await context.close()
            await browser.close()
