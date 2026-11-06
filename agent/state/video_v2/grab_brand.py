import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).parent
SITES = {"vistara": "https://vistararealty.com", "namasya": "https://shreenamasya.com"}
out = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for k, u in SITES.items():
        pg = b.new_page(viewport={"width": 1280, "height": 800}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        try:
            pg.goto(u, wait_until="networkidle", timeout=45000)
        except Exception as e:
            print(k, "goto issue:", str(e)[:120])
        pg.wait_for_timeout(1500)
        (HERE / k / "home_pw.html").write_text(pg.content(), encoding="utf-8")
        pg.screenshot(path=str(HERE / k / "top.png"))
        imgs = pg.evaluate("""() => Array.from(document.images).slice(0,40).map(i => ({src:i.currentSrc||i.src, w:i.naturalWidth, h:i.naturalHeight, alt:i.alt, cls:i.className, inHeader: !!i.closest('header,nav')}))""")
        out[k] = {"title": pg.title(), "imgs": imgs[:25]}
        print(k, pg.title(), len(imgs))
        for i in imgs[:14]:
            print("  ", i["w"], i["h"], i["inHeader"], i["src"][:110], "|", i["alt"][:30])
        pg.close()
    b.close()
json.dump(out, open(HERE / "brand_imgs.json", "w"), indent=1)
