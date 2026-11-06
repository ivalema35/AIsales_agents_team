# -*- coding: utf-8 -*-
"""One plain dusk skyline (no people, no diyas, no festival decoration) for scenes 1 and 6 of the non-Diwali lead videos.
Same working pattern as shyamal/gen_stills_v3.py (no character sheet for a pure skyline). Spend cap: 1 image = 4 credits. The key is never printed."""
import sys
from pathlib import Path
sys.path.insert(0, "C:/Users/Administrator/Desktop/AISales_agent_team/agent/pilot/video")
import kie_lib as K
OUT = Path(__file__).parent / "_shared" / "assets" / "stills"
STYLE = ("Warm modern flat-vector storybook illustration in the style of an explainer video, clean shapes, soft gradients, NOT photorealistic, no 3D. Indian urban setting in Gujarat. "
         "Absolutely no text, no letters, no numbers, no logos, no watermarks anywhere in the image. Vertical 9:16 composition, full-bleed, filling the entire frame edge to edge, no borders, no blank bars. ")
name = sys.argv[1] if len(sys.argv) > 1 else "E_plain_skyline"
b0 = K.credits()
print("balance before:", b0)
t = K.create("nano-banana-2-lite", {"prompt": "Scene: a calm flat vector dusk skyline with NO people and NO characters at all, and NO lamps, NO diyas, NO string lights, NO flowers, NO festival decorations of any kind: "
    "deep navy-to-teal twilight sky with a few tiny soft stars and a gentle warm glow on the horizon, a row of simple modern apartment-building and villa silhouettes with a few softly lit windows along the bottom 25% of the frame, a plain dark road at the very bottom edge. "
    "The area between 5% and 70% of the height is calm, smooth and fairly empty (just the sky gradient). " + STYLE, "aspect_ratio": "9:16"})
d = K.wait(t)
us = K.urls(d)
print(name, d.get("state"), d.get("creditsConsumed"), d.get("failMsg") or "")
if us:
    K.download(us[0], OUT / (name + ".jpg"))
b1 = K.credits()
print("balance after:", b1, "spent:", (b0 - b1) if (b0 is not None and b1 is not None) else "?")
