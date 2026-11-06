# -*- coding: utf-8 -*-
"""Lead version of shyamal/render_story.py (that file is untouched). Renders video_v2/<key>/<html>: design stills (--stills 1.5,5,...) or the video (--out file.mp4).
Usage: C:/ivtools/venv/Scripts/python.exe render_story_lead.py <key> [--html story.html] [--tl timeline.json] [--audio preview|voice.mp3|none] [--stills t1,t2] [--out renders/<key>_x.mp4]  (all paths relative to the lead folder)
Audio: --audio preview  = the 6 SAPI wavs placed at timeline voice_at (PREVIEW voice only, never sent to a lead)
       --audio file.mp3 = the real ElevenLabs MP3, played from t=0 (timeline.json must come from timeline_from_mp3.py)
       --audio none     = silent.
Run with the media venv python: C:/ivtools/venv/Scripts/python.exe render_story.py ..."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
HERE = ROOT / sys.argv.pop(1)   # lead folder: video_v2/<key>
sys.path.insert(0, str(ROOT / "shyamal"))
import toolpaths
FF = toolpaths.ffmpeg()
FPS = 30

ap = argparse.ArgumentParser()
ap.add_argument("--html", default="story.html"); ap.add_argument("--tl", default="timeline.json")
ap.add_argument("--stills", default=""); ap.add_argument("--out", default="")
ap.add_argument("--audio", default="preview")
a = ap.parse_args()
tl = json.loads((HERE / a.tl).read_text(encoding="utf-8"))
URL = (HERE / a.html).resolve().as_uri()


def open_page(p):
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 720, "height": 1280}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.goto(URL)
    pg.wait_for_function("window.READY === true", timeout=30000)
    pg.wait_for_timeout(400)
    return b, pg, errs


def audio_args():
    if a.audio == "none":
        return None
    if a.audio == "preview":
        (HERE / "voice").mkdir(exist_ok=True)
        out = HERE / "voice" / "preview_mix.wav"
        ins, fcs, labs = [], [], []
        for i, s in enumerate(tl["scenes"]):
            ins += ["-i", str(HERE / "voice" / ("s%d.wav" % s["id"]))]
            ms = int(round(s["voice_at"] * 1000))
            fcs.append("[%d:a]aresample=48000,aformat=channel_layouts=mono,adelay=%d|%d[a%d]" % (i, ms, ms, i)); labs.append("[a%d]" % i)
        fc = ";".join(fcs) + ";" + "".join(labs) + "amix=inputs=%d:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[o]" % len(labs)
        r = subprocess.run([FF, "-y", *ins, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", str(out)], capture_output=True, text=True)
        if r.returncode:
            sys.exit("audio mix failed: " + r.stderr[-400:])
        return out
    p = (HERE / a.audio).resolve()
    (HERE / "voice").mkdir(exist_ok=True)
    out = HERE / "voice" / "real_norm.wav"
    r = subprocess.run([FF, "-y", "-i", str(p), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1", str(out)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("audio normalise failed: " + r.stderr[-400:])
    return out


with sync_playwright() as p:
    if a.stills:
        outd = HERE / "stills"; outd.mkdir(exist_ok=True)
        b, pg, errs = open_page(p)
        for t in [float(x) for x in a.stills.split(",")]:
            pg.evaluate("setT(%s)" % t); pg.wait_for_timeout(80)
            pg.screenshot(path=str(outd / ("t%05.2f.png" % t)))
        b.close(); print("stills ->", outd, "| page errors:", errs[:5]); sys.exit(0)
    if not a.out:
        sys.exit("give --stills or --out")
    outp = (HERE / a.out).resolve(); outp.parent.mkdir(parents=True, exist_ok=True)
    frames = HERE / "frames_tmp"; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
    b, pg, errs = open_page(p)
    n = int(round(tl["total"] * FPS))
    for i in range(n):
        pg.evaluate("setT(%s)" % (i / FPS))
        pg.screenshot(path=str(frames / ("f%05d.jpg" % i)), type="jpeg", quality=92)
    b.close()
    if errs: print("page errors:", errs[:5])
    aud = audio_args()
    cmd = [FF, "-y", "-framerate", str(FPS), "-i", str(frames / "f%05d.jpg")]
    if aud: cmd += ["-i", str(aud)]
    # JPEG frames are full range: convert to TV range (limited) like the older campaign videos; pad the audio so the silent tail (disclaimer/arrow) stays on screen
    cmd += ["-vf", "scale=in_range=pc:out_range=tv:flags=bicubic,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
            "-color_range", "tv", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    if aud: cmd += ["-af", "apad", "-c:a", "aac", "-b:a", "128k"]
    cmd += ["-t", str(tl["total"]), "-movflags", "+faststart", str(outp)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("encode failed: " + r.stderr[-500:])
    shutil.rmtree(frames, ignore_errors=True)  # the ~1000 jpg frames are not needed after encoding
    print("OK", outp, round(outp.stat().st_size / 1e6, 1), "MB", round(tl["total"], 1), "s")
