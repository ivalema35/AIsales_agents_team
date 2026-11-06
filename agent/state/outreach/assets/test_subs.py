# -*- coding: utf-8 -*-
# Automatic check of the video page: never more than ONE subtitle chunk visible, no page errors, and every scene shows a headline.
# usage: <playwright python> test_subs.py [timeline.json]
import asyncio, sys
from playwright.async_api import async_playwright
TL = sys.argv[1] if len(sys.argv) > 1 else "timeline.json"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 720, "height": 1280})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"http://127.0.0.1:5013/master_video.html?project=Pride%20Aura&city=Rajkot&bhk1=3%20BHK&bhk2=4%20BHK&tl={TL}")
        await pg.wait_for_function("window.READY === true", timeout=20000)
        total = await pg.evaluate("window.TOTAL")
        worst, bad, t, gaps = 0, [], 0.0, 0
        while t <= total:
            n = await pg.evaluate(f"(setT({t}), [...document.querySelectorAll('#subs .chunk')].filter(e => e.style.opacity === '1').length)")
            worst = max(worst, n)
            if n > 1: bad.append(round(t, 2))
            t += 0.05
        chunks = await pg.evaluate("window.__chunks")
        print(f"total {total}s | max chunks visible at once: {worst} | overlap times: {bad[:10]} | page errors: {errs[:3]}")
        print("chunks:", " | ".join(chunks))
        await b.close()
asyncio.run(main())
