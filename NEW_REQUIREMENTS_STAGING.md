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

## ✅ BATCH 2 — ALL 6 ITEMS MERGED into the PRD docs (2026-08-22)

User ne confirm kiya, saare Batch-2 items (12–17) teeno authoritative docs me proper phases ke roop me
likh diye gaye — bilkul wahi process jo Batch 1 (Items 1–11 → Phases 6–10) ke liye follow hua tha.

**Kahan likha gaya:**
- `MASTER_DEVELOPMENT_PRD.md` **§5B** — naye **Phase 11–15**, har phase ke steps + DoD gate
  (§9 ki gate table me **P11–P15** bhi add, aur §0/§3.1 ke table-count references bhi correct kiye).
- `AI_Sales_Intelligence_PRD_v2.md` **Chapter 17** — cognitive contract (composition as a cognitive act,
  declared-vs-inferred intent ranking, sequence-as-conversation, one-content-many-renderings,
  relevance-is-comprehension-not-seniority, cross-sell-without-hype).
- `CRM_UI_UX_PLAN.md` **§2B** — UI **Phase 10–14**, har ek apne backend phase ke saath 1:1 paired.

**Item → Phase mapping:**

| Item | Kya | Phase |
| :-- | :-- | :-- |
| 12 | Email template ka naya 8-section structure + Hostinger-jaisa HTML design, button CTAs, graceful section-skip | **Phase 11** (UI Phase 10) |
| 17 | Har outreach me AI-services cross-sell mention | **Phase 11** (Step 11.5, per-product opt-in) |
| 13 | Yes/No one-click interest + admin email/WhatsApp alert + human-readable lead reference code | **Phase 12** (UI Phase 11) |
| 14 (A+C) | 3-level follow-up ka apna-apna content + har level ke liye HTML/WhatsApp templates | **Phase 13** (UI Phase 12) |
| 14 (B) | Lead page pe per-message status (Delivered/Seen/Replied), real WhatsApp text, follow-up stage | **Phase 14** (UI Phase 13) |
| 15 | Lead page ke platform icons se same content copy karke manually share | **Phase 14** (Step 14.4) |
| 16 (A) | Company lead ke andar product-relevant person target karna (CEO nahi, engineer) | **Phase 15(A)** (UI Phase 14) |
| 16 (B) | Standalone LinkedIn/prospect finder (keyword+filter search, Apollo.io ya equivalent) | **Phase 15(B)** — independently gated |

**Item 14 ko do phases me kyun toda:** 14(A)+(C) backend follow-up content hai (Phase 13), 14(B) lead-page
UI hai — aur 14(B) + Item 15 dono `LeadDetail.jsx` ke usi conversation panel pe kaam karte hain. Alag-alag
phases me karte to ek hi screen do baar rebuild karni padti. Yehi precedent Batch 1 me bhi tha (Item 6
subject-line testing: Phase 8 me candidates bane, Phase 9 me measure hue).

**Naye data-layer objects (28 → 31):** T29 `interest_responses` (Phase 12), T30 `prospects` +
T31 `prospect_searches` (Phase 15). Naye columns: `products.ai_cross_sell_enabled`,
`outreach_logs.content_sections`, `leads.reference_code`, `whatsapp_templates.followup_level`.
**Do cheezon ke liye jaanbujh ke koi nayi table nahi banayi** — apni company ke contact details
(`system_settings` me, already dashboard-editable) aur products/services ki list (`products` table khud —
ek doosri list banate to dono time ke saath alag ho jaati).

**Sequencing (§5B.0 me poora reasoning):** 11 → 12 → 13 → 14 → 15. Structure pehle (kyunki buttons,
per-level emails, cross-channel re-render — sab section-engine ke bina possible hi nahi), phir click-capture
(button ke bina click ho hi nahi sakta), phir follow-up content (cadence machinery already proven hai,
sirf content badalna hai), phir lead-page UI (ek hi screen, ek hi baar), aur naya paid provider
(Apollo.io) sabse aakhir me — bilkul wahi risk-ordering jo Phase 10 me SMS/voice ke liye thi.

---

## Batch 2 (2026-08-22) — original raw capture, jaisa bola gaya tha

### Item 12 — Email outreach template ka poora naya structure + behtar HTML design — `MERGED` (2026-08-22)

