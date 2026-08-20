# NEW_REQUIREMENTS_STAGING.md — Raw Requirement Capture (Pre-Confirmation)

**Purpose:** User jab bhi koi naya change/add-on requirement deta hai, wo yahan raw (jaisa bola gaya waisa) note ho jata hai — turant PRD docs edit nahi hote. Jab user explicitly **confirm** kare, tabhi is file ke items ko `MASTER_DEVELOPMENT_PRD.md` / `AI_Sales_Intelligence_PRD_v2.md` / `CRM_UI_UX_PLAN.md` me properly likha jayega (jahan jo applicable ho), aur phir phase-wise ek-ek karke build hoga.

**Status legend:** `RAW` (diya gaya, confirm nahi hua) → `CONFIRMED` (user ne confirm kar diya, PRD me merge karna baaki) → `MERGED` (PRD docs me likh diya gaya) → `DONE` (build/deploy ho chuka).

---

## ✅ ALL 11 ITEMS MERGED into the PRD docs (2026-08-19)

User ne confirm kiya, saare items teeno authoritative docs me proper phases ke roop me likh diye gaye —
**plus** wo saare points jo pehle "hold par" the (Phase 5 ke alawa) unhe bhi inhi phases me fold kar diya.

**Kahan likha gaya:**
- `MASTER_DEVELOPMENT_PRD.md` **§5A** — naye **Phase 6–10**, har phase ke steps + DoD gate (§9 ki gate table me P6–P10 bhi add).
- `AI_Sales_Intelligence_PRD_v2.md` **Chapter 16** — cognitive/agent-layer contract (naye agent roles, channel-reality constraints, measurement→adaptation rule).
- `CRM_UI_UX_PLAN.md` **§2A** — UI **Phase 5–9**, har ek apne backend phase ke saath 1:1 paired.

**Item → Phase mapping:**

| Item | Kya | Phase |
| :-- | :-- | :-- |
| 11 | Live system monitoring | **Phase 6** (UI Phase 5) |
| 1 | Target business category + target person fields | **Phase 7** (UI Phase 6) |
| 1-addendum | Corporate LinkedIn priority + person-level LinkedIn | **Phase 7** (Step 7.5) |
| 4a, 4b | Admin-defined message format (email + WhatsApp) | **Phase 8** (UI Phase 7) |
| 7 | Content library (demo URLs, case studies) | **Phase 8** (Step 8.2) |
| 6 | Subject-line variation | **Phase 8** (candidates) → **Phase 9** (measured) |
| 5 | Multi-touch follow-up sequence | **Phase 9** (Step 9.3) |
| 8 | Engagement-based escalation | **Phase 9** (Step 9.4) |
| 4c | Admin WhatsApp template submission via API | **Phase 9** (Step 9.5) |
| 4d | AI khud adaptive templates banaye | **Phase 9** (Step 9.6) |
| 9 | Non-WhatsApp countries → SMS | **Phase 10** (Steps 10.1–10.2) |
| 2, 3 | LinkedIn / Instagram / Facebook outreach | **Phase 10** (Step 10.3 — draft-and-queue) |
| 10 | AI voice calling | **Phase 10** (Step 10.4) |

**Pehle se hold-par-rakhe points jo in phases me fold ho gaye:**

