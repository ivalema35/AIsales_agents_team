# Nexus360 demo: kya banayenge, kitne ghante me, kaise dikhayenge

Tayyar: Tue 20 Oct 2026. Status: SPEC, kuch banaya ya bheja nahi gaya. Owner ke liye (Hinglish; screen par aane wala text English).
Labels: FACT = file/site se. INFERENCE = andaza. ASSUMPTION = hamara estimate (range ke saath). OPINION = meri salah.
Ghante hamare hain, Rs = ghante x Rs 500 (cost, margin nahi, ASSUMPTION low-price proposal ke mutabik).

---

## 0. Demo ka matlab aur uski seema

Demo sirf yeh dikhata hai: **pipeline chalti hai**. Yeh nahi dikhata ki customer milenge.
Hamari apni campaign: 9 contact, 0 confirmed genuine reply, 7 cold template me se 2 hi time par pahunche (FACT: `CAMPAIGN1_DIAGNOSIS_2026-10-20.md`). Isliye demo me koi reply rate, forecast, demo count ya "customer aayenge" nahi.

Demo me kabhi nahi: price, follow-up ka calendar, booking, doosre states ka automation (MP automatic nahi: robots.txt), "instant", "guaranteed", Reddit ki unverified posts, Nexus360 ka koi price jo usne publish nahi kiya.

Trigger: demo tab banta hai jab Sridhar ne `requirements.md` ke Q1 se Q5 ke jawab diye (jagah, size, kise, volume, assets). Uske bina sirf Tier 0 aur Tier 1 (section 3).

---

## 1. Nexus360 ko aasan bhasha me (demo ki bhasha yahi hogi)

Sab FACT hai nexus360.in se (earlier workstream ne 20 Oct ko padha), jahan "INFERENCE" likha hai wahan nahi.

1. Nexus360 = builders ke liye **ERP + CRM**. ERP matlab "company ka hisaab-kitaab software". CRM matlab "customer aur lead ka record".
2. Site side: BOQ (kaam ke liye planned material ki quantity), indent (site se material ki maang), purchase order (supplier quotes ki tulna), inward receipt, project-wise stock aur kharcha.
3. Sales side: lead capture, follow-up aur site-visit plan, deal pipeline, payment schedule, collection.
4. AI: English me sawal puchne par live data se jawab (table ya chart).
5. Phone aur desktop dono par chalta hai. Multi-company aur white-label bhi.
6. Banane wale: GreyBoard Consulting (Rajnandgaon, Chhattisgarh). Site par 20+ projects aur 200+ log ka claim. Customers sab Rajnandgaon-Durg-Bhilai-Raipur belt me (naam site par hain; outreach me unka naam sirf permission par).
7. Price public nahi ("Ask for pricing").
8. **Kaun khareedta hai** (INFERENCE): builder owner/MD, purchase head, accounts head. Naya project register hone par site setup shuru hota hai: yeh ek natural trigger hai (jaanch nahi hui, sirf soch).
9. **Hum kya bech rahe hain (Sridhar ko)**: software nahi. Hum bechte hain: (a) register se builder dhundhna, (b) asli owner/decision-maker ki research confidence label ke saath, (c) Nexus360 ke naam se personalised pehla message + page + video, (d) genuine reply Sridhar ko turant, (e) dashboard. Baat Sridhar karta hai. Hum owner se baat nahi karte.
10. **Dhyan me rakhna**: builder ki zaroorat "dekhi" nahi gayi, sirf maani gayi (campaign 1 se sabak). RERA ka phone owner ka nahi hota. Sridhar ke apne customers ko prospect ki tarah kabhi mat dikhana.

---

## 2. Kya banayenge (6 cheezein), kitne ghante

