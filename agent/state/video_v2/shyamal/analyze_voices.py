# -*- coding: utf-8 -*-
"""Objective check of the three ElevenLabs takes: Whisper (English, forced) transcript vs the script, language-detection hint, pace, break structure.
Whisper cannot judge 'sounds nice', but a wrong name or dropped word usually means the voice mumbled or mispronounced it."""
import difflib, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import toolpaths
os.environ["HF_HOME"] = toolpaths.hf_home()
from faster_whisper import WhisperModel

SCRIPT = [
    "For Shyamal Park Lane. An I V Infotech idea.",
    "One of your Diwali ads has a Send WhatsApp message button. A buyer taps it.",
    "Say it is ten forty-seven at night. A buyer asks for details.",
    "An automatic reply can send a brochure, ask three quick questions, and offer visit times, in about a minute.",
    "By morning, your team sees who asked and who picked a visit, then takes over.",
    "Want to see this for Shyamal Park Lane? Tap the button below. It says: Yes, send the demo.",
]
ref = " ".join(SCRIPT)


def norm(s):
    s = s.lower().replace("-", " ").replace("i v ", "iv ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = s.replace("forty seven", "fortyseven")
    return re.sub(r"\s+", " ", s).strip().split()


model = WhisperModel("medium", device="cpu", compute_type="int8")
res = {}
for name in ["hale", "monika", "ruhaan"]:
    f = str(HERE / ("voice_%s.mp3" % name))
    segs, info = model.transcribe(f, language="en", word_timestamps=True, vad_filter=False, beam_size=5)
    words, text = [], []
    for s in segs:
        text.append(s.text.strip())
        for w in (s.words or []):
            words.append((w.word.strip(), round(w.start, 2), round(w.end, 2), round(w.probability, 2)))
    hyp = " ".join(text)
    a, b = norm(ref), norm(hyp)
    sm = difflib.SequenceMatcher(None, a, b)
    ratio = round(sm.ratio(), 3)
    diffs = [(tag, " ".join(a[i1:i2]), " ".join(b[j1:j2])) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    # language hint on the raw audio (not forced)
    _, info2 = model.transcribe(f, language=None, beam_size=1, without_timestamps=True)
    probs = [w[3] for w in words]
    shy = [w for w in words if w[0].lower().startswith("shy") or "mal" in w[0].lower()]
    res[name] = {"ratio": ratio, "diffs": diffs, "detected_lang": info2.language, "lang_prob": round(info2.language_probability, 2),
                 "mean_word_prob": round(sum(probs) / max(1, len(probs)), 3), "min_word_probs": sorted(words, key=lambda w: w[3])[:6],
                 "n_words": len(words), "duration": round(info.duration, 2), "wpm": round(len(words) / info.duration * 60), "transcript": hyp, "shyamal_words": shy[:4]}
    print("=====", name, "match", ratio, "| lang", info2.language, res[name]["lang_prob"], "| mean word prob", res[name]["mean_word_prob"], "| wpm", res[name]["wpm"], "| dur", res[name]["duration"])
    print("  transcript:", hyp)
    print("  diffs:", diffs)
    print("  shyamal-ish words:", shy[:4])
    print("  lowest-confidence words:", [(w[0], w[3]) for w in sorted(words, key=lambda w: w[3])[:6]])
(HERE / "voice_analysis.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