| Hold item | Kahan gaya |
| :-- | :-- |
| ⭐ Autonomous WhatsApp Template Creation & Approval Loop (2026-08-13 deferred) | **Phase 9 Step 9.6** — ab unblocked, kyunki Step 9.1/9.2 wahi real performance data de rahe hain jiske na hone ki wajah se ye defer hua tha |
| Hunter.io ke discarded person-level fields (linkedin/seniority/department/decision_maker) | **Phase 7 Step 7.4** — zero naya API cost, data already aa raha tha aur phenka ja raha tha |
| `campaign_variants` table (Phase 1 se schema me hai, kabhi likha nahi gaya) | **Phase 9 Step 9.1** |
| 604-lead social-profile backfill (offer kiya tha, chala nahi) | **Phase 7 Step 7.7** |
| `_handle_discover` city filter nahi karta | **Phase 7 Step 7.6(a)** |
| Cross-city name-collision (`find_website`/`find_phone`/`find_email`) | **Phase 7 Step 7.6(b)** |
| Multi-branch business galat branch ka contact | **Phase 7 Step 7.6(c)** |
| §12 ka "Voice SDR Agent" (Intelligence PRD ka future module) | **Phase 10 Step 10.4** + Chapter 16 §16.4/§16.6 |
| CRM UI Phase 4 (global polish) | Waise hi pending hai — Phase 5–9 ke liye blocker nahi, lekin skip bhi nahi karna |

**Do items jinka jawab "haan bana denge" nahi, "aise nahi ban sakta" hai** — Item 2 (LinkedIn) aur
Item 3 (Instagram/Facebook) ka cold-outreach part. Platform khud allow nahi karta (LinkedIn ka koi
official cold-messaging API hai hi nahi; Meta sirf reply-window me messaging deta hai). Isliye Phase 10
Step 10.3 me **draft-and-queue** design rakha hai: AI sab kuch karega (research, personalisation,
drafting) sirf **send** human karega — poora AI value, zero account-ban risk. IG/FB pe reply-window
auto-response allowed hai, wo bhi build hoga.

---

## Requirements Log

### Item 1 — Product-level "target business category" + "target person/designation" fields — `RAW` (2026-08-19)

**User ke original words (raw):** "hm product add karte waqt 2 fields lennge naye but optional, pahele target business category kis type ke category target karne he multipale add hoge, sath me target person ye bhi multipale hoge aur optional hoge ye like hoga property manager, ceo, ya koi sales manager etc iss agar koi corport company hoto hum uss perticula post wale person ka linkedin, email ya contact nikal sake contact ke liye kyuki uska business email ya contact me jaldi reach na bhi mile usse achha perticual business ke person ko contact karenge to behter rahgea"

**Samajh (paraphrase, not yet confirmed as final spec):**
- Product create/edit form me 2 naye fields add karne hain, **dono optional**:
  1. **Target business category** — kis type ki business category target karni hai (e.g. coaching center, gym, corporate office, etc.) — **multiple values** ho sakte hain ek product ke liye.
  2. **Target person / designation** — kis role/post ke person ko target karna hai (e.g. "Property Manager", "CEO", "Sales Manager") — ye bhi **multiple** ho sakta hai, aur **optional** hai.
- **Purpose/why:** agar target business ek corporate company hai, to us particular designation wale person ka **LinkedIn / email / contact** nikalne ki koshish ki jaaye — kyuki generic business email/contact pe jaldi reply na mile, us se behtar hai directly us role ke person ko contact karna (higher response chance).
- Iska connection existing LinkedIn person-level discovery capability se hai jo pehle discuss hui thi (managers/CEO/employees ka data lena) — ye field shayad discovery/scoring pipeline ko batayega ki **kis designation ko specifically dhundhna hai** us product ke liye.

**Open questions (jab confirm karoge tab clarify karna hoga, abhi sirf raw note):**
- Ye fields kahan store honge (`products` table me naya column, ya `product_strategies` jaisi kisi related table me)?
- "Target person" sirf ek discovery-hint hai (LLM/search ko batana kis designation ko dhundhna) ya isse koi hard filter/matching logic bhi banegi?
- Corporate-only apply hoga ya har business type ke liye try hoga (chhoti business jaha koi formal "CEO"/"Property Manager" designation na ho)?
- Existing lead-level LinkedIn/social discovery (already built) ke saath kaise integrate hoga — naya person-level enrichment step add hoga discovery pipeline me?

**Addendum (2026-08-19, same item — corporate LinkedIn priority + person-level LinkedIn):**