| # | Cheez | Kaise | Sridhar se kya chahiye | Hamare ghante (L / Base / H) |
|---|---|---|---|---|
| D1 | CG builder list (funnel 2,173 se 72) | `cg_rera_demo.py` dobara chalana: uske districts, size rule, customers ki exclusion list ke saath. Ek hi GET, 11 MB, koi login/CAPTCHA nahi. Size ke liye filed project cost chahiye to detail page 13 sec per builder (72 builder = ~16 min machine, ASSUMPTION) | Q1, Q2, Q11 ke jawab | 1 / 1.5 / 3 |
| D2 | Asli owner ke dossier, 5 se 10 builder | Register detail + builder ki apni site + company listing, har fact par source aur date. Confidence: VERIFIED / LIKELY / UNKNOWN. Screen par masked | Q2 ka jawab | 1.8 / 2.5 / 3.8 (8 builder; 5 builder 1.3 / 1.8 / 2.6, 10 builder 2.2 / 3.0 / 4.7) |
| D3 | Nexus360 page + 15 se 20 sec video | Page template + animatic pehle se bane hain (17.0 sec, 510 frames). Uski recordings dal kar render. 3 sample builder (kalpnik naam) ke version | Q5: screenshots/recordings, logo, voice | 2.5 / 4 / 6 |
| D4 | ek SAMPLE WhatsApp, sirf owner ke phone par | Section 4 ke tareeke se | Kuch nahi (sirf claims ka OK) | 0.5 / 0.8 / 1.3 |
| D5 | Dashboard view | Maujooda `dashboard.html` me asli dossiers aur naya funnel bharna | Q10 | 3 / 4 / 6 |
| D6 | 10 minute ka script, rehearsal, claims check | Section 6 | Kuch nahi | 1 / 1.5 / 2.5 |
| | **Total hamare ghante** | | | **9.8 / 14.3 / 22.6** (lagbhag **10 / 14 / 23**) |

- **Rupaye (cost)**: 10 / 14 / 23 ghante = Rs 4,900 / 7,150 / 11,300. Plus cash cost: AI + data tools 8 builder x Rs 24 / 76 / 279 = Rs 200 / 600 / 2,200 (`unit_costs.md` ka per-builder). Total ~Rs 5,100 / 7,750 / 13,500. Voice agar hum banayein: ElevenLabs commercial plan $6 (Rs 540), agar Sridhar apni voice de to 0.
- **Sridhar ka time**: 1.5 se 2.5 ghante (2 screen recording 30 se 60 min, Hindi voice 4 clip 30 se 60 min, logo/permission 20 min, claim lines padhna 20 min; `page_video_effort.json`) + 30 min demo dekh kar likhit OK. Kul 2 se 3 ghante.
- **Machine time**: ~1 ghanta (register detail pages ~16 min, dossier ke liye AI ~4 min per builder, video render 40 se 90 sec each). Bina dekhe chalta hai.
- **Kitne din**: Sridhar ki recordings milne ke baad 3 working din (ASSUMPTION): din 1 list + dossiers + page, din 2 video + sample + dashboard, din 3 QA + rehearsal. Critical path = uski recordings.
- Per-builder marginal (agar scale karein): dossier 10 / 15 / 25 minute (register lookup 5 se 10 + QC 3 + likhna 1.5, ASSUMPTION), page check 0.5 se 2 min, video check 0.5 se 1 min.
- Agar `crm_access.md` me Option C (static dashboard generator) chuna, to D5 ke 4 ghante alag nahi: woh generator ka pehla run hai. ~4 ghante bachenge.
- Dossier me pehle ke 6 builder (E1 se E6, `enrichment.md`) kaam aa sakte hain. Tab D2 ~1 / 1.5 / 2.5 ghante, par Sridhar ka filter badlega to list badal sakti hai (bade group nikal gaye to Dee Vee jaise do nikalenge).

### Dossier me screen par kya dikhega (aur kya KABHI nahi)

Dikhega: builder ka registered naam (company/firm ka, jo register me public hai), district, project, approve date, filed project cost ka band, "RERA contact ka role" (owner / officer / consultant / unknown), owner ya decision-maker ka **role** aur confidence label, route class (enquiry line / role inbox / office landline / none), WhatsApp-capable? (yes / no / unknown), kitne sources aur kis tareekh ko dekhe.

Kabhi nahi: kisi vyakti ka naam, phone (poora ya last 4 digit), email (domain bhi nahi), ghar ka pata, detail-page ka seedha link. Individual promoter ke liye "Individual promoter, [project]". Poori values sirf hamare restricted store me.
Do jaal se bachna:
- `proposal_lowprice/enrichment/sample_records_masked.json` ko show-file mat banao. Usme abhi vyakti ke naam hain aur Dee Vee ko "VERIFIED" likha hai. Baad ke review ne dono ko LIKELY kar diya (`proposal_lowprice/owner_notes.md` point 5). Dashboard aur PDF LIKELY dikhate hain, wahi rakhna.
- `dashboard.html` ke table me sirf 4 builder ke result hain (Likely / Unknown), baaki 11 "Not researched". Naya table bharne ke baad ek baar screen par check karo.

---

## 3. Sridhar ke jawab se PEHLE kya dikha sakte hain

**Tier 0: abhi dikha sakte hain** (sab `proposal_lowprice/` me bane hue hain, kuch naya nahi banana)

