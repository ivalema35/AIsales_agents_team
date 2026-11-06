# Final videos for Vistara, BLJ and Shree Namasya

Nothing here sends anything. Everything is local build work. The preview videos use a placeholder Windows voice (SAPI, Zira) and are never for a lead.

## 1. What the owner does
Record the lead's voice script in ElevenLabs and save the MP3 as exactly this name:

| Lead | Script (already in the folder) | Drop the MP3 here |
|---|---|---|
| Vistara Group / Anahata Florenza | `agent/state/video_v2/vistara/voice_script_elevenlabs.txt` | `agent/state/video_v2/vistara/voice.mp3` |
| BLJ Infra LLP / Silver Square | `agent/state/video_v2/blj/voice_script_elevenlabs.txt` | `agent/state/video_v2/blj/voice.mp3` |
| Shree Namasya | `agent/state/video_v2/namasya/voice_script_elevenlabs.txt` | `agent/state/video_v2/namasya/voice.mp3` |

Keep the six lines and the `<break time="1.0s" />` between them (the five longest silences are the scene breaks).

## 2. One command per lead (from the repo root `C:/Users/Administrator/Desktop/AISales_agent_team`)
```
bash agent/state/video_v2/finalize_lead.sh vistara
bash agent/state/video_v2/finalize_lead.sh blj
bash agent/state/video_v2/finalize_lead.sh namasya
```
Output: `agent/state/video_v2/<key>/renders/<key>_final.mp4` (720x1280, about the audio length + 2.4 s, so the silent tail with the disclaimer and arrow stays on screen). Rendering takes about 1.5 to 2 minutes per video (three can run in parallel).

What `finalize_lead.sh <key>` runs (all with `C:/ivtools/venv/Scripts/python.exe`, `PYTHONIOENCODING=utf-8`, inside `agent/state/video_v2`):
```
python timeline_from_mp3_lead.py <key> voice.mp3 timeline_real.json
python build_story_lead.py <key> timeline_real.json story_final.html
python render_story_lead.py <key> --html story_final.html --tl timeline_real.json --audio voice.mp3 --out renders/<key>_final.mp4
```
The render keeps the Shyamal fixes: audio loudness-normalised and padded (`apad`) so the video is not cut at the end of the voice, JPEG frames converted to TV range (limited) with bt709 tags, `-t total`.

## 2b. Status 2026-10-22
The three real voice.mp3 files arrived and the finals were rendered with the command above: `<key>/renders/<key>_final.mp4` for vistara, blj and namasya (check frames: `<key>/renders/<key>_final_sheet.png`, made by `final_sheet_lead.py <key>`). The beat times (tap in scene 2, three beats in scene 4, rows in scene 5, call-to-action in scene 6) are per lead in `lead.json` -> `fx`, tuned with `chk_beats_lead.py <key>` (Whisper word times vs the fractions of each scene's voice).

## 3. Check before anything is used
1. If `timeline_from_mp3_lead.py` stops with "found only N inner silences", the MP3 does not have five clear 1 s breaks: re-record or tell me, do not guess.
2. Look at the contact sheet again with the real timings: `python contact_sheet_lead.py <key> timeline_real.json story_final.html` (writes `<key>/renders/<key>_sheet.png`).
3. Watch the MP4 once (voice says the right names: "B L J Infra", "I V Infotech").

## 4. Files (all in `agent/state/video_v2/`, Shyamal's files are untouched)
- `build_story_lead.py <key> [timeline.json] [out.html]` builds the HTML from `<key>/lead.json`; copies `_shared/assets` (fonts, IV logo, common stills) into `<key>/assets` on every build.
- `render_story_lead.py <key> ...` frames with Playwright plus ffmpeg (same flags as Shyamal's `render_story.py`).
- `timeline_from_mp3_lead.py`, `timeline_from_wavs_lead.py`, `make_voice_sapi_lead.ps1 -Key <key>` (preview voice), `contact_sheet_lead.py`.
- `gen_still_plain.py`, `gen_still_evening.py` were the two kie.ai stills (plain skyline, plain evening at home); not needed again.
- Per lead: `lead.json` (all names, sub line, ad caption, question rows, colours, logo sizing) and `renders/<key>_preview_sapi.mp4`.

## 5. Facts shown in the videos (only these)
- Vistara: Vistara Group, Anahata Florenza, Ankhol, Vadodara, villas. Ad header "Anahata Florenza" (no invented Facebook page name). Questions: Villa size? / Budget? / Buying timeline?
- BLJ: BLJ Infra LLP, Silver Square, Near 150 Ft Ring Road, Rajkot, 3 BHK flats, sample flat ready. Logo = the small Facebook profile photo (200x200), shown at 200 px in a rounded square, never enlarged.
- Shree Namasya: Atladra-Padra Road, Vadodara, 3 BHK homes, sample house ready. White wordmark logo on the dark scenes.
- Common: EXAMPLE tags, "Concept by IV Infotech" mark, independence plate in scene 1, "Independent concept by IV Infotech. Voice is AI. Not affiliated with <brand>, WhatsApp or Meta." in scene 6, no prices, no unit counts, no RERA numbers, no Diwali wording.
- Example buyer sizes in scene 5: "Villa" for Vistara, "3 BHK" for BLJ and Namasya (the only size each brand states).
