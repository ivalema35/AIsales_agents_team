# -*- coding: utf-8 -*-
"""Whisper word times of <key>/voice.mp3 vs the data-inf fractions of the builder (scene 2 tap, scene 4 beats, scene 5 rows, scene 6 cta). Usage: python chk_beats_lead.py <key>..."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "shyamal"))
import toolpaths
os.environ["HF_HOME"] = toolpaths.hf_home()
from faster_whisper import WhisperModel
model = WhisperModel("medium", device="cpu", compute_type="int8")
for key in sys.argv[1:]:
    D = ROOT / key
    tl = json.loads((D / "timeline_real.json").read_text(encoding="utf-8")); S = {s["id"]: s for s in tl["scenes"]}
    segs, info = model.transcribe(str(D / "voice.mp3"), language="en", word_timestamps=True, vad_filter=False, beam_size=5)
    words = [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or [])]
    print("=====", key, "dur", round(info.duration, 2))
    for i in (2, 4, 5, 6):
        s = S[i]; a, b = s["voice_at"], s["voice_at"] + s["voice_dur"]
        ws = [(w, round((st - a) / s["voice_dur"], 2)) for w, st, en in words if st >= a - 0.1 and st < b]
        print(" scene", i, "|", " ".join("%s@%.2f" % x for x in ws))