| File | Kya dikhata hai | Dhyan |
|---|---|---|
| `dashboard/dashboard.html` | Register se list tak ka funnel (asli), pipeline (SAMPLE, invented numbers, grey label), 15 builder ka table, "one builder end to end", hand-off card | Funnel ke beech ke numbers (146, 135, 131) replay se thoda alag (151, 140, 136); summary file wale rakhe hain. Table me sirf 4 row ka result |
| `page_video/builder_page_sample.html` (`?builder=Sample+Builders&project=Sample+Heights&city=Durg`) | Page, 5 fields bharte hue, "Book a demo on WhatsApp" button ka preview (message typed, Send nahi dabta) | Amber boxes = uski recordings ki jagah. Hindi lines ka native check nahi hua |
| `page_video/video_animatic.html`, `video_storyboard.html`, `stills/` | 17 sec ka storyboard aur animatic, Hindi cut aur English cut | Rendered MP4 abhi nahi hai. Animatic ko silent MP4 banana ~40 sec machine, optional |
| `cg_rera_demo_summary.txt` | Asli funnel 2,173 se 72 | Isme koi contact data nahi |

**Tier 1: sirf INTERNAL rehearsal** (public nexus360.in material, Sridhar ko NAHI dikhana, host nahi karna)
- Nexus360 jaisa dikhne wala page public site ke text aur screenshots se banao: layout, Hindi font, lambe naam ka overflow, video ka time aur size (16 MB limit se bahut neeche) check karne ke liye.
- Poora sample-message raasta owner ke phone par kalpnik naam se test karo (section 4).
- Har cheez par "INTERNAL TEST" likho. Claim sirf wahi jo `page_video_effort.json` ke `claims_ledger` me hai aur "from site; confirm" jaisa label ho.
- Yeh kaam D3 aur D4 ka hi hissa hai (jaldi kiya gaya), alag ghante nahi: ~2 se 3 ghante is Tier me jaate hain.
- Fayda: jab Sridhar ke asli assets aate hain to sirf swap karna hota hai, 3 din ka plan 2 din me ho sakta hai (ASSUMPTION).

**Tier 2: uske jawab ke baad** (D1 se D6 poora)

---

## 4. Ek SAMPLE WhatsApp message: sirf aapke apne phone par

### Raasta (kyun yehi, aur kyun koi aur nahi)

- Hamare tool `agent/tools/send_owner_file.py` ka receiver tay hai: `owner_numbers[0]` (`agent/config.json`). `--to` option hai hi nahi. Isliye woh kisi builder ya Sridhar ko bhej hi nahi sakta. Video + caption = **ek hi message**, jo asli video-header template message jaisa dikhta hai.
- Shart: aapka 24 ghante ka window khula ho (aap us din business number par ek message likh do). Window band ho to tool kuch nahi bhejta (email fallback nahi).
- File sirf `agent/state/assets/` ya `agent/state/drafts/` ke andar, mp4 16 MB tak (hamari video 1.5 se 3 MB hogi, ASSUMPTION), caption 900 characters tak.
- Pehle `--dry-run`, phir live. Isme `--live` ya approval code nahi lagta kyunki asar sirf aapke phone tak hai (docstring: `send_owner_file.py`).
- **Kabhi nahi `wa.py send-template`**: usme koi bhi number dal sakte hain.

### Hamare +1 business number wale raaste se kyun bachna hai

- Us number par kisi bhi non-owner ka message aata hai to CRM ka demo responder (ON 16 Oct se) aur OpenAI wala sales agent (ON 19 Oct 17:55 se) jawab de dete hain (FACT: `agent/memory.md`). Agar Sridhar ya koi builder wahan likhe to unhe hamari real-estate WhatsApp automation ki pitch milegi. Galat brand, galat baat.
- Sirf server par registered owner number is se bacha hai: woh "owner message" ban kar `owner_inbox` me jaata hai aur AI tak nahi pahunchta. Hamari company ka koi aur phone ya doosra number **bacha nahi hai**: uska reply AI agent tak jaayega. Isliye sample sirf `owner_numbers[0]` par.
- Aap sample ka reply karoge to fast lane (aapka apna assistant) jawab de sakta hai. Woh theek hai, builder-facing nahi.

### Sample message ka draft (English, 60 words)

Yeh draft hai. Asli text Sridhar ke saath tay hoga. Naam kalpnik hain, asli builder ka naam nahi.

```
SAMPLE - NOT SENT TO ANY BUILDER. Test message to IV Infotech only.

Hello, this is IV Infotech, writing on behalf of Nexus360 (ERP and CRM for builders). We saw Sample Heights, Durg on the Chhattisgarh RERA register. One question: are material indents and site stock tracked in Excel or in software today? If this is not relevant, reply STOP.
```

