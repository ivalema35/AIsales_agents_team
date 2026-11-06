# -*- coding: utf-8 -*-
"""messages_final.json (ya draft) se owner ke liye WhatsApp outreach pack banata hai: har lead ka caption text (video ke saath paste), personalised demo link (hamare demo bot ka wa.me),
lead ka chat-link (video manually attach karke bhejne ke liye) aur steps. Kuch bheja nahi jaata: bhejna owner ka haath hai (apne WhatsApp se, ek ek karke).
Chalao:  python build_pack.py [messages_final.json]"""
import json
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).parent
src = HERE / (sys.argv[1] if len(sys.argv) > 1 else "messages_final.json")
if not src.exists():
    src = HERE / "messages_draft.json"
M = json.loads(src.read_text(encoding="utf-8"))
demo_no = M["demo_number"]
out, texts = [], {}
for L in M["leads"]:
    demo_link = "https://wa.me/%s?text=%s" % (demo_no, urllib.parse.quote("Yes, send the demo for " + L["project"]))
    tpl = M["template_gu"] if L.get("lang") == "gu" else M["template_en"]
    caption = tpl.replace("{greet}", L.get("greet", "team")).replace("{ad_phrase}", L.get("ad_phrase", "ads")).replace("{brand}", L["brand"]).replace("{project}", L["project"]).replace("{demo_link}", demo_link)
    assert len(caption) < 1024, (L["key"], len(caption))                       # WhatsApp video caption limit
    texts[L["key"]] = caption
    (HERE / ("caption_%s.txt" % L["key"])).write_text(caption, encoding="utf-8")
    alt = "".join("  - https://wa.me/%s\n" % p for p in L.get("alt_phones", []))
    block = "## %s (%s)\n\n" % (L["project"], L["city"])
    block += "1. Open the chat: https://wa.me/%s  (+%s)\n" % (L["phone"], L["phone"])
    if alt:
        block += "   If this number is not on WhatsApp, try:\n" + alt
    block += "2. Attach the video, paste this as the caption, press Send:\n\n```\n%s\n```\n\n" % caption
    if L.get("lang") == "gu" and M.get("english_alt_for_gu"):
        alt_text = M["template_en"].replace("{greet}", L.get("greet", "team")).replace("{ad_phrase}", L.get("ad_phrase", "ads")).replace("{brand}", L["brand"]).replace("{project}", L["project"]).replace("{demo_link}", demo_link)
        block += "English version (if you prefer it for this lead):\n\n```\n%s\n```\n\n" % alt_text
    block += "Demo link only (what the lead taps): %s\n\nChecked facts: %s\n" % (demo_link, L["facts_verified"])
    out.append(block)
head = ("# WhatsApp outreach pack - 27 Oct 2026 (4 verified leads, real estate)\n\n"
        "Video to attach: `%s` (same video for all four).\n\n"
        "How: send from YOUR WhatsApp, one lead at a time. Open the chat link, attach the video, paste the caption, Send. "
        "If a message is not delivered or the number is not on WhatsApp, tell me before trying another number. "
        "After each send tell me 'sent <lead>' and I log it in the CRM. Reply STOP = never message again.\n\n"
        "Order: Shreem first (strongest), then Shivanta, Kishan Antilia, Class One.\n\n" % M["video"])
(HERE / "OUTREACH_PACK.md").write_text(head + "\n\n".join(out), encoding="utf-8")
print("pack written:", [k for k in texts], [len(v) for v in texts.values()])