User ke original words (raw): "man le koi business me linkedin he ya hum kisi corporate lead la rahe he to unke linkedin to hoga hi to wo must needed he linkedin cantact lana aur agar humne uss product ya services me target person bhi dala he to wo post ya position wale person ka linked in bhi lana he uss corporate linked in account se if avilable taki hum usse contact kar sake"

**Samajh:**
- Agar lead ek **corporate business** hai, to uska **company LinkedIn contact lana "must needed"** hai (best-effort optional nahi, priority signal hai) — ye already-built company-level LinkedIn discovery se cover hota hai.
- Agar us product/service ke liye **"target person/designation"** field (Item 1 ka naya field) set hai, to us **specific designation wale person ka LinkedIn** bhi nikalna hai — us corporate company ke LinkedIn account/page se (e.g. company ke "People"/employees listing se us role wale person ko match karna), **if available**, taaki us particular person ko directly contact kiya ja sake.
- Ye Item 1 ke person-level enrichment ka hi extension/priority-clarification hai — company ka LinkedIn hona ek strong signal hai ki person-level lookup try karni chahiye.

---

### Item 2 — AI-driven LinkedIn messaging/outreach (question + build request) — `RAW` (2026-08-19)

**User ke original words (raw):** "kya hum ai se linkedin par mssg ya outreach kar sakte he agar haan to bhi karwana he"

**Samajh:** User poochh raha hai ki kya AI se LinkedIn par automatically message/outreach bheja ja sakta hai — agar possible ho to wo bhi build karna hai (ek naya outreach channel, email/WhatsApp ki tarah).

**Claude ka honest flag (raw request ke saath hi note kar raha hoon, taaki confirm karte waqt ye context saamne ho):**
- LinkedIn ka **official API se general/free-form cold outreach messaging automate karna practically possible nahi hai** for a normal business account — LinkedIn ki Marketing/Partner APIs sirf approved partners (ads, recruiting products) ke liye hain, generic "kisi ko bhi automated DM bhejo" wali capability nahi dete.
- Isko bina official API ke karne ka matlab hoga **browser automation se LinkedIn ka apna login/session use karke bot se messages bhejna** — ye seedha LinkedIn ke Terms of Service ke against hai, aur real risk hai: **account ban/permanent restriction**, aur ye is project ke apne existing rule (tracker.md §B — "Playwright fallback evasion-free rehna chahiye, koi bot-detection bypass nahi") ke bilkul against jaata hai jo humne khud already set kiya hai email/WhatsApp/scraping ke liye.
- **Recommendation (final decision user ki hai):** LinkedIn ko ek **contact-info source** ki tarah use karna (jo already ho raha hai/plan me hai) theek hai, lekin **automated bulk messaging LinkedIn par risky/not-recommended** hai — behtar alternative: discovered LinkedIn URL ko lead detail me dikhana taaki koi human team member manually message kare, ya AI se sirf **suggested message draft** generate karwana (jo human copy-paste karke bheje) — automation sirf research/draft tak, actual send tak nahi.
- Confirm karte waqt is trade-off pe explicitly decide karna hoga.

---

### Item 3 — Instagram/Facebook outreach (build request) — `RAW` (2026-08-19)

**User ke original words (raw):** "jese ki hum instagram aur facebook bhi laa hi rahe he aur kuch buisiness isme jyada active rahete he to hum innn platform me bhi outreach kar paye to aur beheter ho sakta he"

**Samajh:** Instagram/Facebook profile discovery to already build ho chuka hai (social-profile-capture feature) — user chahta hai ki ab in dono platforms par bhi actual **outreach (message bhejna)** kar sake, kyuki kuch businesses email/WhatsApp se zyada Instagram/Facebook par active rehti hain.