**User ke original words (raw):** "sabse pahela point he email template me isme ye email sirf marketing jese nahi lagne chahiye log view karne ke liye majbur hojaye aisa hook first line and subject jese unke kisi customer ne bheja ho pain point ke regarding , fir ayege bullet point me unke domain ke pain points , fir hoga soltion by our product uske bhi bullet points me fir ek video url (thumbnail ke sath) jisme product ke bare me hoga video me bas uss video ka thumbnail dikhana he fir hoga cta start for 1 month free aur usme hoga demo link btn fir hoga are you intredted or not yes or no btn sath phir hoga company yani hamare compnay contact details unke contact ke liye jisme email, mobile number, website , company profile link etc last me hoga stop and footer -- ye hoga otreach mail ka template but ye har business lead ka personal content ke hisab se hoga aur isse bettre html me degine karna he bettre ui ux ke sath. aur agar koi section na bhi ho like video na ho to ye bhi handle ho jaye ye ke reqruiment he isse pahele note karo"

**Samajh (paraphrase, exact order jo user ne bataya):**

Email ka naya, fixed section-order chahiye (aaj jo bhi format hai uski jagah ya usse extend karke):

1. **Subject + first line (hook)** — marketing-jaisa bilkul na lage, aisa lage jaise koi real customer ne khud apna pain point describe karte hue message bheja ho — user ko turant open/read karne pe majboor kare.
2. **Unke domain/business ke real pain points** — bullet points me.
3. **Hamare product se solution** — unhi pain points ka jawab, bullet points me.
4. **Ek video URL, thumbnail ke saath** — product ke baare me ek video, email me sirf uska thumbnail image dikhna hai (video pehle hi build ho chuka hai Phase 9 me — thumbnail-fetch mechanism already exist karta hai).
5. **CTA: "Start for 1 month free"** — iske andar ek **Demo link button**.
6. **"Are you interested or not" — Yes/No button** — lead ka turant response capture karne ke liye.
7. **Company/contact details** — hamari company ki details (email, mobile number, website, company profile link, etc.) taaki lead humein contact kar sake.
8. **Aakhir me: Unsubscribe/STOP + footer** (compliance).

**Do explicit, non-negotiable requirements jo user ne khud bataye:**
- **Personalization**: ye poora structure fixed hai, lekin har section ka *content* har business lead ke apne real data/pain-points ke hisab se **personalized** hona chahiye — generic/copy-paste nahi.
- **Graceful section-skip**: agar koi section ke liye data available na ho (jaise video na ho kisi product ke content library me), to us section ko **cleanly skip/handle** karna hai — email tootna/adhura nahi dikhna chahiye.
- **Behtar HTML design + UI/UX** — abhi ka email HTML basic hai (plain text + linkify + thumbnail), isko genuinely achhe visual design/layout ke saath banana hai.

**Claude ka technical note (raw ke saath, existing architecture se related — abhi sirf reference ke liye, build nahi kiya):**
- Ye poora Phase 8's `message_formats` (admin-defined "sections" guideline list) ka hi ek bahut zyada specific, opinionated **default/reference template** jaisa lagta hai — matlab is exact 8-section order ko ek naya "recommended format" ke roop me kisi product ke liye set kiya ja sakta hai (already-built format-engine hi is use karega), ya phir ek naya, alag "smart HTML template" layer likhna padega jo:
  - "Yes/No — interested?" jaisa **naya interactive element** hai — abhi tak koi email me clickable Yes/No response-capture button hai hi nahi (naya real feature, koi reply-tracking se bhi jud sakta hai).
  - CTA + demo-link button, company-contact block — ye bhi naye, structured HTML components hain (abhi sirf plain linkified text + ek video-thumbnail block hai).
- Video-thumbnail mechanism (Step 9 follow-up, YouTube/Vimeo oEmbed) already bana hua hai — is naye structure me wahi reuse ho sakta hai.
- **Open questions (jab confirm karoge tab clarify karna hoga):**
  - "Yes/No — interested?" button dabane par kya hona chahiye — seedha ek reply-jaisa event record ho (jaise `inbound_conversations` me ek "YES_CLICKED"/"NO_CLICKED" signal), ya kisi landing page/form pe le jaaye?
  - Ye naya structure **sabhi products ke liye default** banega, ya per-product/per-format optional choice hoga (jaise aaj `message_formats` optional hai)?
  - Company contact-details block ke exact fields kahan se aayenge (`Config`/naya settings table, ya hardcoded company info)?