Pehle ke jaanch-bindu (sab hone chahiye):
1. `crm.py health` me `owner_routing` = enabled.
2. Caption "SAMPLE" se shuru, 900 se kam characters.
3. Koi asli builder ka naam, phone, email nahi. Link nahi (page host nahi hua; asli send par link template me jaayega).
4. Video 16 MB se kam. File `agent/state/assets/` ke andar.
5. `--dry-run` clean.
6. Sender aapke phone par +1 "IV Infotech" dikhega. Asli send +91 number se hoga: demo me uska ek **MOCK** screenshot alag dikhana, "MOCK" label ke saath.

### Sridhar ke phone par kab (aur kaise)

- **Kabhi nahi** jab tak Sridhar ka likhit OK na ho. OK ke baad bhi hamari +1 line se nahi: jab tak forward-only bana nahi hai, uska reply AI agent tak jaa sakta hai.
- Tab tak: aap apne **personal WhatsApp** (jis par Sridhar ke saath baat hoti hai) se uska screenshot ya screen recording forward kar do. Woh hamare business number ke raaste se bahar hai.
- Pilot ke liye +91 number aur forward-only ke baad hi koi asli send.

---

## 5. Dashboard ka view (demo me)

- Tier 0 ka `dashboard.html` base. Sirf yeh badalna: (1) funnel taaza run ke numbers se, (2) builder table me 5 se 10 asli dossier (role + confidence + route), (3) "Sample" label wale pipeline numbers jaise ke taise, grey label ke saath, (4) hand-off card SAMPLE ke label ke saath.
- Console ka live client view demo me mat dikhao. Pehle `crm_access.md` ka faisla.
- Sridhar ko sirf baat batani hai: "yeh har hafte ka view hai. Jahan abhi 0 hai wahan 0 hi dikhega."
- Ghante: D5 me.

---

## 6. 10 minute ka screen-share script (aap bolenge, Hinglish)

Pehle ek baar khud rehearsal (20 min). Screen par sirf dashboard, page aur phone ka screenshot.

| Samay | Kya dikhana | Aap kya bolo (chhota) | Ruko |
|---|---|---|---|
| 0:00 to 0:45 | Dashboard ka upar ka hissa | "Aaj ek builder ka poora safar dikhata hoon: register se list, asli owner ki research, pehla message, jawab aapke paas. Koi result ka vaada nahi, sirf pipeline." | Koi number badhakar mat bolna |
| 0:45 to 2:45 | "From the register to the first list" | "Yeh Chhattisgarh RERA ki asli list hai: 2,173 projects. Har filter likha hua hai. Isme phone nahi hota, aur jo hota hai wo aksar owner ka nahi hota: aapne sahi kaha." MP: "MP RERA bots ko mana karta hai, isliye wahan haath ki list." | "Small/medium" register ka field nahi, stand-in rule hai: yeh bol dena |
| 2:45 to 5:15 | 3 dossier: ek LIKELY, ek UNKNOWN, ek group-resolved | "Hum naam tab batate hain jab evidence ho. Warna UNKNOWN. 6 ke test me 4 ka owner mila, koi pakka nahi, ek ke paas WhatsApp wala number tha. Aise me hum us builder ko message nahi bhejte." | Naam ya number mat dikhana. Sirf role aur confidence |
| 5:15 to 7:15 | Page phone-width par, phir 17 sec ki video | "Yeh builder ke liye personalised page hai, aapke naam se, aapke screens se. Button dabane par aapke number par WhatsApp khulta hai, message pehle se likha hai, Send nahi hota." | Hindi lines "draft" bolna (native check baki) |
| 7:15 to 8:15 | Aapke phone ka screenshot (SAMPLE message) + MOCK +91 screenshot | "Yeh us din ka message hai jo builder ko jaayega. Abhi ek test hai, sirf mere phone par." | Dono par SAMPLE/MOCK ka label dikhne do |
| 8:15 to 9:30 | Hand-off card + weekly view | "Genuine reply aate hi aapko alert. Koi AI owner se baat nahi karta. Aap lete ho. Hafte me yahi view ya CSV aapko milegi." | Agar usne CRM access poocha to `crm_access.md` ke options |
| 9:30 to 10:00 | Band | "Aage badhne ke liye 6 jawab chahiye (message me bheje hain). Estimate indicative hai, jawab ke baad badal sakta hai." | Price yahan nahi bolna jab tak aapne tay nahi kiya |

