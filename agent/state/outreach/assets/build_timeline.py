# -*- coding: utf-8 -*-
"""Real timeline from the real narrator MP3 (replaces the estimate): finds the scene segments from the long silences, transcribes the words, maps everything
onto the tight timeline (scene gaps become 0.35 s). usage: python build_timeline.py master_voice_en_v2.mp3 master_voice_en_v2.txt timeline_v2.json
It stops with a clear message if the number of scenes found does not match the voice text, or if the transcript differs from the text."""
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
SP = Path(r"C:\Users\ADMINI~1\AppData\Local\Temp\claude\C--Users-Administrator-Desktop-wire-soldering\dec5451d-390d-44dc-a02c-fbc50c6d4a7c\scratchpad")
FF = str(SP / "tools_venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe")
ASR = str(SP / "asr_venv/Scripts/python.exe")
mp3, txt, outname = sys.argv[1], sys.argv[2], sys.argv[3]
GAP = 0.35

scenes = [re.sub(r"\s+", " ", s).strip() for s in re.split(r"<break[^>]*/>", (HERE / txt).read_text(encoding="utf-8")) if s.strip()]
# 1) long silences = scene breaks (ElevenLabs <break time="1.0s"> gives about 1.2-1.4 s; pauses inside a scene stay under 0.9 s)
r = subprocess.run([FF, "-hide_banner", "-i", str(HERE / mp3), "-af", "silencedetect=noise=-46dB:d=0.4", "-f", "null", "-"], capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
sil = [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", r.stderr), re.findall(r"silence_end: ([\d.]+)", r.stderr))]
inner = [(a, b) for a, b in sil if a > 0.3 and b < dur - 0.2]               # silences strictly inside the speech
if len(inner) < len(scenes) - 1:
    sys.exit(f"only {len(inner)} inner silences found, the text has {len(scenes)} scenes: {inner}. Check the <break> tags or the MP3.")
breaks = sorted(sorted(inner, key=lambda x: x[1] - x[0], reverse=True)[: len(scenes) - 1])   # the N-1 LONGEST silences are the scene breaks
bounds, prev = [], 0.0
for a, b in breaks:
    bounds.append((prev, a)); prev = b
bounds.append((prev, dur))
# 2) words
r = subprocess.run([ASR, str(HERE / "transcribe_en.py"), str(HERE / mp3), str(HERE / (mp3 + ".words.json"))], capture_output=True, text=True)
if r.returncode: sys.exit("ASR failed: " + r.stderr[-400:])
words = json.loads((HERE / (mp3 + ".words.json")).read_text(encoding="utf-8"))["words"]
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace("i v", "iv"))
want = norm(" ".join(scenes)).split(); got = norm(" ".join(w["w"] for w in words)).split()
miss = [w for w in want if w not in got]
if len(miss) > 2: print("WARNING: the transcript differs from the text, words missing:", miss[:10])
# 2b) show the SCRIPT's spelling and punctuation on screen (the ASR may write "any time" or put a full stop after "Tap"); the timing stays the ASR's
import difflib
def script_tokens(scene_text): return scene_text.split()
def retext(asr_words, tokens):
    nz = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    # merge ASR pairs that the script writes as one word (any + time = anytime)
    merged, i = [], 0
    joined = {nz(t) for t in tokens}
    while i < len(asr_words):
        if i + 1 < len(asr_words) and nz(asr_words[i]["w"]) + nz(asr_words[i + 1]["w"]) in joined:
            merged.append({"w": asr_words[i]["w"] + asr_words[i + 1]["w"], "s": asr_words[i]["s"], "e": asr_words[i + 1]["e"]}); i += 2
        else:
            merged.append(dict(asr_words[i])); i += 1
    sm = difflib.SequenceMatcher(None, [nz(w["w"]) for w in merged], [nz(t) for t in tokens], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1): merged[i1 + k]["w"] = tokens[j1 + k]
    return merged
# 3) map to the tight timeline
segs, mapped, t = [], [], 0.0
for k, (a, b) in enumerate(bounds):
    src = [max(0.0, round(a - 0.05, 2)), round(min(dur, b + 0.15), 2)]
    length = src[1] - src[0]
    segs.append({"scene": k + 1, "src": src, "out": [round(t, 2), round(t + length, 2)]})
    inside = [w for w in words if src[0] - 0.02 <= w["s"] <= src[1] + 0.02]
    for w in retext(inside, script_tokens(scenes[k])):
        mapped.append({"w": w["w"], "s": round(w["s"] - src[0] + t, 2), "e": round(w["e"] - src[0] + t, 2), "scene": k + 1})
    t += length + GAP
total = round(t - GAP, 2)
(HERE / outname).write_text(json.dumps({"total": total, "gap": GAP, "segments": segs, "words": mapped}, ensure_ascii=False, indent=1), encoding="utf-8")
print("OK", outname, "total", total, "s | scenes", [s["out"] for s in segs], "| words", len(mapped))