**Addendum (2026-08-22, same item — design reference):**

User ke original words (raw): "dekh hume email temaplete degined chahiye jese hostinger ka hota he normal ya text me achha nahi lagega minimum but behetre ui ux like urlke liye link nahi but btn lenge wisa kuch to tum"

**Samajh:** Design ka reference/bar — **Hostinger ke transactional/marketing emails jaisa** professional, polished HTML template chahiye — plain/minimal text me nahi jaana (achha nahi lagega), lekin bahut zyada heavy-designed bhi nahi. **URLs ke liye plain hyperlink text nahi, balki proper styled BUTTON elements** use karne hain (jaise demo-link, CTA — sab clickable buttons ki tarah dikhein, plain blue underlined link nahi).

---

### Item 13 — Yes-click par admin ko turant email/WhatsApp alert, lead ID ke saath — `MERGED` (2026-08-22)

**User ke original words (raw):** "phir agal point he har lead ka alag identifier yani unique lead id manlo email me lead ne yes dabay to wo crm me update to hoga but admin ke email ya whatsapp me bhi msg ayega ki this lead id shows intrest isse lead findout karna aur bhi assana hoga ye point add karo"

**Samajh:** Item 12 ke "Are you interested — Yes/No" button ka seedha follow-up/extension:
- Har lead ka apna **unique identifier (lead ID)** hona chahiye — reference/dikhane ke liye (note: `Lead.id` already ek UUID hai DB me, lekin user shayad ek chhota/readable ID chahta ho ya bas isi existing ID ko surface karna chahta ho — abhi clarify nahi hua, open question hai).
- Jab lead email me **"Yes" button dabaye**:
  1. CRM me turant update ho (jaise lead status "interested"/hot ho jaaye — Item 12 ka hi open-question tha).
  2. **Admin ko turant ek alert jaaye — email YA WhatsApp par** — jisme us lead ka **ID** bataya jaaye ki "is lead ID ne interest dikhaya hai."
- **Purpose**: taaki admin us specific lead ko turant, aasani se dhoondh (find out) sake CRM me — us waqt bina khud dashboard khole scan kiye.

**Claude ka technical note (raw ke saath, existing architecture se related — abhi sirf reference, build nahi kiya):**
- Isme bahut kuch already-built infra reuse ho sakta hai — Phase 6 ka admin-alert mechanism (stuck-lead/system-down alerts already email bhejte hain `Config` se), aur Phase 9 Step 9.4 ka engagement-escalation pattern (real signal par lead ko "Hot" banana + koi ek `agent_events` log) bilkul isi shape ka hai — "Yes" click bhi ek naya real signal hoga, jaisa "3+ opens" signal tha.
- WhatsApp se admin ko alert bhejna — abhi tak koi admin-facing WhatsApp alert nahi hai (sirf lead-facing WhatsApp outreach hai), ye ek naya real capability hoga agar WhatsApp wala option choose kiya.
- **Open questions (jab confirm karoge tab clarify karna hoga):**
  - Lead ID — existing `Lead.id` (UUID) hi surface karna hai, ya ek naya chhota/human-readable ID (jaise "L-0042") banega?
  - Alert **email**, **WhatsApp**, ya **dono** jaaye — ya admin dashboard se configurable ho?
  - "No" button dabane par bhi kuch hona chahiye (koi alert, ya bas silently record ho ki interested nahi hai)?

---

### Item 14 — 3-level structured follow-up content + lead-page message status/visibility + HTML+WhatsApp templates for every level — `MERGED` (2026-08-22)

**User ke original words (raw):** "jese ki ab humne lead idetifier add kar diya he ab uska process bhi behter karte he like ab follow up wala manle koi lead ne email reply nahi diya ya sirf view kiya to isme hum 3 level follow up karege like out reach ke bad 1 level agar video url bheji gayi thi to video ke sath ya phir akele uske pain point and solution ke sath video frame bheje, level 2 me uska follow up agar koi response na aye to have you check out the video or details any query you want to ask like, agar fir bhi na aaye to ek last level 3 follow up jisme company detail hogi contact ki aur jo produts and services he sare uska bullet points ke sath dikhe aur kahe ke future me apko aise services need ho to contact kare aur ye follow up me proper deley maintain ho har follow up me demo cta hona chahiye if avilable aur process lead me bhi dikhe sath me lead page me jo email and whatsaap ke msg dikhte he usme status dikhe dileverd ,seen , reply etc whatsapp me template ki jagah real msg dikhe isme aur ye emails bhi achee html templates ke sath hi jaye aur same whatsapp temaplets bhi chahiye outreach and 3 leve follow up ke liye"

