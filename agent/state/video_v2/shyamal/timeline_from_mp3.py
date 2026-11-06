# -*- coding: utf-8 -*-
"""Real timeline from the owner's ElevenLabs MP3 (6 scene lines separated by <break time="1.0s" />):
the 5 longest silences are the scene breaks; every scene = from the middle of the previous break to the middle of the next one,
so the 0.4 s cross-fades of the visuals happen inside the silences. The MP3 is then played from t=0 (render_story.py --audio file.mp3).
Usage: C:/ivtools/venv/Scripts/python.exe timeline_from_mp3.py voice_elevenlabs.mp3 [timeline_real.json]"""
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import toolpaths
FF = toolpaths.ffmpeg()

mp3 = HERE / (sys.argv[1] if len(sys.argv) > 1 else "voice_elevenlabs.mp3")
out = HERE / (sys.argv[2] if len(sys.argv) > 2 else "timeline_real.json")
N = 6

r = subprocess.run([FF, "-i", str(mp3), "-af", "silencedetect=noise=-33dB:d=0.55", "-f", "null", "-"], capture_output=True, text=True)
log = r.stderr
dm = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log)
total_audio = int(dm.group(1)) * 3600 + int(dm.group(2)) * 60 + float(dm.group(3))
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
sil = []
for i, s in enumerate(starts):
    e = ends[i] if i < len(ends) else total_audio
    sil.append((s, e, e - s))
# leading / trailing silence is not a scene break
inner = [x for x in sil if x[0] > 0.8 and x[1] < total_audio - 0.3]
inner.sort(key=lambda x: -x[2])
if len(inner) < N - 1:
    sys.exit("found only %d inner silences >= 0.55 s (need %d). Detected: %s" % (len(inner), N - 1, [(round(a, 2), round(b, 2)) for a, b, _ in sil]))
breaks = sorted(inner[:N - 1], key=lambda x: x[0])
print("breaks:", [(round(a, 2), round(b, 2), round(c, 2)) for a, b, c in breaks])
# first voice start / last voice end
first_voice = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
last_voice = sil[-1][0] if sil and sil[-1][1] >= total_audio - 0.05 else total_audio
bounds = [0.0] + [(a + b) / 2 for a, b, _ in breaks]
ends_ = [(a + b) / 2 for a, b, _ in breaks] + [last_voice + 2.4]
scenes = []
for i in range(N):
    v_start = first_voice if i == 0 else breaks[i - 1][1]
    v_end = breaks[i][0] if i < N - 1 else last_voice
    scenes.append({"id": i + 1, "start": round(bounds[i], 3), "end": round(ends_[i], 3), "voice_at": round(v_start, 3), "voice_dur": round(v_end - v_start, 3)})
total = round(ends_[-1], 3)
json.dump({"total": total, "scenes": scenes}, open(out, "w"), indent=1)
print("total", total, [(s["id"], s["start"], s["end"], s["voice_dur"]) for s in scenes])