**Claude ka honest flag (same LinkedIn wali concern ka Meta-platform version, raw ke saath hi note kar raha hoon):**
- Facebook Messenger aur Instagram DM — dono ke **official Meta Graph API messaging endpoints hain** (WhatsApp jaisa hi ecosystem, Meta ka hi), lekin inki policy WhatsApp se **zyada restrictive** hai for **cold/first-contact** messaging:
  - Meta ki policy ke hisaab se business sirf un logo ko message kar sakta hai jinhone khud pehle contact kiya ho (DM, comment, story reply, "Click-to-Messenger" ad click, etc.) — ek "messaging window" ke andar.
  - WhatsApp Business API me pre-approved **template** se cold first-contact allowed hai (jo humne WhatsApp ke liye already build kiya hai) — **Facebook/Instagram ka koi equivalent "cold template" mechanism nahi hai** unsolicited outreach ke liye.
  - Matlab: kisi aisi business/person ko jisne humse kabhi interact nahi kiya, unhe **official API se pehla cold message bhejna generally allowed nahi hai.**
- Unofficial route (normal account se bot/automation se DM bhejna) — same risk jo LinkedIn wale case me bataya: **ToS violation, account ban ka risk**, aur project ke evasion-free rule ke against.
- **Recommendation (final decision user ki hai):** abhi ke liye Instagram/Facebook ko **contact-info/presence-indicator** ki tarah use karna (already ho raha hai) sahi approach hai. Agar future me koi lead khud reply/comment/DM kare, tab uss reply-window ke andar official API se revert karna feasible hai (WhatsApp ke inbound-reply flow jaisa hi pattern) — lekin **cold outreach start karna Instagram/Facebook par abhi technically/policy-wise possible nahi** jaisa WhatsApp/email me hai.
- Confirm karte waqt decide karna hoga: (a) sirf contact-info tak rakhna, (b) reply-only/inbound-triggered messaging build karna (jab lead khud pehle interact kare), ya (c) kuch aur approach.

---

### Item 4 — Admin-defined message FORMAT (structure, not content) for email + WhatsApp, AI adapts + fills content library, plus admin-submitted WhatsApp templates + AI-generated adaptive templates — `RAW` (2026-08-19)

**User ke original words (raw):** "like email he uss par normally ai ek msg banakr bhejta he but admin ek formate banake rakhe crm me like greeting ya koi aisa message jisse dekh kar turant open kare , fir unka buisness ke 2-3 week points, fir uska kese solution de sakte he wo , agar koi video url ya demo url dena he aisa sirf ek formate admin likhega (actula data nahi sirf formate ya point ) ai khud usse adpate kare lead aur product ke hisab se aur userne jo demo urls bheje ho wo email me bheje ya koi aur content usne formate me add kiya ho jo email me bhejna jaruri he lead ya product ke hisab se to bhej sake , same whatsapp me bhi ho , aur user bhi api se khud tempale banake approve hone ke liye bhej sakta he jise ai use kar sake aur abhi ai khud template nahi banata adaptivness ke sath wo bhi karna he ye point bhi add karo taki ab hum jo ai outreach karvaye wo open and read it ratio badhaye."

**Samajh (sub-points):**

**(a) Email — admin-defined FORMAT, AI adapts content:**
- Abhi AI email ka poora message khud se likh raha hai (free-form).
- User chahta hai admin CRM me ek **structural format/skeleton** define kare — actual final text nahi, sirf **structure/points**, jaise:
  1. Greeting / opening hook — kuch aisa jo dekh kar turant open karne ka mann kare.
  2. Lead ki business ke 2-3 **pain points/weak points** mention karna.
  3. Un pain points ka **solution** kaise diya ja sakta hai.
  4. Agar relevant ho to **video URL / demo URL** include karna — admin sirf ye "point/slot" define karega format me (ki yahan demo link jaani chahiye), actual URL data nahi.
- **AI is format ko har lead aur product ke hisab se adapt karega** — actual pain points/solution/wording us specific lead+product ke context se bharega.
- Agar admin ne format ke saath **actual demo URLs ya doosra content** (jaise multiple demo links, alag-alag products/leads ke liye) already provide kiya hai, to AI ko sahi content **lead/product ke hisab se pick karke** email me include karna hoga.

