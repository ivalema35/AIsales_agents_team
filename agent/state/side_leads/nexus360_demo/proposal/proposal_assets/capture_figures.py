# Captures the page figures used in proposal.html from the sample files (read-only on the page sample; the video stills are re-shot
# from page_video/video_animatic.html, which has amber placeholders after the 20 Oct review).
# Run: C:/ivtools/venv/Scripts/python.exe capture_figures.py
# Outputs (in this folder): fig_page_m1.png, fig_page_m_screens.png (390 x 816 and 390 x 812 phone screens, cut at a block boundary),
# four video stills (720 x 1280 JPG), the two brand fonts.
# The dashboard figures on page 4 are drawn in HTML by build_proposal.py so the text is real text.
import os, shutil
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
BASE = HERE.rsplit("/", 1)[0]
Q = "?builder=Sample+Builders&project=Sample+Heights&city=Durg&rera=PCGRERA+SAMPLE&date=20+Oct+2026"
H1, H2 = 816, 812  # phone screen heights in CSS px: first shot ends after the "what the tap does" note, second between slot rows 3 and 4
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto("file:///" + BASE + "/page_video/builder_page_sample.html" + Q)
    pg.wait_for_timeout(2500)
    pg.screenshot(path=f"{HERE}/fig_page_m1.png", clip={"x": 0, "y": 0, "width": 390, "height": H1}, full_page=True)
    bb = pg.query_selector("#screens").bounding_box()
    pg.screenshot(path=f"{HERE}/fig_page_m_screens.png", clip={"x": 0, "y": bb["y"] - 8, "width": 390, "height": H2}, full_page=True)
    ctx.close()
    # video stills: stage only (?bare=1), 720 x 1280, at the four timestamps used on page 5
    ctx = b.new_context(viewport={"width": 720, "height": 1280}, device_scale_factor=1)
    pg = ctx.new_page()
    for t, name in ((0.0, "f1_hook_t00.0.jpg"), (4.2, "f2_screenA_checks12_t04.2.jpg"), (8.2, "f3_screenA_checks34_t08.2.jpg"), (11.0, "f4_screenB_t11.0.jpg"), (14.5, "f5_ask_t14.5.jpg")):
        pg.goto("file:///" + BASE + f"/page_video/video_animatic.html?t={t}&bare=1&autoplay=0")
        pg.wait_for_timeout(1200)
        pg.screenshot(path=f"{HERE}/{name}", type="jpeg", quality=88)
        shutil.copy(f"{HERE}/{name}", f"{BASE}/page_video/stills/{name}")
    ctx.close()
    b.close()
# IV Infotech brand fonts (already in the repo)
src = "C:/Users/Administrator/Desktop/AISales_agent_team/agent/state/outreach/assets/fonts/"
for f in ("inter.woff2", "space-grotesk.woff2"):
    if os.path.exists(src + f):
        shutil.copy(src + f, f"{HERE}/{f}")
print("done")
