# -*- coding: utf-8 -*-
# TEMPORARY preview narrator for timing tests only (edge-tts, robotic; NEVER sent to a lead). The real voice is the owner's ElevenLabs MP3.
import asyncio, re, subprocess, sys
from pathlib import Path
import edge_tts

HERE = Path(__file__).parent
FF = r"C:\Users\ADMINI~1\AppData\Local\Temp\claude\C--Users-Administrator-Desktop-wire-soldering\dec5451d-390d-44dc-a02c-fbc50c6d4a7c\scratchpad\tools_venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
src = (HERE / sys.argv[1]).read_text(encoding="utf-8")
out = HERE / sys.argv[2]
scenes = [re.sub(r"\s+", " ", s).strip() for s in re.split(r"<break[^>]*/>", src) if s.strip()]

async def main():
    tmp = HERE / "_tts_tmp"; tmp.mkdir(exist_ok=True)
    files = []
    for i, text in enumerate(scenes):
        f = tmp / f"s{i}.mp3"
        await edge_tts.Communicate(text, "en-IN-PrabhatNeural", rate="-6%").save(str(f))
        files.append(f)
    # concat with 1.25 s of silence between scenes, like the ElevenLabs file with its <break time="1.0s"> tags
    inputs, labels = [], []
    for i, f in enumerate(files):
        inputs += ["-i", str(f)]
    fc = []
    for i in range(len(files)):
        fc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono[a{i}]")
    seq = []
    for i in range(len(files)):
        seq.append(f"[a{i}]")
        if i < len(files) - 1:
            fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:1.25[g{i}]"); seq.append(f"[g{i}]")
    fc.append("".join(seq) + f"concat=n={len(seq)}:v=0:a=1[o]")
    r = subprocess.run([FF, "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[o]", "-b:a", "128k", str(out)], capture_output=True, text=True)
    print(r.stderr[-300:] if r.returncode else f"OK {out.name}")
asyncio.run(main())
