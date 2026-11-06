# -*- coding: utf-8 -*-
"""Check frames taken from the FINAL mp4 itself (not the HTML): 8 frames of <key>/renders/<key>_final.mp4 at scene 1, the tap in scene 2, scene 3, scene 4 (3 beats), scene 5, scene 6
-> <key>/renders/<key>_final_sheet.png. Usage: C:/ivtools/venv/Scripts/python.exe final_sheet_lead.py <key>"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "shyamal"))
import toolpaths
FF = toolpaths.ffmpeg()
key = sys.argv[1]; D = ROOT / key
tl = json.loads((D / "timeline_real.json").read_text(encoding="utf-8")); S = {s["id"]: s for s in tl["scenes"]}
fx = json.loads((D / "lead.json").read_text(encoding="utf-8")).get("fx", {})
def at(i, f): s = S[i]; return round(min(s["voice_at"] + f * s["voice_dur"], s["end"] - 0.1), 2)
times = [at(1, 0.9), at(2, fx.get("tap", 0.82) + 0.08), at(3, 0.8), at(4, 0.2), at(4, 0.55), at(4, 0.92), at(5, 0.97), at(6, 1.0)]
tmp = D / "stills"; tmp.mkdir(exist_ok=True)
files = []
for i, t in enumerate(times):
    f = tmp / ("final_%d.png" % i); files.append(f)
    subprocess.run([FF, "-y", "-ss", str(t), "-i", str(D / "renders" / (key + "_final.mp4")), "-frames:v", "1", str(f)], capture_output=True)
cmd = [FF, "-y"]
for f in files: cmd += ["-i", str(f)]
fc = "".join("[%d:v]scale=400:-1[v%d];" % (i, i) for i in range(8)) + "[v0][v1][v2][v3]hstack=4[r1];[v4][v5][v6][v7]hstack=4[r2];[r1][r2]vstack=2[o]"
out = D / "renders" / (key + "_final_sheet.png")
r = subprocess.run(cmd + ["-filter_complex", fc, "-map", "[o]", "-frames:v", "1", str(out)], capture_output=True, text=True)
print(out, times, r.returncode)
