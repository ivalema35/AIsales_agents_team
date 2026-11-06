# SIDE LEAD (NOT campaign 1) - B Sridhar Patnaik / Nexus360
Kept apart on purpose (owner, 2026-10-20): different pitch, different channel (the owner's PERSONAL WhatsApp, not our business number, so the sales agent / demo responder / console never touch it), different offer ("AstraAutomate" Autonomous B2B Sales Engine). Do not count it in campaign 1 numbers.

## What happened (from the owner's screenshot, 2026-10-20)
- Earlier (11:21, a previous day): the owner sent a Hinglish pitch + a 1:24 video: Sridhar = solo developer / acting CTO of Nexus360 (construction-management app, "20+ projects, 200+ daily users"); pitch = a system that pulls active builders from RERA directories, WhatsApps them case studies (Mahavir Group / Evergreen City), does a 7-14 day automatic 3-touch follow-up and books demos on his calendar; claims "92+ staff hours and Rs 23,000+ monthly overhead saved" (unsourced); "write DEMO and I will prepare a demo for your need"; "we can deploy this in a 14-day sprint".
- 10:22 Sridhar: "Let's talk. Would love to see a demo"
- 10:23 owner: "Please share a basic requirement for demo how it should be"
- 10:27 Sridhar: "I would like to see how can it fetch data from rera and drop a message"

## What he wants (precisely)
To SEE two things end to end: (1) the data step: how the system fetches builders' data from RERA; (2) the outreach step: it "drops a message" (a WhatsApp message to a builder). He has NOT asked about price, calendar booking or the 3-touch follow-up yet. He replied within 1 and 4 minutes: warm and online.

## Unknown (ask him)
Which state's RERA, and which builders he wants to reach (size, city); whether he wants a call or a screen recording; his own WhatsApp number only if he agrees to receive a sample message.

## Honesty notes
- What exists for real: our Gujarat round-2 research (GujRERA + public web + Meta Ad Library -> 34 candidates -> 12 qualified, with evidence) and an approved WhatsApp template route. What does NOT exist: a one-click scraper for every state's RERA portal (many have captchas/forms), and proof of results: our own campaign on this engine has 0 replies from 9 and cold WhatsApp templates were delivered 2 of 7 (see agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md).
- So the demo shows that the pipeline works, not that it wins customers. Avoid repeating the unsourced savings figures to a technical buyer.

## Update 2026-10-20 (later)
- Owner sent the demo reply (RERA data + one message in his voice, asked state + builder size).
- Sridhar answered: "Best place to start is Chhattisgarh and Madhya Pradesh. Small and medium sized business. Let me know if you want to have a call".
- Next: accept the call, prepare the demo for CG + MP small/medium builders (workflow `nexus360-demo-prep`, run wf_879d3ec9-14a: CG RERA sample data, 10-state RERA access table incl. MP, outreach drafts, 2-week pilot design, skeptic review).
- Call plan given to the owner: discovery first (who buys, how customers came so far, demos/month, what he tried, capacity to run demos, success in 30 days), honest description of the engine and channel mix (WhatsApp 1:1 from his own number + email + calls + warm intros; cold templates are throttled by Meta, our own test 2 of 7 delivered, 0 replies yet), a 2-week pilot with a commitment from him (weekly 15-min review, calendar link, permission to use a customer case study), NO price quoted on the first call, no unsourced savings numbers.

## Demo prep result (workflow nexus360-demo-prep, 2026-10-20 ~11:20) - corrections the skeptic made
- CG RERA: ONE plain GET of https://rera.cgstate.gov.in/Approved_project_List.aspx returns all 2,173 projects (no login/CAPTCHA); list has NO phone/email (contacts are only on per-project detail pages: do not use them for the demo). Script: agent/state/side_leads/nexus360_demo/cg_rera_demo.py (funnel 2,173 -> 1,317 in Raipur/Durg/Rajnandgaon -> 1,127 valid -> 146 approved in 18 months -> 135 housing -> 131 non-government -> 82 'small' (<=3 registered projects) -> 80 after removing his customers -> 72 promoters). Outputs in the same folder; no contact data in any of them.
- MADHYA PRADESH: https://www.rera.mp.gov.in/robots.txt says 'User-agent: *  Disallow: /' -> we do NOT automate MP. Tell Sridhar plainly; offer to write to MP RERA for permission/API, or do manual research. (Telangana: image CAPTCHA; UP: errors; Odisha, Gujarat, Rajasthan readable.)
- 'Small/medium' is NOT a field in the register: it is a stand-in rule (3 or fewer registered projects) and must be called that.
- Do NOT show his own customers as prospects; use them only as an exclusion list (name match, with his OK), no customer details on screen. The sanitised cross-check (no person names) is nexus360_demo/2_nexus360_customers_in_cg_rera.csv.
- The 'message going out' step: only to a number we control (owner's own phone) with a visible SAMPLE prefix. Do NOT ask Sridhar to text the IV business number (the AI sales agent would answer him with IV's real-estate pitch). Follow-up sequence, calendar booking, pilot price and result forecasts are NOT part of the demo and must not be promised.
- Correct the unsourced figures from the first pitch (92 staff hours, Rs 23,000, 14-day sprint) in one line.
- Delete the scratch detail_pages/ and sample_25_raipur_durg.csv (contacts + bank fields) once the demo is done.

## CALL OUTCOME (2026-10-20, Google Meet 11:00) - what Sridhar said (owner's report)
1. RERA phone numbers are NOT the real owner: the owner is one person, the operator another, the company is registered in someone else's name. RERA-only data will not reach the real owner -> he needs the REAL OWNER's contact: research + enrichment of each builder (the way we build lead dossiers), not just the RERA list.
2. The WhatsApp API account used is OURS (the one we use in our workflow), not the client's.
3. He wants the full research/enrichment process, then messaging on WHATSAPP. He did not mention email.
4. Can the video + page we send (like campaign 1) be done for Nexus360? Yes in principle.
5. If a lead gives a GENUINE reply, Sridhar will hand off / take over himself: owners do not like talking to a bot.
6. He now wants a NUMBER: the estimated cost; and a comparison: hiring a sales employee vs our system doing the work.
7. He did not ask for a CRM; he may have one; he could give access so our system's data can be shown visually.
8. The owner has NOT shown any demo yet: the estimate must go with a demo, visually good.
Open design points this raises: sender number/brand (a +1 US-looking 'IV Infotech' line is wrong for Indian builders: prefer a +91 number and a clear brand), forward-only mode (the AI sales agent must NOT answer replies to this campaign; alert Sridhar instead), WhatsApp-only first touch has the deliverability limits we measured (2 of 7 on time), real-owner hit rate unknown (our own research named an owner for 6 of 9 leads).
