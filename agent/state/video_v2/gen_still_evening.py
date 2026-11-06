# -*- coding: utf-8 -*-
"""One plain evening-at-home still (Rahul on a sofa with a phone, NO diyas / garlands / string lights) for scene 2 of the non-Diwali lead videos.
Same working pattern as shyamal/gen_stills_v3.py: character sheet = shyamal/assets/stills/charsheet.png (look of Rahul only). 1 image = 4 credits. Key never printed."""
import base64, json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "C:/Users/Administrator/Desktop/AISales_agent_team/agent/pilot/video")
import kie_lib as K
ROOT = Path(__file__).parent
OUT = ROOT / "_shared" / "assets" / "stills"
def upload(path, name):
    data = "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()
    req = urllib.request.Request("https://kieai.redpandaai.co/api/file-base64-upload",
                                 data=json.dumps({"base64Data": data, "uploadPath": "images", "fileName": name}).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + K._key(), "Content-Type": "application/json", "User-Agent": "iv-kie/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())["data"]["downloadUrl"]
STYLE = ("Warm modern flat-vector storybook illustration in the style of an explainer video, clean shapes, soft gradients, NOT photorealistic, no 3D. Indian urban setting in Gujarat. "
         "Absolutely no text, no letters, no numbers, no logos, no watermarks anywhere in the image. Vertical 9:16 composition, full-bleed, filling the entire frame edge to edge, no borders, no blank bars. ")
url = upload(ROOT / "shyamal" / "assets" / "stills" / "charsheet.png", "iv_charsheet_v2c.png")
CHARS = ("Use the attached character sheet only for the exact look of Rahul, the young man with black hair and blue shirt (a home buyer); keep his face, hair and outfit consistent. Only include Rahul. ")
b0 = K.credits(); print("balance before:", b0)
t = K.create("nano-banana-2-lite", {"prompt": CHARS + "Scene: a calm ordinary evening at home. Rahul sits on a sofa in the upper part of the frame (between 5% and 38% of the height), curious and happy with a small smile, looking at his smartphone. "
    "Warm cosy living room in a soft amber and navy palette lit by a floor lamp, plain wall with a simple framed picture, a plant. NO diyas, NO oil lamps, NO candles, NO string lights, NO flower garlands, NO festival decorations of any kind. "
    "Below him the room continues all the way to the bottom edge: sofa cushions, a patterned rug and wooden floor, a low wooden coffee table with a tea cup. IMPORTANT: no white shapes, no white tablecloth, no white oval, no flat empty colour areas. " + STYLE,
    "image_urls": [url], "aspect_ratio": "9:16"})
d = K.wait(t); us = K.urls(d)
print("F_evening_home", d.get("state"), d.get("creditsConsumed"), d.get("failMsg") or "")
if us: K.download(us[0], OUT / "F_evening_home.jpg")
b1 = K.credits(); print("balance after:", b1, "spent:", (b0 - b1) if (b0 is not None and b1 is not None) else "?")
