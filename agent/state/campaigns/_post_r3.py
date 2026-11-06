# -*- coding: utf-8 -*-
"""Round 3 entries ko push se pehle theek karo: 'round 2' wale text, extra fields (must_not_claim etc.), safety checks."""
import json
import re
from pathlib import Path

P = Path("C:/Users/Administrator/Desktop/AISales_agent_team/agent/state/campaigns")
f = P / "ai-automation-real-estate-gujarat-r3.leads.entries.json"
extra = json.loads((P / "_r3_extra_fields.json").read_text(encoding="utf-8"))["keys"]
items = json.loads(f.read_text(encoding="utf-8"))

for it in items:
    if it["type"] == "lead":
        d = it["data"]
        d["history"] = [
            {"date": "2026-10-21", "text": "Found in round 3 of the lead research: Meta Ad Library (click-to-WhatsApp ads), hiring signals and new-RERA scan; nobody contacted"},
            {"date": "2026-10-21", "text": "Re-checked by an independent skeptic (own browser tab, raw HTML, MX); graded %s, hunger %s/10 (%s)" % (d["grade"], d["hunger_score"], d["hunger_tier"])},
        ]
        d["note"] = ("All facts come from public sources dated within 90 days (checked 21 Oct 2026). The need is inferred from ads, hiring and the funnel, not observed as slow replies. "
                     "Owner/decision-maker is not verified. Nobody has been contacted.")
        d.update(extra[it["key"]])
        d["round"] = "round-3"
        # safety: boss ka personal number kabhi nahi
        blob = json.dumps(d, ensure_ascii=False)
        assert "9924426361" not in re.sub(r"\D", "", blob), "boss number found"
        assert d["status"] == "researched" and d["contacted"] is False
    elif it["type"] == "activity":
        n = len([i for i in items if i["type"] == "lead"])
        it["key"] = "research-done-ai-automation-real-estate-gujarat-2026-10-round-3"
        it["data"]["text"] = ("Round 3 lead research done: %d leads added (2 hungry: Shyamal Park Lane, Vistara Group; 2 warm kept at the owner's request: BLJ Infra, Shree Namasya). "
                              "14 builders were enriched from 79 WhatsApp-button advertisers, hiring and new-RERA scans; 2 passed the bar (grade B or better and hunger 6 or more). "
                              "Sources: Meta Ad Library, LinkedIn jobs, GujRERA mirrors, own websites. Nobody contacted." % n)

f.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
for it in items:
    if it["type"] == "lead":
        d = it["data"]
        print(it["key"], "|", d["name"], "|", d["grade"], d["hunger_score"], d["hunger_tier"], "| contacts:", len(d["contacts"]), "| lang:", repr(d["language"]), "| tags:", it["tags"])
    else:
        print(it["key"], "|", it["data"]["text"][:200])
print("OK", len(items), "entries")
