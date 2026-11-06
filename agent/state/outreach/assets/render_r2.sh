#!/bin/bash
# wave 2 ke 4 videos, ek ke baad ek (har render apna frames_tmp use karta hai, isliye parallel nahi)
cd "$(dirname "$0")"
PY=/c/ivtools/venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8
r() { echo "== $1"; "$PY" render_master.py --project "$2" --city "$3" --bhk1 "$4" --bhk2 "$5" --audio master_voice_en_v2.mp3 --tl timeline_v2.json --out "renders/$1" || { echo "FAILED $1"; exit 1; }; }
r great_spaces_aaroham_en_v3.mp4 "Great Spaces Aaroham" Vadodara "4B3HK villa" "Other size"
r swagat_cilantra_en_v3.mp4 "Swagat Cilantra" Surat "3 BHK" "4 BHK Penthouse"
r parshwanath_emerald_en_v3.mp4 "Parshwanath Emerald" Adalaj "2 BHK" "Other size"
r arvind_sensora_en_v3.mp4 "Arvind Sensora" Ahmedabad "400 sq yd plot" "550 sq yd plot"
echo ALL_DONE
