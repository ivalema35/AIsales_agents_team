# -*- coding: utf-8 -*-
# Word-level transcript of a narrator MP3 (faster-whisper medium, cached in the scratchpad).  usage (ASR venv python): transcribe_en.py <audio.mp3> <words.json> ["prompt words"]
import json, os, sys
from pathlib import Path

SP = Path(r"C:\Users\ADMINI~1\AppData\Local\Temp\claude\C--Users-Administrator-Desktop-wire-soldering\dec5451d-390d-44dc-a02c-fbc50c6d4a7c\scratchpad")
os.environ["HF_HOME"] = str(SP / "asr_models"); os.environ["HF_HUB_OFFLINE"] = "1"
from faster_whisper import WhisperModel

audio, out = Path(sys.argv[1]), Path(sys.argv[2])
prompt = sys.argv[3] if len(sys.argv) > 3 else "Namaste, we are I V Infotech, Mehsana. WhatsApp enquiry, site visit, brochure."
model = WhisperModel("medium", device="cpu", compute_type="int8", download_root=str(SP / "asr_models"))
segments, info = model.transcribe(str(audio), language="en", word_timestamps=True, vad_filter=False, beam_size=5, initial_prompt=prompt)
words, text = [], []
for seg in segments:
    text.append(seg.text.strip())
    for w in seg.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})
out.write_text(json.dumps({"duration": round(info.duration, 2), "text": " ".join(text), "words": words}, ensure_ascii=False, indent=1), encoding="utf-8")
print(round(info.duration, 2), "s |", " ".join(text))
