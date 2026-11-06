import asyncio, pathlib
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).resolve().parent
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 900, "height": 1300}, device_scale_factor=1.6)
        await pg.goto((HERE / "indicative_estimate.html").as_uri())
        await pg.wait_for_timeout(600)
        await pg.pdf(path=str(HERE / "Nexus360_indicative_estimate.pdf"), format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        # overflow = content bottom vs the footer top inside each sheet
        res = await pg.evaluate("""Array.from(document.querySelectorAll('.sheet')).map(s => { const f = s.querySelector('.foot').getBoundingClientRect().top; let last = 0; Array.from(s.children).forEach(c => { if (!c.classList.contains('foot')) last = Math.max(last, c.getBoundingClientRect().bottom); }); return Math.round(last - f); })""")
        print("content bottom minus footer top (px, negative = fits):", res)
        for i, el in enumerate(await pg.query_selector_all(".sheet")):
            await el.screenshot(path=str(HERE / ("page_%d.png" % (i + 1))))
        await b.close()
asyncio.run(main())