**(b) WhatsApp — same format/structure system:**
- Wahi structural-format approach WhatsApp messaging ke liye bhi chahiye (jaisa email ke liye bataya).

**(c) Admin/user khud WhatsApp templates bana ke Meta approval ke liye submit kar sake:**
- User (admin) CRM se hi, API ke through, naye WhatsApp templates bana ke Meta ki approval ke liye bhej sake — approved hone ke baad AI un templates ko use kare.

**(d) AI khud bhi adaptive templates generate kare (naya capability):**
- Abhi AI khud templates nahi banata. Ye naya requirement hai: AI ko khud se bhi **adaptive templates propose/generate** karne ki capability deni hai (structure wahi jo (a)/(b) me define hui — greeting/pain-points/solution/demo-slot pattern).

**Goal (explicitly stated):** AI outreach ka **open rate aur read rate** badhana — structured, hook-driven format se generic AI-written messages se better engagement.

**Open questions (jab confirm karoge tab clarify karna hoga, abhi sirf raw note):**
- Format kaha store hoga — naya DB table (e.g. `message_templates`/`outreach_formats`) jisme structure-slots ho, ya `products` se linked?
- Format **per-product** hoga ya ek global default + per-product override?
- Content library (demo URLs, attachments, etc.) admin kaise upload/manage karega CRM UI se — naya section chahiye?
- WhatsApp template submission API integration — ye Meta ki WhatsApp Business Management API (`message_templates` endpoint) use karega; kya humare paas already WABA (WhatsApp Business Account) ka API access/permissions hai iske liye?
- AI-generated templates (point d) — kya wo bhi **Meta approval ke liye submit** honge (jaise humans-created), ya sirf format-fill ke liye internal use honge free-form messaging ke andar (24h reply-window)? Cold-first-contact ke liye Meta-approved template hi mandatory hai (existing rule, tracker.md §B) — is nayi capability ka scope isi constraint ke andar rehna hoga.
- Kya AI-generated template ko bhejne se pehle **human review/approval** chahiye (jaise QC veto pattern already project me hai) — ya AI ki adaptiveness khud-mukhtar (fully autonomous) rahegi format ke andar?

---

### Item 5 — Multi-touch follow-up sequence — `RAW` (2026-08-19, Claude's suggestion, user-approved to log)

**Origin:** Claude ne suggest kiya (open/read-ratio goal se directly related), user ne "haan add karo" bola.

**Idea:** Abhi jo bhi outreach build ho raha hai wo ek single message hai. Real sales me single-touch se reply rate kam hoti hai. Agar message #1 (email/WhatsApp) ka open/reply na aaye ek defined time ke andar, to AI khud-b-khud ek defined cadence follow kar ke follow-up #2 (doosra angle/reminder, WhatsApp switch, etc.) bheje.

**Open questions:** Cadence kitne din ki hogi (configurable per product?), kitne touches tak jayega, follow-up ka content bhi Item 4 wale format-system se aayega, suppression/opt-out rules yahan bhi 100% apply honge (already project rule).

---

### Item 6 — Subject-line variation/testing for email — `RAW` (2026-08-19, Claude's suggestion, user-approved to log)

**Origin:** Claude ne suggest kiya, user ne approve kiya.

**Idea:** Open-rate ka sabse bada lever subject line hota hai. AI ek se zyada subject-line candidates generate kare per lead/product, aur best wala use kare ya rotate/test kare.

**Open questions:** "Best" kaise decide hoga (koi historical open-rate data chahiye pehle, jo abhi track ho raha hai ya nahi verify karna hoga), ya sirf lead-context ke hisab se AI judgment se pick karega.

---

### Item 7 — Content library / admin UI for demo-URLs, case-studies etc. — `RAW` (2026-08-19, Claude's suggestion, user-approved to log)