**Samajh (paraphrase, alag sub-parts me tod ke):**

**(A) 3-level follow-up ka specific content-design** (abhi ka follow-up sirf ek generic "chhota nudge" hai — ye use content-specific 3-level structure me badalna hai):
- **Trigger**: lead ne reply nahi diya, ya sirf email **view/open** kiya (dono cases follow-up trigger karenge).
- **Level 1** (pehla follow-up): agar original outreach me video URL bheja gaya tha, to video ke saath follow-up bhejo; agar video nahi tha, to sirf unke pain point + hamare solution ke saath follow-up bhejo.
- **Level 2** (agar Level 1 ke baad bhi koi response nahi): ek check-in style follow-up — "did you check out the video/details? Any query you want to ask?" jaisa.
- **Level 3** (aakhri follow-up, agar Level 2 ke baad bhi response nahi): company contact details + **hamare saare products/services ki poori list bullet points me**, aur ek closing note ki "future me agar aisi services chahiye ho to contact karna."
- **Delay**: har level ke beech proper delay maintain ho (jaisa aaj `followup_cadence_days` already karta hai, e.g. [3,7] din).
- **Demo CTA har follow-up me ho, agar available ho** — sirf first-touch tak simit nahi (Item 12 ka CTA design har touch pe apply hona chahiye).

**(B) Lead page par visibility improvements:**
- Lead ka "process/stage" bhi lead page pe dikhna chahiye — matlab abhi lead kis follow-up level pe hai (outreach done, Level 1 follow-up done, Level 2 me hai, etc.) — ek visible progress/stage indicator.
- Jo email/WhatsApp messages already lead page pe dikhte hain, unme **status bhi dikhna chahiye** — Delivered / Seen / Replied, etc. (per-message status, sirf list nahi).
- **WhatsApp message list me abhi template ka naam dikhta hai — uski jagah asli, real bheja gaya message (filled-in text) dikhna chahiye.**

**(C) Template quality — sabhi levels ke liye:**
- Har follow-up email bhi Item 12 wale **achhe HTML design** ke saath jaana chahiye (sirf first-touch nahi — outreach + Level 1 + Level 2 + Level 3, sabme).
- WhatsApp ke liye bhi — outreach + teeno follow-up levels, sabke liye **proper (Meta-approved) WhatsApp templates** chahiye (abhi sirf ek generic follow-up template ka concept hai).

**Claude ka technical note (raw ke saath, existing architecture se related — abhi sirf reference, build nahi kiya):**
- **(A)** ye Phase 9 Step 9.3 ke `followup_cadence_days` + `is_followup` design ka hi extension hai, lekin abhi `is_followup` sirf ek generic boolean flag hai ("chhota nudge likho") — is naye requirement ko ek **level-aware** design chahiye (`is_followup` ki jagah/saath "follow_up_level: 1/2/3" jaisa kuch), jisse AI ko har level ka apna specific content-instruction mile.
- **(B)** "Seen" status ke liye email me already `open_count`/`read_at` tracking hai (Phase 9 Step 9.4 ka engagement-escalation isi pe based hai) — "Delivered"/"Replied" bhi already `OutreachLog.status`/`inbound_conversations` se derive ho sakta hai, sirf UI par surface karna baaki hai. WhatsApp ka "real message dikhna" — `OutreachLog.message_body` me already poora filled-in text store hota hai (Step 9.1 ke `variant_id` ke saath), sirf frontend abhi template-naam dikha raha hai uski jagah.
- **(C)** WhatsApp ke liye 3 naye follow-up templates (Level 1/2/3 ke liye) Meta se real approval lene honge (Step 9.5/9.6 ka existing AI-draft-template loop yahan reuse ho sakta hai — AI khud in teeno levels ke liye template draft kar sakta hai, QC check ke saath, phir admin approve kare).
- **Open questions (jab confirm karoge tab clarify karna hoga):**
  - "Sirf view kiya" (open hua, reply nahi) — Level 1 kab trigger ho, kitne opens/kitne din baad?
  - Kya teeno level har product ke liye same structure follow karenge, ya per-product customizable?
  - WhatsApp ke 3 naye templates — Meta approval process me time lagta hai, isliye jab tak approve na ho tab tak fallback kya hoga (aaj jaisa generic follow-up, ya WhatsApp follow-up skip)?

