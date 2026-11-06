#!/usr/bin/env bash
# Final video for one lead, once the owner's ElevenLabs MP3 is at agent/state/video_v2/<key>/voice.mp3.
# Usage: bash agent/state/video_v2/finalize_lead.sh <key>        (key = vistara | blj | namasya | any other lead folder with lead.json)
# Steps: timeline from the MP3 (5 longest silences = scene breaks) -> HTML -> render with the real voice (audio padded, TV range, total = audio + 2.4 s)
# Output: agent/state/video_v2/<key>/renders/<key>_final.mp4. Never sends anything.
set -euo pipefail
KEY="${1:?usage: finalize_lead.sh <key>}"
cd "$(dirname "$0")"
PY="C:/ivtools/venv/Scripts/python.exe"
export PYTHONIOENCODING=utf-8
[ -f "$KEY/voice.mp3" ] || { echo "missing: $(pwd)/$KEY/voice.mp3 (drop the ElevenLabs MP3 there first)"; exit 1; }
[ -f "$KEY/lead.json" ] || { echo "missing: $KEY/lead.json"; exit 1; }
"$PY" timeline_from_mp3_lead.py "$KEY" voice.mp3 timeline_real.json
"$PY" build_story_lead.py "$KEY" timeline_real.json story_final.html
"$PY" render_story_lead.py "$KEY" --html story_final.html --tl timeline_real.json --audio voice.mp3 --out "renders/${KEY}_final.mp4"
echo "DONE: $(pwd)/$KEY/renders/${KEY}_final.mp4"