### Jo nahi bolna / nahi karna
- "Instant", "guaranteed", koi reply rate, demo count, savings, ROI.
- Doosre states automated hain (sirf CG).
- Real builder ka naam, owner ka naam, phone.
- Sridhar ko +1 business number par likhne ko mat kaho.
- Hamari campaign 1 ke numbers hide mat karo: poochhe to saaf bolo (9 contact, 0 confirmed genuine reply, 7 me se 2 time par).

### Sridhar ke saval jo aa sakte hain (short jawab)
1. "Owner ka WhatsApp number do." Nahi. Test me 6 me se 0 ka verified direct number mila. Jahan published WhatsApp-wala number nahi, wahan research hoti hai par message nahi jaata.
2. "Kitne customer aayenge?" Pata nahi. Hamari pehli campaign me 9 me se 0 confirmed genuine reply. Pilot sirf coverage, delivery aur hand-off naapta hai.
3. "WhatsApp account block hua to?" Account hamara hai, risk hamara. Alag +91 number aur Meta warning par ruk jaana.
4. "MP bhi?" Automatic nahi. Permission maangne ya haath ki list ka option hai, vaada nahi.
5. "Hum aapko CRM access de dein?" Ji, optional. Aap hame batao kaunsa CRM aur API.

---

## 7. Dependencies aur kram

| # | Kya chahiye | Kisse | Kab tak | Bina uske kya |
|---|---|---|---|---|
| 1 | Q1 se Q5 ke jawab | Sridhar | din 0 | Sirf Tier 0, Tier 1 |
| 2 | Uski recordings, logo, voice | Sridhar | din 1 | Video = animatic (amber placeholder) |
| 3 | Claims ki confirmation ("20+ projects, 200+ people", customer ke naam) | Sridhar | din 1 | Page par claims nahi |
| 4 | Hindi native check, 15 minute | Koi Hindi-native (Sridhar ya hamare yahan) | din 2 | Sirf English version |
| 5 | Aapka 24-ghante window khula (us din business number par ek message) | Aap | din 2 | Sample WhatsApp nahi bhejega |
| 6 | `C:/ivtools/venv` (Playwright + ffmpeg) chalta ho | Hum | din 1 | Video render nahi |
| 7 | Likhit OK agar sample Sridhar ke phone par | Sridhar | optional | Sample sirf aapke phone par |
| 8 | Pilot ke liye (demo ke liye NAHI): +91 number, forward-only (4 se 8 ghante), Meta template approval, Hindi check | Hum / BSP | pilot se pehle | Koi asli send nahi |

Page ka host (demo me nahi chahiye): `www.ivinfotech.com/campaign/<slug>` (noindex, unlisted) par ya Sridhar ke subdomain par: yeh call par poochna (14 sawalon me nahi hai). Deploy me aapka OK code lagega; demo me page apni local file se dikhega.

---

## 8. Demo se pehle QA checklist (har cheez par haan)

1. Har claim `claims_ledger` me hai aur "from site; confirm" ya Sridhar ke OK ke saath.
2. Screen par koi vyakti ka naam, 10 se zyada digit ka number, `@` wala email, `wa.me`, `tel:` nahi. (Ek chhota script se sab HTML/CSV scan karo.)
3. Har sample cheez par SAMPLE/MOCK/INTERNAL label.
4. Confidence labels dashboard/PDF jaise hi (LIKELY, VERIFIED nahi jahan review ne kam kiya).
5. Sridhar ke customers kisi list me nahi (match registered company naam se bhi, brand se bhi).
6. Funnel ke numbers summary file se milte hain.
7. Phone width par page ka pehla screen dekha, Hindi font sahi, lambe naam par overflow nahi.
8. Sample message sirf aapke phone par gaya. Koi doosra send nahi.

## 9. Safai (demo ke baad)

Earlier rule: scratch `detail_pages/` aur `sample_25_raipur_durg.csv` (isme contacts aur bank fields the) demo ke baad delete (`nexus360_sridhar_patnaik.md`). Tier 1 ke INTERNAL page aur video bhi delete. Restricted store me poori values rakhi rahengi, retention ki date Sridhar ke saath tay hone tak.

---

## Sources

`proposal_lowprice/page_video/page_video_effort.json`, `proposal_lowprice/owner_notes.md`, `proposal/enrichment/enrichment.md`, `proposal/unit_costs/unit_costs.md`, `cg_rera_demo.py`, `cg_rera_demo_summary.txt`, `agent/tools/send_owner_file.py`, `agent/tools/notify_owner.py`, `agent/docs/AGENT_API_CONTRACT.md` (owner routing), `agent/memory.md` (demo responder, sales agent, +1 line), `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, `agent/state/side_leads/nexus360_sridhar_patnaik.md`.
