# Sridhar ke liye read-only view: kya lagega (aur uske CRM me leads daalna)

Tayyar: Tue 20 Oct 2026. Status: JAANCH + SPEC. Console me kuch badla nahi, kuch deploy nahi kiya.
Kiske liye: Owner (Hinglish). Sirf section 8 Sridhar ke liye hai (English).
Labels: FACT = repo ki file se dekha. INFERENCE = andaza. ASSUMPTION = hamara estimate (range ke saath). OPINION = meri salah.
Ghante hamare hain. Rs = ghante x Rs 500 (cost, margin nahi, ASSUMPTION).

---

## 1. Jawab pehle (chhota)

1. **Maujooda Agent Console ka login Sridhar ko mat do.** Us login se hamari saari leads, unke phone/email ke links, hamare Claude/Apify/video-credit ke meters aur budget dikhte hain. Console me na users hain, na roles, na "sirf ek campaign" ka filter (FACT, section 2).
2. Sabse safe aur sasta: **alag chhota console instance sirf Nexus360 ke liye** (wahi code, alag database, alag password, alag subdomain). Console ka code badalna nahi padta. Ghante: 11 / 16 / 26 (Rs 5,500 / 8,000 / 13,000), jisme data nikalne aur safai jaanchne ka kaam bhi hai. Hafte ka kaam ~0.3 se 0.5 ghanta.
3. Sabse kam jokhim: **hafte ki static dashboard file + CSV** (koi server nahi, koi login nahi). Ghante: 10 / 15 / 24 (Rs 5,000 / 7,500 / 12,000). Demo wali dashboard ka hi layout use hota hai.
4. Meri salah (OPINION): demo aur pilot ke pehle 2 hafte me **static file + CSV + aapki screen-share**. Agar Sridhar "live" maange to option A. Console ke code me "client mode" (option B) tab banao jab 3 ya zyada client hon.
5. Phone/email chhupane ka asli tareeka: login par bharosa nahi. **Jo data client wale store me jaata hi nahi, wo leak ho hi nahi sakta.** Isliye ek "allow-list wala export" banta hai (section 5), aur har file ko scan karte hain.
6. Uske CRM me leads daalna: uski API ka hame kuch pata nahi. Pehle 12 sawal (section 6). Jab tak jawab nahi, uska kharcha estimate me nahi.

---

## 2. Aaj console me kya hai (FACT, `console/` ki code se)

| Cheez | Aaj kya hai |
|---|---|
| App | Flask + SQLite, `console/app.py`. VPS par `/opt/agent-console`, gunicorn 127.0.0.1:5010, 1 worker, 4 threads, MemoryMax 300M, CPUQuota 40% (`deploy_console.sh`). Sales subdomain se LiteSpeed proxy |
| Login | **Ek hi shared password** (`CONSOLE_PASSWORD`, kam se kam 10 characters start par check). Session me sirf `owner = True`. 12 ghante ka session. 5 galat try par 10 minute ka lock, per IP, memory me (restart par reset). CSRF sirf login form par |
| Roles | **Nahi hain.** Har logged-in vyakti sab kuch dekhta hai. Kisi campaign ya tag se filter nahi |
| Browser se write | Nahi. Sirf logout. Edit screen hai hi nahi |
| Write kaun karta hai | Agent, `POST/PATCH/DELETE /v1/entries` par, ek bearer key (`CONSOLE_API_KEY`) se. Wahi key `GET /v1/entries` se **sab entries padh** bhi sakti hai |
| Entry types | product, campaign, lead, activity, metric, approval, handoff, heartbeat, engagement, event, email_event. JSON max 64 KB, depth 6. Delete = sirf `deleted_at` (soft). Har write ka audit. **Read ka audit nahi** |
| Pages | Overview (KPI, activity, pipeline, limits tile, calendar), Campaigns (calendar + table jisme budget used/cap), Leads (list + detail), Products |
| Public routes | `/login`, `/v1/health`, `/hooks/resend` (signature se), `/p/<slug>` (band jab tak `CONSOLE_PAGES_ENABLED=1` na ho) |
| Seed | Har start par 11 IV Infotech ke products daalta hai (soft-deleted wale wapas nahi aate) |
| Branding | Sidebar aur login par "Agent Console / Ivinfotech sales" fixed text |
| Tests | `console/tests/`: `test_console.py` me 31 test, baaki alag files me; `agent/memory.md` me poori console suite 169 likhi hai |
| Nexus360 | **Console me hai hi nahi.** 20 Oct ko owner ne alag rakhne ko kaha (`agent/memory.md`) |