**Claude ka suggestion (2026-08-22, user-approved to log):** In naye 3 follow-up levels + har-touch-CTA ka result bhi **measurable** rehna chahiye — Phase 9 ka already-bana variant-tracking system (`OutreachLog.variant_id`, Step 9.1/9.2) in teeno levels ke liye bhi use ho, taaki baad me pata chal sake kaunsa level (1/2/3) sabse zyada reply/interest laata hai, sirf build karke chhod na diya jaaye.

---

### Item 15 — Lead page ke platform-icons se, usi lead ke real outreach content ko copy karke doosre channels pe manually share karna — `MERGED` (2026-08-22)

**User ke original words (raw):** "ab agala point he copy formate ka manle ye email temaplete (out reach wala ) set he ab mujhe ye copy karke uss lead ke dusre channle yani insta me ya khud email kare ke dalna he (jese abhi social queue he) wo lead page me lead specific banle aye aur lead page me sare paltform ke icons he un par click karke same formate me lead ke real otreach mssg yani lead spesific outreach msg copy ho jaye (email keliye hum html me template le rahe he to email ,wa , insta, facebook ya limnked in me ye proper handle hona chaiye) aur hum uss platform me manul share kar paye."

**Samajh:**
- Ek baar jab lead ke liye outreach content (Item 12 wala real, personalized email — pain points + solution + video + CTA) ban jaaye, to usi content ko **doosre channels ke liye bhi copy karke manually share karna** ho — jaise Instagram DM me, ya khud apne email client se manually bhejna.
- Ye bilkul jaisa **abhi ka Social Queue feature** (Step 10.3, LinkedIn/Instagram/Facebook draft-and-queue) hai, lekin isko **lead-specific** banana hai aur **seedha lead page pe** laana hai.
- Lead page pe already platform icons hain (Email/WhatsApp/Instagram/Facebook/LinkedIn — `EDITABLE_FIELDS` me already dikhte hain profile-URL ke roop me, aur Step 10.3 ka "Social outreach" card bhi already lead page pe hai). Un icons par click karne se **usi lead ka real, already-generated outreach message** (same content jo email me gaya tha) copy ho jaana chahiye, **us specific platform ke format me sahi tarike se handle karke**:
  - **Email** — HTML template (Item 12 wala poora design) jaisa hai waisa hi.
  - **WhatsApp / Instagram / Facebook / LinkedIn** — same core content (pain point + solution + CTA, etc.) ko us platform ke liye sahi tarah handle karna hai (HTML nahi chalega in platforms pe — plain/formatted text version chahiye).
- Purpose: user khud us platform (jaise Instagram) me jaake manually paste/share kar sake.

**Claude ka technical note (raw ke saath, existing architecture se related — abhi sirf reference, build nahi kiya):**
- Ye Item 12 (naya email template) aur existing Step 10.3 (Social Queue) — dono ka combination/extension hai: Step 10.3 abhi apna **alag, independent AI draft** banata hai social platforms ke liye (chhota, platform-native tone) — is naye requirement me lagta hai user chahta hai ki **wahi outreach content jo email me gaya** (same pain-point/solution framing) doosre platforms ke liye bhi reuse/reformat ho, taaki messaging consistent rahe across channels — ye Step 10.3 ke current design se thoda alag philosophy hai (naya draft vs. same content ka reformatted version), confirm karte waqt ye trade-off clarify karna hoga.
- "Copy" ka matlab — sirf ek **plain-text/clipboard copy button** (jaisa Social Queue me pehle se hai "Copy text"), koi automatic send nahi — ye project ka already-established "AI drafts, human sends manually" principle follow karta hai (Step 10.3 ka evasion-free rule).
- **Open questions (jab confirm karoge tab clarify karna hoga):**
  - Har platform ke liye alag AI draft chahiye (jaisa Step 10.3 abhi karta hai), ya bas email ka content hi ek simple text-conversion (HTML strip + reformat) karke reuse karna hai?
  - Video/CTA/company-details jaise HTML-only elements (Item 12 se) doosre platforms pe kaise represent honge (jaise WhatsApp me link + short text, Instagram me sirf text)?