**Origin:** Claude ne suggest kiya (Item 4 ko practically support karne ke liye), user ne approve kiya.

**Idea:** Item 4 me admin ko demo-URLs/case-studies/testimonials jaisa content define karna hai jo AI lead/product ke hisab se pick kare — iske liye ek structured admin UI section chahiye (products se linked content-asset library), warna ye content kahin loosely define hoga aur AI ke liye "sahi cheez pick karo" ambiguous rahega.

**Open questions:** Content types kya-kya honge (URL, text-block, file-attachment?), per-product ya global bhi ho sakta hai kuch content, versioning chahiye ya nahi.

---

### Item 8 — Engagement-based follow-up escalation — `RAW` (2026-08-19, Claude's suggestion, user-approved to log)

**Origin:** Claude ne suggest kiya, user ne approve kiya.

**Idea:** Agar lead email 2-3 baar open kare but reply na kare, to system automatically higher-priority channel (WhatsApp, ya human-alert/manual-follow-up queue) par escalate kare — interest ka signal hai but action nahi liya, isse waste nahi hona chahiye.

**Open questions:** Email-open tracking already hai ya build karna hoga (tracking pixel/analytics), "kitne opens = escalate" threshold configurable hoga, escalation destination (WhatsApp vs human alert) kis logic se decide hoga.

---

### Item 9 — Non-WhatsApp countries: alternative outreach channel — `RAW` (2026-08-19)

**User ke original words (raw):** "out contry me jaydatar phone me whatsapp nahi hota to kya karenge wo point bhi add karna"

**Samajh:** International leads (India ke bahar — jaise existing Canada-based product/leads) ke liye WhatsApp ek reliable channel nahi hai kyuki bahut se countries me WhatsApp itna commonly use nahi hota jitna India me. Aisi leads ke liye outreach ka **alternative channel** chahiye.

**Claude ka honest flag (raw ke saath note):**
- Sabse realistic universal alternative **SMS** hai (India ke bahar bhi kaam karta hai, cross-carrier) — lekin SMS marketing/outreach har country me apne **compliance rules** ke saath aata hai (jaise US ka TCPA, Canada ka CASL, EU-side rules) — ye already is project ki existing discipline (suppression list, opt-out=100% rule) ke saath align karna hoga, bas country-specific legal nuance add hoga.
- **Email already universal hai** — cross-border sabse safe/existing channel hai, koi naya risk nahi.
- iMessage/Apple-specific automation practically feasible nahi hai (proprietary, no general API).
- Recommendation direction: **region/country ke hisab se channel-priority decide karna** — jaise `target_regions` (already ek existing product-level field hai, tracker.md §A.2 se) ka use karke system decide kare ki us region ke liye WhatsApp try kare ya seedha SMS/email-priority pe jaye.

**Open questions:** SMS provider kaunsa use karenge (Twilio jaisa), per-country compliance kaise track/enforce hoga, kya `target_regions` field hi is decision ka source-of-truth banega ya alag country-channel-mapping chahiye.

---

### Item 10 — AI voice calling: AI khud call kare leads ko — `RAW` (2026-08-19)

**User ke original words (raw):** "ek aur last me add karna call ka call ai assistance ai khud sab ko call kare"

**Samajh:** Ek naya outreach channel — **AI khud phone call kare** leads ko (voice-based outreach/AI calling assistant), email/WhatsApp/SMS jaisa hi ek aur channel.

**Claude ka honest flag (raw ke saath note, ye sabse bada/riskiest naya channel hai ab tak ki list me):**
- **Regulatory risk sabse zyada is channel me hai** — cold-calling laws email/WhatsApp se kaafi zyada strict hote hain:
  - **India:** TRAI ka National Do Not Call (DND) registry + unsolicited commercial communication rules — bina registration/consent ke business calls karna violation ho sakta hai.
  - **US:** TCPA — AI/autodialed/prerecorded calls ke liye prior express consent mandatory, violation pe per-call statutory penalty ($500–1500) hota hai — bahut high-stakes.
  - Canada/EU me bhi similar strict robocall/AI-call regulations hain.
  - Matlab: **AI cold-calling bina consent ke karna is poore project ka sabse legally-risky channel hoga**, existing email/WhatsApp/SMS se kaafi zyada.
