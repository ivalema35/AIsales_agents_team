import os, sys, re, json
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "shyamal"))
import toolpaths
os.environ["HF_HOME"] = toolpaths.hf_home()
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
res = {}
for f in sorted((HERE / "_incoming").glob("*.mp3")):
    segs, info = m.transcribe(str(f), language="en", beam_size=1)
    t = " ".join(s.text.strip() for s in segs)
    low = t.lower()
    key = "vistara" if ("vistara" in low or "anahata" in low or "florenza" in low) else "blj" if ("silver" in low or "b l j" in low or "bl j" in low or "bhlj" in low) else "namasya" if "namasya" in low or "nama" in low else "?"
    res[f.name] = {"key": key, "dur": round(info.duration, 1), "text": t}
    print(f.name, "->", key, round(info.duration, 1), "|", t[:230])
json.dump(res, open(HERE / "_incoming" / "labels.json", "w"), indent=1)
