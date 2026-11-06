# Detailing template: where we are and what comes next (30 Oct 2026, 10:40 IST)

DONE: template iv_detailing_video_hi_v1 APPROVED by Meta (hi, MARKETING, video header, 3 quick replies); header video public at
https://www.ivinfotech.com/assets/campaign/det-studios-v1-k7q3x9/detailing_hi_v1.mp4 (sha256 af6a6881..., 5.65 MB, via agent/deploy/vps_campaign_video.sh);
owner-number test SENT 10:36 IST (approval SVDYN) and the owner tapped "हाँ, बताइए" (10:36:40) and "अभी नहीं" (10:37:14): the CRM recorded both
(owner_inbox #84 / #85, type button, label text intact) -> the tap path works; NOTHING answers a tap yet (no responder deployed), which is why "kuch nahi hua".
Window proof: NOT possible today (the owner's text "OK SVDYN" at 10:34 had already opened the 24 h window). Real proof = the first lead tap or a test after 24 h of silence.

NOT SENT TO ANY LEAD. Manual 1:1 outreach from the owner's own WhatsApp continues (TODAY_FIRST_MESSAGES_2026-10-30.txt, EXTRA_CANDIDATES_2026-10-30.txt).

NEXT (needs the owner's "build it" because of usage: weekly 92% on 30 Oct 10:40, resets Mon 2 Nov 00:30 IST; do it in a FRESH session, the context of the 29-30 Oct session was 86% full):
1. Port the reply responder (prototype in agent/state/detailing_wa/proto_reply/, design in reply_path_analysis.json):
   copy services/detailing_responder.py + detailing_config.json -> backend/services/, tests -> backend/tests/, mutate script -> backend/tests/, patch -> agent/deploy/crm_detailing_patch.py;
   rebuild detailing_config.json from reply_texts.json["responder_config"] (key iv_detailing_video_hi_v1, labels EXACT: "हाँ, बताइए" / "अभी नहीं" / "मैसेज बंद करें (STOP)");
   tighten STOP matching (whole message / strong phrase, not the bare substring "बंद": "office बंद है" must NOT suppress);
   apply the patch to local backend/api/inbound.py + services/owner_channel.py (hooks + DETAILING ON/OFF/TEST/STATUS/RUN);
   run: cd backend && venv\Scripts\python.exe -m pytest tests -q (84 demo tests + all others stay green), python tests\mutate_detailing.py (no survivors), patch twice on a temp copy, python 3.9 syntax;
   write agent/deploy/vps_crm_detailing.sh (pattern vps_crm_demo.sh) + vps_detailing_probe.sh; one independent 3-lens review (safety / lead-facing text / tests) because it changes what a lead can receive.
2. Owner says "deploy it" -> package + bash agent/deploy/vps_run.sh agent/deploy/vps_crm_detailing.sh ...; then he sends DETAILING TEST from his own WhatsApp, taps the test template again (needs a new test send + OK code) and sees the reply; only then DETAILING ON.
3. Per lead (one at a time, send-day re-check, status read after ~60 s, 3 non-deliveries = stop): propose.py wa-template --lang hi --body-param V1 --body-param V2 --header-video-url <link> --lead "<Brand>" --no-notify -> owner OK -> wa.py send-template --live --approval CODE. Params + order + holds in params.json (Arihant HOLD, Motors Inn last). Log these sends as their own channel (not Gate 1). No cold sends 6-15 Nov (Diwali).
4. Small fixes still open: wa.py param lint + --lang check + optional --log-project; read-only status script for Meta error codes; Hindi/Gujarati opt-out words in the CRM classifier (human reads inbound meanwhile).
