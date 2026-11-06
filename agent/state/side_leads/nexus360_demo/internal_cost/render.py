import asyncio, pathlib
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).resolve().parent
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 900, "height": 1300}, device_scale_factor=1.6)
        await pg.goto((HERE / "internal_cost.html").as_uri())
        await pg.wait_for_timeout(600)
        await pg.pdf(path=str(HERE / "Nexus360_INTERNAL_cost_breakdown.pdf"), format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        res = await pg.evaluate("Array.from(document.querySelectorAll('.sheet')).map(s => { let last = 0; Array.from(s.children).forEach(c => { last = Math.max(last, c.getBoundingClientRect().bottom - s.getBoundingClientRect().top); }); return Math.round(last - s.clientHeight); })")
        print("content bottom minus sheet height (px, negative = fits):", res)
        el = await pg.query_selector(".sheet")
        await el.screenshot(path=str(HERE / "page_1.png"))
        await b.close()
asyncio.run(main())