- **Technical complexity bhi sabse zyada hai:** ek poora voice-AI stack chahiye — telephony (jaise Twilio Voice), speech-to-text, conversational LLM, text-to-speech, call recording/consent handling, aur likely complex conversations ke liye human-handoff bhi.
- **Cost bhi per-minute basis pe hoti hai** — email/WhatsApp/SMS ke per-message cost se alag/zyada model.
- Is project ki already-existing safety culture (autonomous-outreach kill-switch, QC veto, 100% opt-out rule, HUMAN_LOCKED_PARAMS) dekhte hue, AI-calling channel ko **kam-se-kam utni hi strong (ya usse zyada strong) guardrails** ke saath design karna hoga — jaise explicit consent-verification step, region-wise legal-compliance gate, aur shayad ye channel autonomous-outreach kill-switch ke bhi peeche ek **alag apna khud ka kill-switch** rakhe (calling sabse sensitive channel hone ki wajah se).

**Open questions (jab confirm karoge tab clarify karna hoga):** Kaunsa voice-AI/telephony provider use karenge, kaunse regions me pehle launch karenge (compliance simplest jaha ho), consent kaise capture/verify hoga call se pehle, kya AI fully autonomous call karega ya sirf AI-assisted (human dial kare, AI real-time suggest kare) — ye do bahut alag scope hai.

---

### Item 11 — Live system monitoring / "what's happening right now" dashboard — `RAW` (2026-08-19)

**User ke original words (raw):** "system monitoring ki system kar kya raha he abhi live me kya horahahe system runing he, leads la raha he outreach ho raha he ya kya ye sab proper assani se patachale aisa ho, system active he ya nahi ye pata chal jaye ye point bhi add karo kyuki abhi crm me ye pata nahi chal raha he ki system kya kar raha he"

**Samajh:** CRM me abhi ye clearly nahi pata chalta ki background system **live me kya kar raha hai** — kya wo active/running hai, kya abhi leads discover ho rahe hain, kya outreach ho raha hai, waghera. User chahta hai ek **real-time/live monitoring view** jisse ye sab aasani se pata chal jaye.

**Samajh (kya-kya dikhna chahiye):**
- System **active hai ya nahi** — ek clear status indicator (jaise "running"/"down").
- Live activity — abhi discovery chal raha hai, abhi outreach ja raha hai, waghera — kya ho raha hai real-time me.

**Claude ka technical note (raw ke saath, existing architecture se related):**
- Backend processes already systemd services hain VPS pe (`bos-api`, `bos-worker`, `bos-scraper`, discovery scheduler) — inka health check (`systemctl is-active` jaisa) ek simple "system active hai ya nahi" signal de sakta hai.
- Job queue (`job_queue` table) aur `agent_events` table already har action log karte hain (discovery, enrich, review, score, outreach) — is data se ek **live activity feed** banana possible hai bina naya data-collection banaye, bas ek naya read API + UI view chahiye hoga.
- Real-time dikhane ka simplest tareeka **polling** hai (har few seconds refresh) — is project ki apni philosophy ("unnecessary complexity avoid karo", jaisa n8n drop karne ka decision tha) ke hisab se WebSocket jaisi cheez ki zaroorat na ho, simple polling kaafi ho sakta hai.

**Open questions (jab confirm karoge tab clarify karna hoga):** Dashboard par kaunsi cheezein exactly dikhni chahiye (service health, current job counts by status, last N activities feed, per-product live stats)? Alert/notification bhi chahiye agar system down ho jaye (e.g. email/WhatsApp alert to admin)?

---