**Claude ka suggestion (2026-08-22, user-approved to log):** Email-HTML aur social-platform-text — dono **ek hi "lead ka real content" (pain point + solution + assets) se generate hone chahiye**, do alag content-generation paths se nahi. Warna waqt ke saath email ka content aur social ka content ek-doosre se drift kar sakta hai (alag-alag baar regenerate hone se), aur messaging inconsistent lagega usi lead ko.

---

### Item 16 — Sahi decision-maker/relevant person ko target karna (existing company lead ke andar) + naya standalone LinkedIn profile-finder tool — `MERGED` (2026-08-22)

**User ke original words (raw):** "ab agala point linked in aur sahi outreach person ke related he man le humne kisi corporate ya aise buisiness ko lead kiya jo ek company he jisme humne company linked in ya uske email whatsapp liye he aur unhe outreach kiya but man lo wo person descion maker nahi he ya unhe hamare product me kuch sahmj nahi aya to hum ghalat person ko contact kiya he like agar me ai automation service pitch kar raha hu to mujhe company ke ceo ya hr ko nahi but uske koi engeenr ya ko ai related kam karta he ya jinhe actual me ai ke bare me pata he usse pitch karna hoga uske liye hume company ke sath unke connected emps jo cureent me bhi aise logo ke linked in bhi lane hoge jinhe abhi ke liye hum manual email and whatapp outreach kar paye , satheme ek alag se linked in profile getter chahiye jkisme ek specific keyaoword ya tag ya kuch filter se unke linked in profile get kar sake klike ai developer in mehsana , 3 years ecperiens etc aur waha se bhi hum koi product unhe pitch kar sake unke email , whatsapp nikal ke ye apollo.io se hosakta he ya koi aur rasta bhi apna sakte he."

**Samajh (do alag sub-requirements hain):**

**(A) Existing company-lead ke andar sahi person target karna:**
- Abhi jab koi corporate/company lead discover hoti hai, hum company-level LinkedIn/email/WhatsApp nikaalte hain aur outreach kar dete hain — lekin ye **galat person ho sakta hai** (decision-maker nahi hai, ya product ko samajhta hi nahi — e.g. AI-automation service pitch kar rahe hain to CEO/HR ko nahi, balki us company ka **engineer / AI-related kaam karne wala employee** ko pitch karna chahiye, jo actually samajh sake).
- Isliye us company se juде **multiple connected employees ke LinkedIn profiles** bhi lane hain (sirf ek "target person role" nahi — product ke hisab se sahi role hona chahiye, jaise AI product ke liye engineer/developer).
- Abhi ke liye ye poora automated nahi karna — bas unka email/WhatsApp nikaal ke rakhna hai taaki user **khud manually** unhe outreach kar sake.

**(B) Ek naya, standalone "LinkedIn Profile Finder" tool:**
- Ye existing company-lead-discovery pipeline se **alag/independent** feature hai.
- User specific **keyword/tag/filter** se seedha LinkedIn profiles search kar sake — jaise "AI developer in Mehsana, 3 years experience."
- Wahan se milne wale profiles ka bhi **email/WhatsApp nikaalna hai** taaki unhe bhi koi product pitch kiya ja sake.
- User ne khud suggest kiya: ye **Apollo.io** se ho sakta hai, ya koi aur tareeka/provider bhi use kar sakte hain.

