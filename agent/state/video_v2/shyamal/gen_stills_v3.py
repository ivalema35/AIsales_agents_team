# -*- coding: utf-8 -*-
"""Round 2b: D (Diwali skyline, NO character sheet so no people get copied in) and A3 (Diwali evening without the white oval)."""
import base64, json, sys
from pathlib import Path
PILOT = Path("C:/Users/Administrator/Desktop/AISales_agent_team/agent/pilot/video")
sys.path.insert(0, str(PILOT))
import kie_lib as K
HERE = Path(__file__).parent
OUT = HERE / "assets" / "stills"

def upload(path, name):
    import urllib.request
    data = "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()
    req = urllib.request.Request("https://kieai.redpandaai.co/api/file-base64-upload",
                                 data=json.dumps({"base64Data": data, "uploadPath": "images", "fileName": name}).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + K._key(), "Content-Type": "application/json", "User-Agent": "iv-kie/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode())
    return j["data"]["downloadUrl"]

STYLE = ("Warm modern flat-vector storybook illustration in the style of an explainer video, clean shapes, soft gradients, NOT photorealistic, no 3D. Indian urban setting in Gujarat. "
         "Absolutely no text, no letters, no numbers, no logos, no watermarks anywhere in the image. Vertical 9:16 composition, full-bleed, filling the entire frame edge to edge, no borders, no blank bars. ")
url = upload(OUT / "charsheet.png", "iv_charsheet_v2c.png")
CHARS = ("Use the attached character sheet only for the exact look of Rahul, the young man with black hair and blue shirt (a home buyer); keep his face, hair and outfit consistent. Only include Rahul. ")
b0 = K.credits()
t1 = K.create("nano-banana-2-lite", {"prompt": "Scene: a flat vector Diwali evening skyline with NO people and NO characters at all: warm marigold glow on the horizon, hanging string lights across the top, a row of lit clay diyas along the very bottom edge, a few simple distant apartment-building silhouettes, deep navy-to-teal sky with soft bokeh lights. The central area between 25% and 70% of the height is calm and fairly empty. " + STYLE, "aspect_ratio": "9:16"})
t2 = K.create("nano-banana-2-lite", {"prompt": CHARS + "Scene: Diwali evening at home. Rahul sits on a sofa in the upper part of the frame (between 5% and 38% of the height), curious and happy with a small smile, looking at his smartphone. Warm marigold-orange and navy palette, lit clay diyas, hanging string lights and a flower garland behind him. "
                    "Below him the room continues all the way to the bottom edge: sofa cushions, a patterned rug and wooden floor, a low wooden coffee table with a tea cup. IMPORTANT: no white shapes, no white tablecloth, no white oval, no flat empty colour areas. " + STYLE,
                    "image_urls": [url], "aspect_ratio": "9:16"})
for name, tid in (("D2_diwali_skyline", t1), ("A3_diwali_evening", t2)):
    d = K.wait(tid)
    us = K.urls(d)
    print(name, d.get("state"), d.get("creditsConsumed"), d.get("failMsg") or "")
    if us:
        K.download(us[0], OUT / (name + ".jpg"))
print("spent this run:", b0 - K.credits(), "| balance:", K.credits())
