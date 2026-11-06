import sys
from playwright.sync_api import sync_playwright
src, out, w = sys.argv[1], sys.argv[2], int(sys.argv[3])
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": 900})
    pg.goto("file:///" + src.replace("\\", "/")); pg.wait_for_timeout(800)
    pg.screenshot(path=out, full_page=True); b.close()
