# -*- coding: utf-8 -*-
# PREVIEW ONLY: estimates word times for a voice text (no audio yet) so the visuals can be designed and checked. Real timing comes from the real MP3 (build_timeline.py).
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
text = (HERE / sys.argv[1]).read_text(encoding="utf-8")
scenes = [re.sub(r"\s+", " ", s).strip() for s in re.split(r"<break[^>]*/>", text) if s.strip()]
GAP, SYL, COMMA, STOP = 0.35, 0.18, 0.5, 0.65

def syllables(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    if w in ("i", "v"): return 1
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee")): n -= 1
    return max(1, n)

words, segs, t = [], [], 0.0
for i, sc in enumerate(scenes):
    start, cur = t, 0.05
    for w in sc.split():
        d = syllables(w) * SYL
        words.append({"w": w, "s": round(start + cur, 2), "e": round(start + cur + d, 2), "scene": i + 1})
        cur += d + 0.04
        if w.endswith(","): cur += COMMA
        elif re.search(r"[.?!]$", w): cur += STOP
    dur = round(cur + 0.15, 2)
    segs.append({"scene": i + 1, "src": [0, 0], "out": [round(start, 2), round(start + dur, 2)]})
    t = start + dur + GAP
total = round(t - GAP, 2)
(HERE / sys.argv[2]).write_text(json.dumps({"total": total, "gap": GAP, "segments": segs, "words": words}, indent=1), encoding="utf-8")
print("estimated total", total, "| scenes", [s["out"] for s in segs], "| words", len(words))
