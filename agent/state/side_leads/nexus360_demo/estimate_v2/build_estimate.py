"""Builds indicative_estimate.html and indicative_estimate.pdf from estimate_template.html,
then renders both pages to PNG (render/page_1.png, render/page_2.png) and prints an overflow check.

Run (from this folder):  C:/ivtools/venv/Scripts/python.exe build_estimate.py
Change a price below, run again. Prices are INR, before GST. Source of every number:
estimate/estimate_model.md (cost model) and buyer/signal_test_output.txt (pool counts).
Pilot price: Standard scope, 'from' price recommended by the cost model (break-even about Rs 1,040 an hour at base hours).
"""
import asyncio
import pathlib

from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent

# Yahan se sirf price badalna hai. Starter (Rs 35,000) ke liye scope bhi kam karna padta hai, sirf number badalna kaafi nahi.
PRICES = {
    "PILOT": "48,000",
    "MONTHLY": "30,000",
    "MONTHLY_LATER": "15,000",
}

# Pilot me read-only view ek weekly snapshot hai (live login nahi): live login alag priced option hai (page 2).
VIEW_ROW = (
    "Campaign only, no phone numbers or personal contacts: a weekly snapshot page and a CSV for you and one colleague, "
    "walked through each week on a screen-share."
)


def build_html() -> pathlib.Path:
    t = (HERE / "estimate_template.html").read_text(encoding="utf-8")
    for k, v in PRICES.items():
        t = t.replace("{{%s}}" % k, v)
    t = t.replace("{{VIEW_ROW}}", VIEW_ROW)
    assert "{{" not in t, "unfilled placeholder"
    out = HERE / "indicative_estimate.html"
    out.write_text(t, encoding="utf-8")
    return out


async def render(html: pathlib.Path):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 900, "height": 1300}, device_scale_factor=1.6)
        await pg.goto(html.as_uri())
        await pg.wait_for_timeout(700)
        await pg.pdf(path=str(HERE / "indicative_estimate.pdf"), format="A4", print_background=True,
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}, prefer_css_page_size=True)
        # overflow: lowest content edge inside .body vs the footer top (px, negative = fits)
        res = await pg.evaluate("""() => Array.from(document.querySelectorAll('.sheet')).map(s => {
            const f = s.querySelector('.foot').getBoundingClientRect().top;
            let last = 0;
            Array.from(s.querySelector('.body').children).forEach(c => { last = Math.max(last, c.getBoundingClientRect().bottom); });
            const body = s.querySelector('.body');
            return {gap_px: Math.round(f - last), body_scrollH: body.scrollHeight, body_clientH: body.clientHeight};
        })""")
        print("footer top minus content bottom (px; positive = room left):", res)
        for i, el in enumerate(await pg.query_selector_all(".sheet")):
            await el.screenshot(path=str(HERE / "render" / ("page_%d.png" % (i + 1))))
        # phone-width check of the HTML
        pg2 = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        await pg2.goto(html.as_uri())
        await pg2.wait_for_timeout(500)
        sw = await pg2.evaluate("document.documentElement.scrollWidth")
        print("phone width 390: scrollWidth =", sw)
        await pg2.screenshot(path=str(HERE / "render" / "phone_top.png"))
        await b.close()


if __name__ == "__main__":
    (HERE / "render").mkdir(exist_ok=True)
    html = build_html()
    asyncio.run(render(html))
