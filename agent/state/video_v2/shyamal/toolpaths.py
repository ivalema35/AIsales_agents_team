# -*- coding: utf-8 -*-
"""Media tools ka ek hi thikana (ffmpeg, Playwright, ASR). Pehle yeh sab session ke scratchpad me the aur har naye session me kho jaate the;
ab durable ghar = C:\\ivtools (chhota path, kyunki Windows long-path pip install todta hai). Banane ka tareeka: agent/docs/CAMPAIGN_PLAYBOOK.md -> "Tool setup".
Env se badal sakte ho: IV_TOOLS (ghar), IV_FFMPEG, IV_HF_HOME (Whisper model cache).
  python.exe  = C:\\ivtools\\venv\\Scripts\\python.exe   (playwright + imageio-ffmpeg + faster-whisper, teeno isi me)
  ffmpeg      = imageio_ffmpeg ka binary isi venv me (ya PATH ka ffmpeg, ya purane scratchpad venv)
  Whisper     = C:\\ivtools\\asr_models  (faster-whisper 'medium', English narrator ke word-times ke liye; Gujarati/Hinglish par bekaar)"""
import glob
import os
import shutil
from pathlib import Path

TOOLS = Path(os.environ.get("IV_TOOLS", r"C:\ivtools"))


def python():
    p = TOOLS / "venv" / "Scripts" / "python.exe"
    if not p.exists():
        raise SystemExit("media venv missing: %s (see agent/docs/CAMPAIGN_PLAYBOOK.md, Tool setup)" % p)
    return str(p)


def ffmpeg():
    cands = [os.environ.get("IV_FFMPEG", "")]
    cands += sorted(glob.glob(str(TOOLS / "venv" / "Lib" / "site-packages" / "imageio_ffmpeg" / "binaries" / "ffmpeg-*.exe")))
    cands.append(shutil.which("ffmpeg") or "")
    tmp = os.environ.get("TEMP", "")
    cands += sorted(glob.glob(os.path.join(tmp, "claude", "*", "*", "scratchpad", "tools_venv", "Lib", "site-packages", "imageio_ffmpeg", "binaries", "ffmpeg-*.exe")))
    for c in cands:
        if c and os.path.isfile(c):
            return c
    raise SystemExit("ffmpeg not found: pip install imageio-ffmpeg in %s or set IV_FFMPEG" % (TOOLS / "venv"))


def hf_home():
    p = Path(os.environ.get("IV_HF_HOME", str(TOOLS / "asr_models")))
    if not p.exists():
        raise SystemExit("Whisper model cache missing: %s (copy models--Systran--faster-whisper-medium there)" % p)
    return str(p)
