import os, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "shyamal"))
import toolpaths
os.environ["HF_HOME"] = toolpaths.hf_home()
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
segs, info = m.transcribe(str(HERE / "_incoming" / "a_0400.mp3"), language="en", beam_size=5, word_timestamps=True)
ws = [(w.word.strip(), round(w.start, 2), round(w.end, 2), round(w.probability, 2)) for s in segs for w in s.words]
for w in ws:
    if 5 < w[1] < 16: print(w)
print("total words", len(ws), "dur", round(info.duration, 1))