Reuse karne layak chhoti cheezein (bina code badle): `agent/tools/console.py push FILE` (URL aur key environment se; same (type,key) dubara bhejne par update, duplicate nahi), `agent/deploy/set_vps_secret.ps1` (password hidden prompt se, chat me kabhi nahi), `console_cutover.sh` ka vhost backup/rollback tareeka.

---

## 3. Agar hum bas Sridhar ko console ka login de dein to kya leak hoga

| Kya dikhega | Kahan | Asar |
|---|---|---|
| Hamari saari doosri leads (campaign 1 ke 22 lead dossier, grade, "What could go wrong", "Why they may need us") | Leads page | Doosre businesses ki research, jo unhone kabhi allow nahi ki |
| Unke phone / email / WhatsApp, `mailto:`, `tel:`, `wa.me` links | Leads detail, "How to reach them" | Personal/contact data, DPDP aur bharose ka jokhim |
| Hamare internal meters: Claude usage, Apify spend, kie.ai credits; campaign ka budget used/cap | Sidebar, Overview, Campaigns table | Hamara cost structure (jo estimate me nahi dikhana) |
| Agent online/idle, heartbeat | Sidebar | Andar ki baat |
| Owner ki bhasha: "Nothing is sent until you approve it with an OK code", "Waiting for your review" | Leads | Sridhar ko confusing: wo "owner" nahi hai |
| "Ivinfotech sales" brand, hamare 11 products | Sidebar, Products | Off-topic |
| Ek password sab ke liye | Login | Kaun dekh raha hai pata nahi, ek ko hataya nahi ja sakta (sirf password badal kar restart) |