**Claude ka technical note (raw ke saath, existing architecture se related — abhi sirf reference, build nahi kiya):**
- **(A)** Ye Phase 7 Step 7.4 (Hunter ke discarded person-fields) + Step 7.5 (role-targeted LinkedIn person discovery, `product.target_person_roles` se gated) ka hi extension hai — abhi Step 7.5 sirf ek admin-set role-list (jaise "CEO") ke against match karta hai; is naye ask me role ki definition **product-specific aur zyada technical/domain-relevant** honi chahiye (jaise "engineer"/"AI-savvy person" AI-automation product ke liye) — ye ek real design question hai ki ye role kaise decide hoga (admin manually set kare per product, ya AI khud product-brief se relevant designation infer kare).
- **(B)** Ye ek **naya, alag data-acquisition capability** hai — abhi existing providers Serper/SerpAPI/Hunter/B2B-provider hain (`services/data_acquisition/`), Apollo.io abhi kahin use nahi ho raha (naya provider integration hoga, agar use karna decide ho). Ye feature discovery pipeline se independent, apna alag "search LinkedIn by criteria" tool jaisa lagta hai — apna alag UI/API bhi chahiye hoga (kisi specific lead se bandha nahi hai).
- **Open questions (jab confirm karoge tab clarify karna hoga):**
  - (A) "Sahi role" kaise decide hoga per product — admin manually role list set kare (jaisa aaj `target_person_roles` hai), ya AI khud product-brief dekh ke decide kare kaunsa role technically relevant hai?
  - (A) Multiple employees mile to sab dikhengे ya top-N (kitne)?
  - (B) Apollo.io ka real account/API key hai kya (jaisa Hunter ka hai) — ya koi aur specific provider pehle se soch rakha hai?
  - (B) Ye standalone tool se mile hue "leads" kya normal `leads` table me hi jaayenge (ek naya product se linked), ya ek alag "prospect list" jaisi cheez banegi?

---

### Item 17 — Har outreach me AI-services ka cross-sell mention (chahe pitched product se match na kare) — `MERGED` (2026-08-22)

**User ke original words (raw):** "aur abhi ke duar me ai boom par he to hum har outreach me ai automation ya ai slotions , ai products tools ko force kare agar kisi lead ko hamare putch kiye product me intrest nahi he but apne business ke liye ai services lena chahte he to wo contact kar sake"

**Samajh:** Abhi AI boom chal raha hai (market trend) — isliye **har outreach** (chahe jo bhi product specifically pitch ho raha ho) me **AI automation / AI solutions / AI products/tools** ka bhi mention/push ho, taaki:
- Agar lead ko us specific pitched product me interest na ho, lekin unhe apne business ke liye **AI services chahiye ho**, to wo bhi humein contact kar sake.
- Matlab ek **cross-sell/secondary mention** — pitched product ke alawa, hamari AI capability ka bhi awareness/CTA har message me ho.

**Claude ka technical note (raw ke saath, existing architecture se related — abhi sirf reference, build nahi kiya):**
- Ye Item 12 ke naya email-template design me ek **extra section/mention** ke roop me fit ho sakta hai (jaise company-contact-details block ke paas, ya ek chhoti closing line "agar AI se related kuch chahiye ho to bhi contact karein" jaisa) — ya phir Phase 8 ke `content_assets`/`message_formats` system ka use karke ek naya "always include this AI cross-sell line" wala rule bhi ban sakta hai.
- Real tension jo dhyan me rakhna hoga: is project ka apna **zero-hallucination / buzzword-ban rule** (QC ka apna check) already generic AI-hype language (jaise "revolutionary", "cutting-edge") ko reject karta hai — is naye "AI push" ko us rule ke against jaye bina, genuinely relevant/specific tarike se likhna hoga (QC prompt me shayad ek explicit carve-out chahiye hoga is cross-sell line ke liye).
- **Open questions (jab confirm karoge tab clarify karna hoga):**
  - Ye sirf un leads ke liye ho jinka pitched product AI se related NAHI hai (taaki genuinely "cross-sell" lage), ya har outreach me hamesha ho chahe product AI-related ho ya na ho?
  - Kya ye ek fixed line/CTA hai (jaisa company-contact-details), ya AI se khud is line ko bhi personalize karna hai lead ke business ke hisab se?
  - Kya ye email + WhatsApp + social — sabhi channels me ho, ya sirf email me?

**Claude ka suggestion (2026-08-22, user-approved to log):** Ise ek **per-product optional flag** banao ("is product ke outreach me AI cross-sell line include karo — haan/nahi"), sab products ke liye force mat karo. Kuch products (jaise koi bahut specific, non-AI niche service) ke liye ye secondary mention pitch ko diluted/off-topic kar sakta hai — admin apne hisab se decide kar sake, jaisa is project ka already-established "admin boundary set kare, AI andar se kaam kare" pattern hai (`target_business_categories` jaisa).

---

