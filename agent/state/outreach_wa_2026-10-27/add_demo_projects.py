# -*- coding: utf-8 -*-
"""Aaj ki 4 verified leads ko WhatsApp demo bot ki project list me jodta hai (backend/services/demo_projects.json). Purane 13 projects jaise the waise rehte hain.
Bot lead ke likhe shabd wapas nahi bhejta: wo sirf is list ki key dekhta hai aur jawab me HAMARA likha naam aur sample buttons jaate hain (bands 'sample' hain, lead ki asli keemat nahi).
Uske baad: bash agent/deploy/vps_run.sh agent/deploy/vps_demo_projects_update.sh backend/services/demo_projects.json"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
F = ROOT / "backend" / "services" / "demo_projects.json"
d = json.loads(F.read_text(encoding="utf-8"))

NEW = {
    "Shreem Avdhesh": dict(brand="Shreem Group", types=["2 BHK", "3 BHK"], budget=["Up to 45 lakh", "45 to 65 lakh", "Above 65 lakh"], slug="shreem-avdhesh-demo-only"),
    "Shivanta Krushnam": dict(brand="Shivanta Group", types=["3 BHK", "Tell me more"], budget=["Up to 75 lakh", "75 lakh to 1.5 cr", "Above 1.5 crore"], slug="shivanta-krushnam-demo-only"),
    "Kishan Antilia": dict(brand="Kishan Antilia", types=["4 BHK", "Tell me more"], budget=["Up to 1.5 crore", "1.5 to 2 crore", "Above 2 crore"], slug="kishan-antilia-demo-only"),
    "Class One Evoq": dict(brand="Class One", types=["4 BHK", "Tell me more"], budget=["Up to 80 lakh", "80 lakh to 1 cr", "Above 1 crore"], slug="class-one-evoq-demo-only"),
}
added = []
for name, v in NEW.items():
    key = re.sub(r"[^a-z0-9]", "", name.lower())
    for label in v["budget"] + v["types"] + ["Not sure yet"]:
        if len(label) > 20:
            sys.exit("label too long: %r" % label)
    if key in d:
        print("already there:", key)
        continue
    d[key] = {"name": name, "brand": v["brand"], "types": v["types"], "budget": v["budget"], "slug": v["slug"]}
    added.append(key)
F.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
print("added:", added, "| total now:", len(d))