Baaki jokhim (INFERENCE):
- VPS par memory kam thi: 15 Oct ko ~3.1 GB available aur 3.6 GB swap use (`agent/memory.md`). Doosra gunicorn jodne se pehle `free -m` dekho. 300 MB ka cap lagta hai.
- Engagement sync (`agent/engagement/engagement_sync.py`) builder ko pehchanta hai lead entry ke **contacts ke last 4 digit** se. Client console me contacts honge hi nahi, isliye us sync ko jaise ka taisa client console par nahi chala sakte. Hamara apna feed chahiye (section 4, "F").
- Hamare apne data me bhi galat signal aaye: Great Spaces ke 7 opens me se zyada se zyada 1 asli lead tha, baaki scanner, auto-open aur hamari team ke phone (`CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, section 2 point 5). Client view me "opened / read" mat dikhao ya "noisy" label ke saath. Reply gino.
- Sridhar ko shuru me 0 dikhega. Yeh sach hai, aur dikhna chahiye. Owner decide kare ki yeh theek hai.

---

## 4. Chaar raaste: kya lagta hai

Common hissa (A, B, C teeno me chahiye):
- **W: record store + client-safe export + leak scanner**: 3 / 4 / 6 ghante. Hamare restricted store me poori values (naam, phone) rahengi, export sirf allow-list ke fields nikalega (section 5), scanner file me email, 10+ digit number, `wa.me`, `tel:`, vyakti ke naam, aur "Claude / Apify / kie / OpenAI / budget" dhoondhega.
- **F: feed**: har send, delivery, reply, hand-off ko record karna (hamare send log aur `crm.py inbound` se): 3 / 5 / 8 ghante. `engagement_sync.py` ko client ke liye reuse nahi kar sakte (section 3), isliye yeh naya chhota script hai.
- W + F = 6 / 9 / 14. `unit_costs.md` ke "read-only client dashboard 6 / 8 / 12 ghante" me yeh dono nahi the, wo sirf dikhne wale hisse ka tha. Option A ka dikhne wala hissa (neeche 5 / 7 / 11.5) usse milta hai.

### Option D: sirf screen-share (har hafte)
- Kuch banana nahi. Demo wali dashboard dikhao. 0.5 ghanta per hafte.
- Kamzori: live nahi, Sridhar akele nahi dekh sakta.

### Option C: static dashboard file + CSV (hafte me ek baar)
| Kaam | L / B / H ghante |
|---|---|
| W (store + safe export + scanner) | 3 / 4 / 6 |
| F (feed) | 3 / 5 / 8 |
| Dashboard generator (maujooda `dashboard.html` ka layout, 988 line ka hand-bana HTML, usko data se banane wala template) + CSV | 4 / 6 / 10 |
| **Total** | **10 / 15 / 24** (Rs 5,000 / 7,500 / 12,000) |
- Har hafte: script chalao, scanner chalao, phone aur desktop par ek nazar, file bhejo: 0.3 se 0.5 ghanta.
- Hosting nahi, login nahi, koi attack surface nahi. File email ya WhatsApp se jaati hai.
- Kamzori: snapshot hai, live nahi. Sridhar ko file milne tak purana data.
- Demo ka D5 (dashboard) isi generator ka pehla run ban jaata hai (~4 ghante bachte hain).

### Option A: alag console instance, sirf Nexus360 (live view, console ka code NAHI badalna)
| Kaam | L / B / H ghante |
|---|---|
| W + F (upar wale) | 6 / 9 / 14 |
| `deploy_console.sh` ki copy: naya folder (jaise `/opt/agent-console-nexus360`), naya port (jaise 5011), naya systemd unit, apni `.env`, apna database. Purani script me ye sab fixed hai (user, path, port, unit ka naam), isliye copy chahiye | 1.5 / 2 / 3 |
| Naya subdomain: DNS record, LiteSpeed vhost, TLS certificate. **Owner/hosting ke haath ke kaam**; hum guide aur check karte hain. Naya vhost hai, purane console ka cutover nahi, isliye jokhim kam | 1 / 1.5 / 3 |
| Entries bhejne wala script: ek `campaign` (calendar me pilot ke din), builder ke `lead` entries, `activity` entries, ek `product` = "Nexus360". 11 IV products ko soft-delete (stay deleted) | 1 / 1.5 / 2 |
| Leak test: client login se Playwright se har page aur har lead detail khol kar HTML save, scanner chalao, desktop + phone ke screenshot dekh kar theek karo | 1 / 1.5 / 2.5 |
| Password hidden prompt se, handover | 0.5 / 0.5 / 1 |
| **Total** | **11 / 16 / 25.5** (Rs 5,500 / 8,000 / 12,750) |
- Har hafte: 0.3 se 0.5 ghanta (feed + push + ek nazar). Availability: 24 ghante best-effort (systemd restart karta hai), koi SLA nahi, VPS shared hai. Hum business hours me support ka vaada karein, 24x7 ka nahi.
- Kyun Option A me doosre leads dikh hi nahi sakte: alag database hai. Wahi code hai, isliye kisi purane test ya feature ko chhune ki zaroorat nahi.
- Jo phir bhi dikhega: brand "Agent Console / Ivinfotech sales", sidebar me Products. Products me sirf "Nexus360" ka ek entry rakhenge (natural lagta hai). Naya brand chahiye to ek copy me template badalni padegi: 2 se 3 ghante aur ek aur fork sambhalna; meri salah: skip.
- Memory: ~100 MB typical, cap 300 MB; pehle `free -m` dekho.
- Console ke built-in "metric" aur "heartbeat" entries hum us instance me likhenge hi nahi. Isliye meters khali aur label "Waiting for the agent". Chahein to ek `heartbeat` entry likh do.

### Option B: console me "client mode" (code badalna)
| Kaam | L / B / H ghante |
|---|---|
| W + F | 6 / 9 / 14 |
| Doosra login ya signed link, session me role | 2 / 3 / 4 |
| Har query par tag/campaign ka allow-list filter (default deny), `entries()` aur API ke reads, contacts server par hi hata dena | 3 / 4 / 6 |
| Template: meters, products, heartbeat, owner-wording chhupana | 1 / 2 / 3 |
| Tests (leak tests, har route) | 2 / 3 / 4 |
| Adversarial review (pehle bhi leads page par 3-lens review se kai asli bug nikle: `agent/memory.md` section N) aur fix | 2 / 2 / 3 |
| **Total** | **16 / 23 / 34** |
- Kamzori: **jis console par hamari saari leads hain usi me code badalna.** Filter me ek galti = saari leads leak. Isliye review zaroori. Fayda tab jab bahut client hon.

### Ek nazar me

| | D screen-share | C file + CSV | A alag instance | B client mode |
|---|---|---|---|---|
| Ek baar ke ghante (L / B / H) | 0 | 10 / 15 / 24 | 11 / 16 / 25.5 | 16 / 23 / 34 |
| Har hafte | 0.5 | 0.3 se 0.5 | 0.3 se 0.5 | 0.3 se 0.5 |
| Live | Nahi | Nahi | Haan | Haan |
| Doosre leads leak ka jokhim | Nahi | Nahi | Bahut kam (alag DB) | Medium (filter ki galti) |
| Server par naya hissa | Nahi | Nahi | Haan (DNS, vhost, TLS, service) | Haan (purana console badalna) |
| Login jaisi cheez | Nahi | Nahi | Ek shared password | Naya login / link |

---

## 5. Client ko kya dikhta hai: allow-list (har option me yehi)

**Kaunse pages milenge (Option A / B):**
- Overview: funnel ke counts (researched, owner named, sent, delivered, replied, handed off), pipeline tile, hand-off wali items, 14 din ki activity line.
- Campaigns: sirf ek campaign, calendar me pilot ke din (Day 0 se Day 17). Budget column khali.
- Leads: builder list + ek builder ka detail (sirf neeche ki allow-list ke fields).
- Products: sirf ek entry, "Nexus360". (Option B me yeh page chhupa dena asaan hai; Option A me nahi, isliye ek entry rakhte hain.)
- Nahi milega: meters, agent heartbeat, doosra koi campaign ya lead (Option A me alag DB, isliye hai hi nahi).

**Link ya login?** Signed link = password nahi, jiske paas link hai wo dekh leta hai; expiry laga sakte hain, par link forward ho gaya to roka nahi ja sakta (secret badalna padta hai, sab ke link toot jaate hain). Login = ek shared password. Dono me asli suraksha yeh hai ki contact data export me hai hi nahi. Isliye Option A ke liye login hi theek hai (code nahi badalna), signed link sirf Option B me banta hai.

**Dikhega** (har builder par, public source se):
- Registered naam (company/firm; register me public). Individual promoter ho to "Individual promoter" + project.
- District, project, approve date, filed project cost ka band.
- "RERA contact ka role" (owner / officer / consultant / unknown).
- Owner/decision-maker ka **role** + confidence label (VERIFIED / LIKELY / UNKNOWN), kitne sources, kis tareekh ko.
- Route ki class: enquiry line / role inbox / office landline / none. WhatsApp-capable: yes / no / unknown.
- Stage: researched, queued, sent, delivered, replied, handed off, demo, stopped. Genuine reply alag gino (button tap aur auto-greeting nahi).
- Funnel ke counts, pilot ka calendar (Day 0 se Day 17), sample hand-off log (kab alert gaya, kab Sridhar ne liya).

**Kabhi nahi:**
- Kisi vyakti ka naam, phone (poora ya last 4 digit), email (domain bhi nahi), ghar ka pata, register detail page ka seedha link.
- Hamari doosri leads, Claude/Apify/kie/OpenAI ke meters, budget, per-builder cost, margin, hourly rate.
- Opens/reads ke "signals" (noisy). Hum sent, delivered, replied dikhate hain.
- Kuch bhi "forecast" ya "expected replies".

**Console entry likhte samay (Option A/B) in fields se bachna:**
- `contacts[]` me asli kuch mat likho (links ban jayenge). Ek hi entry rakho: kind `route`, value "Handed to you on reply" ya khali. Warna Leads detail me "No contact found yet." dikhta hai, jo bhrama deta hai.
- `best_angle`, `best_channel`: in se "Nothing is sent until you approve it with an OK code" wala owner-text aata hai. Mat likho.
- `status` me `researched`, `ready`, `queued`, `approved` mat do: unka text "Waiting for your review", "Ready for your OK" hai. Apne naye words do (jaise `owner_named`, `handed_off`). `contacted`, `replied`, `meeting` theek hain.
- `campaign` entry me `budget_used`, `budget_cap`, `unit` mat likho.
- Sab free-text (`decision_maker`, `size_cues`, `observed_facts`, `history`) hamare export se jaaye, haath se nahi.

**Leak scanner** (har release se pehle, har file par): email pattern, `PHONE_RE` jaisa 10+ digit pattern, `wa.me`, `tel:`, `mailto:`, vyakti ke naamon ki list (restricted store se), aur ye shabd: Claude, Apify, kie, OpenAI, budget, "your OK". Ek bhi hit = release nahi.

---

## 6. Sridhar ke apne CRM me leads daalna (baad me): kya poochna hai

Hame uski API ka kuch pata nahi (UNKNOWN). Nexus360 ka CRM hissa lead capture, follow-up, site-visit, deal pipeline deta hai (nexus360.in). Yeh 12 sawal pehle:

1. Kaunsa CRM wo apni sales ke liye khud use karta hai (Nexus360 ka apna, Zoho, sheet)?
2. Public ya partner API hai? Documentation ka link? Auth kaisa (API key, OAuth)? Rate limit?
3. Sandbox ya test company mil sakti hai? (Nexus360 multi-company hai.)
4. Lead me kaunse fields: naam, company, project, city, source, stage, assignee, notes, custom fields? Duplicate kaise pakadta hai?
5. Source ka naam "IV Infotech outreach" jaisa set kar sakte hain? Stage ke naam?
6. Webhook ya callback hai jisse uske stage change (contacted, demo, won) hamare dashboard tak aa sakein?
7. API na ho to: lead-capture form/endpoint, email-to-lead, ya CSV bulk import? Template aur limit?
8. Hamare liye alag integration user jo sirf lead **bana** sake (padh na sake)? IP allow-list? Kill switch? Hum kya likh rahe hain uska log?
9. Pushed leads kaun dekh sakta hai (sirf uski sales team)?
10. Data kahan host hota hai? Delete aur retention kaise?
11. API ya integration user ka koi extra charge? Change hone par kitne din pehle batata hai?
12. Uski pasand: builder ke reply **aane par hi** lead banaye (hamari salah), ya research ke stage par hi sab?

**Raaste (sab ASSUMPTION, API dekhne ke baad badlenge, estimate me abhi nahi):**

| # | Raasta | Ghante (ek baar) | Hafte ka |
|---|---|---|---|
| P1 | Hafte ka CSV, wo apne CRM me import kare | 0 (C ya A ka CSV) | 0.3 |
| P2 | Hand-off alert + wo haath se enter kare (abhi ki yojana) | 0 | 0 |
| P3 | Uska lead-capture form/endpoint ya email-to-lead (agar ho) | 4 se 8 | 0.2 |
| P4 | API se lead banana, sirf hand-off par | 8 se 16 | 0.2 |
| P5 | Dono taraf ka sync (uske stage hamare dashboard par) | 16 se 30 | 0.5 |

OPINION: pilot me P1 ya P2. P4 tabhi jab pilot ke baad Sridhar chale. P5 pilot se pehle nahi.

Dhyan: uske CRM me builder ka contact daalna personal data uske paas bhejna hai. Safe default: sirf tab jab builder ne **reply** diya (tab woh hamare number par likh chuka hai). Research ke stage par saari contact details uske CRM me mat bhejo. Uska CRM ka admin password ya production login hamare paas nahi aana chahiye: sirf scoped API token, hamare server ki env file me, chat me kabhi nahi.

---

## 7. Jokhim ek jagah

| # | Jokhim | Kya karein |
|---|---|---|
| 1 | Main console ka password Sridhar ko dena | Kabhi nahi |
| 2 | Contact data ya vyakti ke naam export me ghus jayein | Allow-list export, scanner, release se pehle |
| 3 | Option B me filter ki galti | Sirf tab, 3 client ke baad, review ke saath |
| 4 | Shared password, koi alag user nahi | Lamba passphrase, 16+ characters (console 10 par rukta hai), password hidden prompt se, badalna ho to `.env` + restart |
| 5 | Instance ki API key leak | Sirf us instance ka data bhugtega (alag DB) |
| 6 | VPS memory | `free -m` pehle, 300 MB cap |
| 7 | Galat signals se bhram | Opens/reads mat dikhao. Reply gino |
| 8 | Sridhar ko 0 numbers dikhna | Pilot me pehle se likho ki 50 builder se reply rate nahi nikalta (`owner_notes.md`) |
| 9 | Hamara engagement_sync client par chalana | Mat chalao: contacts ke last 4 digit chahiye, aur doosri leads padhta hai |
| 10 | Uske CRM me bina permission data daalna | Pehle sawal 1 se 12, sirf reply par, scoped token |

---

## 8. Sridhar ke liye (English, ek paragraph, jab aap chaho)

```
Each week we can show you a read-only view of this campaign only: builders researched, owner or decision-maker named with a confidence label, messages sent and delivered, replies handed to you, and anything you log as a demo. It shows company names and roles from public sources, with no phone numbers or personal contact details. It can be a weekly file (HTML plus CSV) or a live page with its own login. If you would like the leads inside Nexus360's CRM later, please tell us whether it has an API or a CSV import, and share the documentation.
IV Infotech
```

---

## 9. Aapko kya tay karna hai

1. Option kaun sa (meri salah: pehle D + C, live chahiye to A).
2. Option A ho to: subdomain ka naam aur DNS/vhost ka access kiske paas hai.
3. Kitne log login karenge (Sridhar ke saath Dhiraj)? Ek hi shared password milega.
4. Opens/reads dikhane hain ya sirf sent/delivered/replied (meri salah: sirf yeh teen).
5. Sridhar ko "0 abhi" wala dashboard dikhana theek hai? (meri salah: haan, saaf label ke saath).

## Sources

`console/app.py`, `console/leads_view.py`, `console/templates/base.html`, `console/templates/leads.html`, `console/templates/overview.html`, `console/templates/campaigns.html`, `console/deploy/deploy_console.sh`, `console/deploy/console_cutover.sh`, `agent/tools/console.py`, `agent/engagement/engagement_sync.py`, `agent/docs/AGENT_API_CONTRACT.md`, `agent/docs/CAMPAIGN_PLAYBOOK.md`, `agent/memory.md`, `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, `proposal/unit_costs/unit_costs.md`, `proposal_lowprice/dashboard/dashboard.html`, `proposal_lowprice/owner_notes.md`.
