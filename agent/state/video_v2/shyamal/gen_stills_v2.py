# -*- coding: utf-8 -*-
"""Shyamal video v2: character sheet (Rahul = buyer, IV = helper mascot) -> upload -> 3 full-bleed stills with nano-banana-2-lite (~4 credits each).
Run with the media venv: C:/ivtools/venv/Scripts/python.exe gen_stills.py
Key kabhi print nahi hoti (kie_lib). Spend: 3 stills ~12 credits."""
import base64, json, sys, time, urllib.request
from pathlib import Path

PILOT = Path("C:/Users/Administrator/Desktop/AISales_agent_team/agent/pilot/video")
sys.path.insert(0, str(PILOT))
import story_build as sb   # noqa: E402  (characters as SVG)
import kie_lib as K        # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "assets" / "stills"
OUT.mkdir(parents=True, exist_ok=True)

# ---- 1. character sheet: only Rahul + IV (no text: AI copies text)
sheet = ('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#F6F4EF;display:flex;align-items:flex-end;justify-content:space-around;'
         'width:900px;height:520px;padding:0 20px;box-sizing:border-box}</style><body>'
         + sb.rahul("neutral", False, w=330) + sb.iv("happy", False, 300) + '</body>')
(OUT / "charsheet.html").write_text(sheet, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 900, "height": 520})
    pg.goto((OUT / "charsheet.html").as_uri())
    pg.screenshot(path=str(OUT / "charsheet.png"))
    b.close()
print("charsheet.png ready")


def upload(path, name):
    data = "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()
    req = urllib.request.Request("https://kieai.redpandaai.co/api/file-base64-upload",
                                 data=json.dumps({"base64Data": data, "uploadPath": "images", "fileName": name}).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + K._key(), "Content-Type": "application/json", "User-Agent": "iv-kie/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode())
    assert j.get("success") or j.get("code") == 200, K._scrub(json.dumps(j))[:300]
    return j["data"]["downloadUrl"]


b0, _ = K.mark("shyamal v2 round2: before")
url = upload(OUT / "charsheet.png", "iv_charsheet_v2b.png")
print("uploaded charsheet")

CHARS = ("Use the attached character sheet for the exact look of the recurring characters and keep their faces, hair and outfits consistent: "
         "the young man with black hair and blue shirt is Rahul (a home buyer); the rounded blue robot with a dark visor face, cyan smiling eyes, an orange antenna ball "
         "and a white 'iv' badge on its chest is IV (a friendly helper mascot). Only include the characters named in the scene, no extra people unless the scene says so. ")
STYLE = ("Warm modern flat-vector storybook illustration in the style of an explainer video, clean shapes, soft gradients, NOT photorealistic, no 3D. "
         "Indian middle-class urban setting in Vadodara, Gujarat. Absolutely no text, no letters, no numbers, no logos, no watermarks anywhere in the image. "
         "Vertical 9:16 composition. The illustration is full-bleed and fills the entire frame edge to edge: no borders, no frames, no inset pictures, no blank bars, no empty white panels. "
         "The room or environment continues naturally all the way down to the bottom edge (rug, floor, furniture) with NO flat empty colour areas and NO hard horizontal edges; "
         "put all characters and props in the upper part of the frame, between 5% and 38% of the height, and keep the lower 55% calm and uncluttered because a chat card and a caption will be placed over it. ")

SCENES = {
    "A2_diwali_evening": "Scene: Diwali evening at home. Rahul sits on a sofa, curious and happy with a small smile, looking at his smartphone. Warm marigold-orange and navy palette, lit clay diyas, hanging string lights and a flower garland. "
                         "Below him the room continues: a patterned rug, wooden floor and a low coffee table with a tea cup. Only Rahul.",
    "B3_night_neutral": "Scene: late at night in a cosy apartment living room, Rahul sits on the sofa and looks at his smartphone; the phone's soft green glow lights his face; through the window behind him are city lights and a crescent moon. "
                        "Below him the sofa cushions, a rug and a floor lamp continue to the bottom edge. Dark navy and teal night palette. Only Rahul.",
    "B2_night_relieved": "Scene: late at night in the same cosy apartment living room, Rahul sits on the sofa smiling, pleased and relieved, looking at his smartphone; soft green glow on his face; window with city lights and a crescent moon behind him. "
                         "Below him the sofa cushions, a rug and a floor lamp continue to the bottom edge. Dark navy and teal night palette. Only Rahul.",
    "C2_morning_desk": "Scene: bright morning in a modern real estate sales office with pastel colours and big windows. A friendly young woman with black hair in a bun and a teal kurta (a sales executive, a new character) sits at a tidy desk, smiling and looking at an open laptop whose screen faces away from the viewer. "
                       "The upper-right quarter of the frame is empty bright wall and window. No robot, no buildings, no architectural models, no extra objects. Below her the desk, the light wooden floor and a chair continue to the bottom edge. Only the woman.",
    "D_diwali_skyline": "Scene: a flat vector Diwali evening skyline, warm marigold glow on the horizon, hanging string lights across the top, a row of lit clay diyas along the very bottom, a few simple distant apartment-building silhouettes, deep navy-to-teal sky with soft bokeh lights. "
                        "No people. The central area between 25% and 70% of the height is calm and fairly empty (a logo will be placed there).",
}

tasks = {}
for name, desc in SCENES.items():
    tid = K.create("nano-banana-2-lite", {"prompt": CHARS + desc + " " + STYLE, "image_urls": [url], "aspect_ratio": "9:16"})
    tasks[name] = tid
    print("task", name, tid)
for name, tid in tasks.items():
    if not tid:
        continue
    d = K.wait(tid)
    us = K.urls(d)
    print(name, d.get("state"), "credits", d.get("creditsConsumed"), d.get("failMsg") or "")
    if us:
        K.download(us[0], OUT / (name + ".jpg"))
b1, sp = K.mark("shyamal v2 round2: after stills")
print("balance:", b1, "| spent this run:", (b0 - b1) if (b0 is not None and b1 is not None) else None)
