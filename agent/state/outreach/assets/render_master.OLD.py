# -*- coding: utf-8 -*-
"""Renders the master explainer video for ONE lead (personalised on-screen slots) or a few still frames for design review.
Needs: the assets folder served on http://127.0.0.1:5013 (python -m http.server 5013 --directory <assets>) and the Playwright venv from the scratchpad
(only the ASYNC api exists there). Run from any folder:
  stills:  python render_master.py --project "Pride Aura" --city Rajkot --bhk1 "3 BHK" --bhk2 "4 BHK" --stills 2,5,8.6,12,13.5,17,19.4,24,26,29,31.5,34,36.5
  video :  python render_master.py --project "Pride Aura" --city Rajkot --bhk1 "3 BHK" --bhk2 "4 BHK" --out renders/pride_aura_en.mp4
The audio = the narrator MP3 cut into the 5 scene segments (timeline.json) with 0.35 s gaps, loudness-normalised."""
import argparse, asyncio, json, shutil, subprocess, sys, urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
FFMPEG = r"C:\Users\ADMINI~1\AppData\Local\Temp\claude\C--Users-Administrator-Desktop-wire-soldering\dec5451d-390d-44dc-a02c-fbc50c6d4a7c\scratchpad\tools_venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
FPS = 30

ap = argparse.ArgumentParser()
ap.add_argument("--project", default="Pride Aura"); ap.add_argument("--city", default="Rajkot"); ap.add_argument("--time", default="10:47 PM")
ap.add_argument("--bhk1", default="3 BHK"); ap.add_argument("--bhk2", default="4 BHK")
ap.add_argument("--stills", default=""); ap.add_argument("--out", default="")
ap.add_argument("--audio", default="master_voice_en_v1.mp3")  # "none" = silent (design previews only)
ap.add_argument("--tl", default="timeline.json")
a = ap.parse_args()
tl = json.loads((HERE / a.tl).read_text(encoding="utf-8"))
q = urllib.parse.urlencode({"project": a.project, "city": a.city, "time": a.time, "bhk1": a.bhk1, "bhk2": a.bhk2, "tl": a.tl})
URL = f"http://127.0.0.1:5013/master_video.html?{q}"


async def open_page(p):
    b = await p.chromium.launch()
    pg = await b.new_page(viewport={"width": 720, "height": 1280}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    await pg.goto(URL)
    await pg.wait_for_function("window.READY === true", timeout=20000)
    await pg.wait_for_timeout(300)
    return b, pg, errs


async def main():
    async with async_playwright() as p:
        if a.stills:
            out = HERE / "stills"; out.mkdir(exist_ok=True)
            b, pg, errs = await open_page(p)
            for t in [float(x) for x in a.stills.split(",")]:
                await pg.evaluate(f"setT({t})"); await pg.wait_for_timeout(60)
                await pg.screenshot(path=str(out / f"t{t:05.2f}.png"))
            await b.close(); print("stills ->", out, "| page errors:", errs[:5]); return
        if not a.out:
            sys.exit("give --stills or --out")
        outp = (HERE / a.out).resolve(); outp.parent.mkdir(parents=True, exist_ok=True)
        frames = HERE / "frames_tmp"; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
        b, pg, errs = await open_page(p)
        n = int(round(tl["total"] * FPS))
        for i in range(n):
            await pg.evaluate(f"setT({i / FPS})")
            await pg.screenshot(path=str(frames / f"f{i:05d}.jpg"), type="jpeg", quality=92)
        await b.close()
        if a.audio == "none":                                   # silent preview video
            cmd = [FFMPEG, "-y", "-framerate", str(FPS), "-i", str(frames / "f%05d.jpg"), "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=mono", "-t", str(tl["total"]), "-vf", "scale=in_range=pc:out_range=tv:flags=bicubic,format=yuv420p", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(outp)]
            r = subprocess.run(cmd, capture_output=True, text=True); shutil.rmtree(frames, ignore_errors=True)
            print("page errors:", errs[:5]); print(r.stderr[-600:] if r.returncode else f"OK (silent preview) -> {outp}"); return
        # audio: the 5 kept segments + 0.35 s of silence between them
        parts, labels = [], []
        for k, s in enumerate(tl["segments"]):
            parts.append(f"[0:a]atrim={s['src'][0]}:{s['src'][1]},asetpts=PTS-STARTPTS[a{k}]"); labels.append(f"[a{k}]")
            if k < 4:
                parts.append(f"anullsrc=r=48000:cl=mono,atrim=0:{tl['gap']},asetpts=PTS-STARTPTS[g{k}]"); labels.append(f"[g{k}]")
        fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=9[aout]"
        # ffmpeg reads the audio as input 1 AFTER the frames (input 0 = frames), so the narrator MP3 is [1:a]
        fc = fc.replace("[0:a]", "[1:a]")
        cmd = [FFMPEG, "-y", "-framerate", str(FPS), "-i", str(frames / "f%05d.jpg"), "-i", str(HERE / a.audio), "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
               "-vf", "scale=in_range=pc:out_range=tv:flags=bicubic,format=yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(outp)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        shutil.rmtree(frames, ignore_errors=True)
        print("page errors:", errs[:5]); print(r.stderr[-700:] if r.returncode else f"OK -> {outp} ({outp.stat().st_size/1e6:.1f} MB)")

asyncio.run(main())
