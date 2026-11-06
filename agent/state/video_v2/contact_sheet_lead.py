# -*- coding: utf-8 -*-
"""Design check: renders 8 stills (scenes 1-6, scene 4 three beats) of <key>/story.html with timeline.json and tiles them into <key>/renders/<key>_sheet.png.
Usage: C:/ivtools/venv/Scripts/python.exe contact_sheet_lead.py <key> [timeline.json] [html]"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "shyamal"))
import toolpaths
FF = toolpaths.ffmpeg()
key = sys.argv[1]; D = ROOT / key
tlf = sys.argv[2] if len(sys.argv) > 2 else "timeline.json"; html = sys.argv[3] if len(sys.argv) > 3 else "story.html"
tl = json.loads((D / tlf).read_text(encoding="utf-8")); S = {s["id"]: s for s in tl["scenes"]}
def at(i, f): s = S[i]; return round(s["voice_at"] + f * s["voice_dur"], 2)
times = [at(1, 0.9), at(2, 0.97), at(3, 0.8), at(4, 0.2), at(4, 0.6), at(4, 0.92), at(5, 0.95), at(6, 1.0)]
times = [min(t, S[i]["end"] - 0.1) for t, i in zip(times, [1, 2, 3, 4, 4, 4, 5, 6])]
subprocess.run([toolpaths.python(), str(ROOT / "render_story_lead.py"), key, "--html", html, "--tl", tlf, "--stills", ",".join(str(t) for t in times)], check=True)
files = [D / "stills" / ("t%05.2f.png" % t) for t in times]
out = D / "renders" / (key + "_sheet.png"); out.parent.mkdir(exist_ok=True)
cmd = [FF, "-y"]
for f in files: cmd += ["-i", str(f)]
fc = "".join("[%d:v]scale=400:-1[v%d];" % (i, i) for i in range(8)) + "[v0][v1][v2][v3]hstack=4[r1];[v4][v5][v6][v7]hstack=4[r2];[r1][r2]vstack=2[o]"
r = subprocess.run(cmd + ["-filter_complex", fc, "-map", "[o]", "-frames:v", "1", str(out)], capture_output=True, text=True)
print("sheet:", out, "times", times, "" if r.returncode == 0 else r.stderr[-300:])
