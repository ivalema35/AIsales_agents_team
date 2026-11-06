# Preview timeline from the per-scene SAPI wavs (the real timeline comes from the ElevenLabs MP3: timeline_from_mp3.py)
import json, re, subprocess, sys
sys.path.insert(0, '.')
import toolpaths
FF = toolpaths.ffmpeg()
dur = {}
for i in range(1, 7):
    r = subprocess.run([FF, "-i", "voice/s%d.wav" % i], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    dur[i] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
LEAD = {1: 0.5, 2: 0.45, 3: 0.45, 4: 0.45, 5: 0.45, 6: 0.45}
TAIL = {1: 1.5, 2: 1.3, 3: 1.0, 4: 1.6, 5: 1.3, 6: 3.0}
t = 0.0; scenes = []
for i in range(1, 7):
    d = LEAD[i] + dur[i] + TAIL[i]
    scenes.append({"id": i, "start": round(t, 3), "end": round(t + d, 3), "voice_at": round(t + LEAD[i], 3), "voice_dur": round(dur[i], 3)})
    t += d
json.dump({"total": round(t, 3), "scenes": scenes}, open("timeline.json", "w"), indent=1)
print(round(t, 2), [(s["id"], s["start"], s["end"]) for s in scenes])
