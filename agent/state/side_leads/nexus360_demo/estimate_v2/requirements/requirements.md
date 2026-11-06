# Nexus360: requirements jo abhi clear nahi hain (sawal list)

Tayyar: Tue 20 Oct 2026. Status: DRAFT. Kuch bhi Sridhar ko bheja nahi gaya.
Kiske liye: Owner (Hinglish). Sirf section A Sridhar ke liye hai (English, sign "IV Infotech").

Labels: FACT = file ya site se dekha hua. INFERENCE = FACT se nikala hua andaza. ASSUMPTION = hamara apna andaza (range ke saath). OPINION = meri salah.
Rupee ka hisaab: hamari mehnat ka cost Rs 500 per ghanta (ASSUMPTION, low-price proposal ke mutabik). Yeh cost hai, margin nahi.

---

## Ek nazar me

- Sawal 14 hain. Pehle 6 MUST hain: inke bina na demo ban sakta hai, na estimate pakka ho sakta hai.
- Sridhar ko ek hi message me 6 sawal bhejna (section A, 117 words). Baaki 8 call par ya doosre chhote message se (A2).
- Agar Sridhar jawab na de, to estimate neeche ke "defaults" par hi chalega (section C). Jo cheez cost badhati hai wo section D me likhi hai, taaki hum jo promise karein wahi de saken.
- Hamare apne kuch pending kaam hain (BSP, +91 number, forward-only). Wo Sridhar se nahi, hum se related hain: section E.

---

## A. Sridhar ko bhejne wala message (English, 117 words)

Isme koi price, promise ya hamare staff ka naam nahi hai. Ek reply me jawab de sake aisa banaya hai.

```
To turn our indicative estimate into a firm one and build your demo, could you answer these six, even roughly?

1. Where first: which districts, and which builders (size or type) should we include or skip?
2. Who should we reach: owner only, or also purchase and accounts heads?
3. How many builders a month, and how many demos a week can you take?
4. Who answers a genuine reply, on which number, in which hours?
5. Can you send 2-3 screenshots or a short screen recording, and your logo?
6. Sender: should the WhatsApp display name be "Nexus360" or "IV Infotech", on a +91 number? WhatsApp only, or also email?

Rough answers are fine.
IV Infotech
```

### A2. Optional doosra message (baaki 8 sawal, English, 120 words)

Sirf tab bhejna jab Sridhar pehle ka jawab de de ya call par time na ho.

```
More for the first-send checklist, one line each is enough:

7. Message language and tone: English, Hindi or both?
8. May we mention a free demo or a price? Which customers may we name, and are "20+ projects, 200+ people" still right?
9. Typical first-year contract value, sales cycle, and what you have already tried?
10. Which CRM do you use, and can it take leads by API or CSV import?
11. Customers and pipeline to exclude (with registered company names), and who owns the researched list at the end?
12. Opt-out wording, and who approves the first messages, within what time?
13. Budget range and start date?
14. What would make you continue after the first month?
IV Infotech
```

Note: "Rough answers are fine" ka matlab hai ki hum uske baad bhi values badal sakte hain. Estimate "indicative" hi rahega, jaisa aapke boss ne kaha.

---

## B. Poori list aapke liye (Hinglish): kyun poochte hain, cost/design par asar

Priority: P1 = MUST (demo + pakka price). P2 = pehle send se pehle chahiye. P3 = jaanna accha hai.
"Asar" me hours hamare hain. Rs = hours x Rs 500. Sab ASSUMPTION jahan source nahi likha.

### P1: MUST (pehle 6, Sridhar ko pehle message me jaate hain)

**Q1. Kahan se shuru (kaunse district) aur kaunse builder (size/type)?**
- Kyun: Chhattisgarh RERA list me 2,173 projects hain. Humari filter ke baad Raipur, Durg, Rajnandgaon me 72 builder bachte hain (FACT: `cg_rera_demo_summary.txt`). "Small/medium" register ka field nahi hai. Hum "3 ya kam registered projects" ko stand-in maante hain (FACT: same file). Test me 6 me se 2 builder bade group nikle (FACT: `enrichment.md`), isliye yeh rule kamzor hai.
- Asar (cost): Aur district jodna ek setting hai, 0.5 se 1 ghanta (Rs 250 se 500). Size ko "filed project cost" aur group size se tay karna behtar hai (register ke detail page par free hai). Isme detail page ek-ek karke kholne padte hain, 72 builder ke liye lagbhag 16 minute (ASSUMPTION, `enrichment.md` se nikala) aur group-resolution ka code (abhi nahi bana): 2 se 4 ghante ek baar (Rs 1,000 se 2,000).
- Asar (design): Pool kitna hai yeh yahi tay karta hai. Teen district me 424 promoter (date limit ke bina), poore Chhattisgarh me 798 (INFERENCE: `unit_costs.md`). 150 per month par teen district ~2.8 mahine chalte hain. Naye qualifying builder sirf ~4 per month aate hain.
- Madhya Pradesh: MP RERA ki robots.txt bots ko mana karti hai, isliye MP automatic nahi hoga (FACT: `nexus360_sridhar_patnaik.md`). Agar wo MP bhi chahta hai: haath se list, 30 se 45 minute per builder (ASSUMPTION) = 50 builder ke liye 25 se 38 ghante (Rs 12,500 se 19,000). Yeh base estimate me nahi hona chahiye.
- Default agar jawab nahi: sirf Raipur, Durg, Rajnandgaon. Size = stand-in rule. MP nahi.

**Q2. Kise reach karna hai: sirf owner, ya purchase / accounts head bhi?**
- Kyun: Sridhar ne kaha RERA ka phone asli owner ka nahi hota (owner, operator aur company alag hote hain). 6 builder ke test me owner/decision-maker 4 ka naam mila, lekin koi bhi pakka (verified) nahi tha. Sirf 1 builder ke paas WhatsApp se juda business number tha. Owner ka seedha WhatsApp number 0 of 6 mila (FACT: `enrichment.md`, owner_notes.md). Chhota sample hai, yeh forecast nahi hai.
- Asar (cost): Doosra persona (purchase/accounts) = naya message variant + research ka alag tareeka: 4 se 6 ghante ek baar (Rs 2,000 se 3,000) aur har builder par 5 se 10 minute extra (50 builder = 4 se 8 ghante, Rs 2,000 se 4,000). Sirf owner = estimate jaisa hi.
- Asar (design): Jahan sirf published enquiry line milti hai, wahan builder research hota hai par WhatsApp par message nahi jaata (phone call chahiye, woh hamare pilot ke bahar hai).
- Default: owner / decision-maker, jitna public evidence se pakka ho.

**Q3. Mahine me kitne builder, aur hafte me kitne demo wo le sakta hai?**
- Kyun: Yeh estimate ka size tay karta hai (pilot 50 builder, monthly 150). Demo capacity se hum bhejne ki speed rokte hain, taaki jab builder jawab de to Sridhar sambhal sake. Sridhar akela hai ya Dhiraj bhi demo leta hai: yeh bhi poochna.
- Asar (cost): WhatsApp ka kharcha bahut chhota hai. Aapke BSP ka Rs 1.5 per marketing message (jo aapne bataya) lein to pilot ke 100 se 150 message sab delivered hon tab bhi Rs 150 se 225 (GST se pehle). Monthly 300 se 450 message = Rs 450 se 675 tak. Asli kharcha hamare ghante hain. Har builder par jaanch ka 4.5 se 9 minute lagta hai (`owner_notes.md`).
- Asar (design): 150 se zyada per month par pool khatam hota hai (Q1) aur check karne ka kaam bottleneck banta hai. Phir zyada district ya repeat touch lagega.
- Default: pilot 50 builder (14 din), monthly 150.

**Q4. Genuine reply kaun sambhalega: kaun sa number, kaun se ghante? "Genuine reply" ka matlab kya?**
- Kyun: Sridhar ne khud kaha ki genuine reply par wo apne haath me lega, kyunki owner bot se baat karna pasand nahi karte. Hum builder ka reply AI ko nahi dikhayenge. Forward-only ka matlab: reply sidha Sridhar ke alert par jaata hai, koi AI jawab nahi deta. Yeh abhi BANA NAHI HAI. Aaj pehla reply hamare AI sales agent ke paas jaata hai (FACT: `agent/memory.md` ki 19 Oct entries) aur wo hamari real-estate wali pitch bol dega, jo galat hoga.
- Asar (cost): Forward-only banane me 4 se 8 ghante lagte hain, base 6 (Rs 2,000 se 4,000; `unit_costs.md`). Doosra number ya team inbox: 2 se 3 ghante aur (Rs 1,000 se 1,500). Alerts: Sridhar ke 24-ghante window ke bahar template alert jaata hai. 10 se 30 alert per month = Rs 15 se 45 (Rs 1.5 per message maan kar, ASSUMPTION).
- Asar (design): Genuine reply ki definition pilot ka pass/fail tay karti hai. Hamara suggestion: owner-level do-tarfa jawab = genuine. Auto-greeting, STOP, aur enquiry-desk ka button tap = genuine nahi (alag gine jayenge). Sridhar se poochna: button tap par call kare ya nahi.
- Default: Sridhar apne number par, business hours me.

**Q5. Assets: 2 se 3 screenshot ya chhoti screen recording, logo.**
- Kyun: Page aur 15 se 20 second ki video Nexus360 ke apne screen se hi bani honi chahiye. Bina uske video "animatic" hi rehti hai (amber placeholder ke saath), bhejne layak nahi (FACT: `page_video_effort.json`).
- Asar (cost): Uska time: 2 screen recording (retake ke saath 30 se 60 min), Hindi voice ke 4 clip (30 se 60 min), logo/permission (20 min), claim lines padhna (20 min) = 1.5 se 2.5 ghante (ASSUMPTION). Voice na de to captions-only ya English AI voice: ElevenLabs commercial plan $6 per month (Rs 540) aur "AI voice" ka disclosure (FACT: `unit_costs.md`).
- Asar (design): Real screenshot milne par hi demo me "Nexus360 ka sach me screen" dikhega.
- Default: sirf nexus360.in ka public text. Rendered video nahi, sirf storyboard.

**Q6. Sender: display name "Nexus360" ya "IV Infotech"? +91 number? Sirf WhatsApp ya email bhi?**
- Kyun: Hamari WhatsApp API line aaj +1 (US jaisa) number hai aur naam "IV Infotech" (FACT: `agent/memory.md`). Indian builder ko +1 sender galat lagega (FACT: `CAMPAIGN1_DIAGNOSIS_2026-10-20.md`). Sridhar ne email ka zikr nahi kiya. WhatsApp account hamara hi rahega (call me tay hua), isliye Meta ka quality-rating risk bhi hamara hai.
- Asar (cost): +91 number aur display name: BSP me milega ya nahi, kitna lagega: ABHI PATA NAHI (section E). Hamara andaza Rs 0 / 1,000 / 3,000 ek baar plus BSP ka alag fee (ASSUMPTION, `unit_costs.md`). "Nexus360" naam hamare WABA par use karne ke liye Meta ko wajah chahiye aur Sridhar ki likhit ijazat; Meta mana bhi kar sakta hai (INFERENCE, hum ne test nahi kiya). Fallback: "IV Infotech (for Nexus360)". Email jodna: 4 se 6 ghante ek baar (Rs 2,000 se 3,000) aur sending domain ki jaanch (14 Oct ko hamare Resend domain ka SPF/DKIM status verified nahi likha tha: `agent/memory.md`, abhi dobara check karna hoga).
- Asar (design): Sirf WhatsApp ka delivery record kamzor hai. Hamari apni campaign me 7 cold template me se 2 hi time par pahunche (FACT: `CAMPAIGN1_DIAGNOSIS_2026-10-20.md`). Email se kuch builder tak doosra raasta khulta hai, par Gujarat me 159 fresh promoter me sirf 7 ka business email tha (FACT: `CAMPAIGN_LEARNINGS.md`).
- Default: WhatsApp hi, max 2 touch, STOP maanenge. Display name: Meta jo allow kare.

### P2: pehle send se pehle chahiye

**Q7. Language aur tone: English, Hindi ya dono? Formal ya friendly?**
- Kyun: Hamare Hindi lines ka koi native check nahi hua (FACT: `owner_notes.md`). Chhattisgarhi test nahi hui.
- Asar: Hindi version + native check 1.5 se 2.5 ghante (Rs 750 se 1,250), aur 15 minute kisi Hindi-native ka review (ASSUMPTION). Voice: Sridhar ki apni Hindi voice (30 se 60 min) ya sirf captions.
- Default: pehla message English. Hindi line check ke baad.

**Q8. Kya bol sakte hain: free demo, price, customer ke naam, "20+ projects, 200+ people"?**
- Kyun: Nexus360 ka price public nahi hai (site par "Ask for pricing", dekha 20 Oct). Hum wo price kabhi nahi likhenge jo Sridhar ne publish nahi kiya. Mahavir Group jaise naam site par hain, par outreach me unka naam sirf Sridhar aur us customer ki ijazat se. "20+ projects, 200+ people" nexus360.in ka claim hai, uski confirmation chahiye.
- Asar: copy aur page ka kaam; extra cost nahi. Par jab tak claims confirm nahi, wo page par nahi jayenge.
- Hum ye KABHI nahi bolenge: savings/ROI, "instant", "guaranteed", doosre states automated hain, kisi builder ke results.
- Default: koi price nahi, koi customer naam nahi, claims sirf site se aur "per nexus360.in" jaisa.

**Q9. Sales motion: pehle saal ka typical contract value, sales cycle, kya try kiya, customers kaise aaye?**
- Kyun: Yeh batata hai ki kaunsa option sach me kaam karega. Rule: ek qualified conversation ka cost <= (hamare conversion ka share x contract value x usne kitna kharch karna hai) (`comparison.md` section 7.5). Example (ASSUMPTION): 20% conversion aur 30% kharch rakhein to cost per qualified conversation contract value ka 6% hona chahiye. Contract value Rs 3.3 lakh ho to Rs 20,000 chalega. Value Rs 1.5 lakh ho to sirf Rs 9,000. Hamare paas yeh number nahi hai.
- Asar: koi cost nahi. Par pilot ke "pass/fail" aur shared-risk (per demo fee) ki definition isi se banegi. Hum "kya try kiya" jaanna chahte hain taaki wahi cheez dobara na dein (cold call, ads, partner, referral).
- Default: kuch pata nahi, isliye pilot ko "jaankari kharidna" maante hain, customer ka vaada nahi.

**Q10. CRM aur reporting: kaunsa CRM? API / sandbox / CSV import? Hafte me kya dekhna hai?**
- Kyun: Sridhar ne CRM maanga nahi, par shayad diya jaaye. Nexus360 ka apna CRM hai (lead capture, follow-up, site visit, pipeline: nexus360.in). Agar campaign ke leads uske CRM me aa sakein to wo ek jagah dekhega. Humein uski API ka kuch pata nahi (UNKNOWN). Kya poochna hai: `crm_access.md` section 6.
- Asar (cost): API push 8 se 16 ghante (Rs 4,000 se 8,000, ASSUMPTION, API docs dekhne se pehle andaza). CSV import 0 integration. Hamara dashboard: `crm_access.md` ke options (A: live view, C: static file + CSV).
- Default: har hafte ek summary file + CSV, live console nahi. CRM me push nahi (jab tak API docs na mil jayein).

**Q11. Exclusions aur data: uske customers aur pipeline jo skip karne hain, aur end me researched list kiski?**
- Kyun: Uske customers register me alag company naam se hain. Jaise Evergreen City ka promoter naam brand se alag hai, Mangalam City ka bhi (FACT: `2_nexus360_customers_in_cg_rera.csv`). Sirf brand ke naam se match karne par miss ho jayega, isliye registered company naam chahiye. "Suncity" naam ke projects ek se zyada promoter ke hain: register se hum nahi bata sakte kaunsa uska customer hai.
- Asar: cost nahi. Jo bhi match miss hua wo galat builder ko "prospect" dikhayega (sharmindagi). Hum customer detail screen par nahi dikhate, sirf exclusion ke liye use karte hain.
- Data: hamara default: end me CSV (research record + send/reply log), jo business ne khud publish kiya wahi, source link ke saath. Retention aur delete ki date likhit me Day 0 se pehle (proposal ka `data_exit_text`). Koi bhi mahine ke end me rok sakta hai.
- Default: exclusion list uska diya hua. Export CSV. Dono taraf se mahine ke end me exit.

**Q12. Compliance aur approvals: opt-out line, stop words, DPDP, pehle messages kaun approve karega?**
- Kyun: Har message me opt-out line aur sender ki pehchaan zaroori hai. Stop words: STOP, band karo, nahi chahiye (English aur Hindi). DPDP: Act ke bade duty ~May 2027 se (secondary sources, counsel se confirm: FACT `enrichment.md`). Asli nazdeeki risk WhatsApp ki apni opt-in policy hai (cold template ko Meta rok sakta hai: 2 of 7 delivered).
- Asar (cost): extra cost nahi. Approval delay hi dikkat hai. Agar Sridhar har message dekhna chahe to pilot ke 100 se 150 message ke liye bohot time lagega. Hamara suggestion (OPINION): template + pehle 5 builder record uska approval, phir har 5 me 1 spot-check.
- Default: opt-out line har message me. Template + pehle 5 records par uska likhit OK.

**Q13. Budget range aur start date.**
- Kyun: Yeh tay karta hai kaunsa option (research-only, pilot, monthly, shared-risk) dena hai. Start date par Diwali (8 Nov) ka asar: hamara apna rule hai ki ~5 Nov ke baad touch band. Diwali ke hafte me builder ka dhyan kam hota hai (INFERENCE).
- Asar: cost nahi, sirf tier. Realistic start: jawab 23 Oct tak aaye to demo ~27 se 29 Oct tak. Pehla asli send +91 number, template approval aur forward-only ke baad. Isliye Diwali ke baad (~16 Nov) maanna theek rahega (OPINION). Meta approval kitna time lega pata nahi.
- Default: jawab nahi to start 16 Nov ke baad.

### P3: jaanna accha hai

**Q14. 30 din me kya dekhna chahta hai, kab rukna chahta hai?**
- Kyun: Pilot ke gates pehle se likhne ke liye (owner coverage 40%, WhatsApp-capable 30%, delivery 60%, 1 genuine reply: `prices.json` ke `pilot_gates`). Sridhar ki apni definition alag ho sakti hai. Report kise jaayegi (Sridhar, Dhiraj).
- Asar: cost nahi. Design: report ka format.
- Default: wohi gates jo proposal me hain.

---

## C. Defaults: agar jawab na mile, estimate in par tikega

| # | Cheez | Default | Sawal |
|---|---|---|---|
| 1 | Jagah | Raipur, Durg (Bhilai), Rajnandgaon. MP nahi | Q1 |
| 2 | Size | 3 ya kam registered projects (stand-in), housing, government nahi | Q1 |
| 3 | Kise | Owner / decision-maker jahan public evidence kaafi ho | Q2 |
| 4 | Volume | Pilot 50 builder, 14 din. Monthly 150 | Q3 |
| 5 | Hand-off | Sridhar apne number par, business hours. Forward-only (AI jawab nahi deta) | Q4 |
| 6 | Assets | Sirf public nexus360.in. Video sirf storyboard | Q5 |
| 7 | Channel | WhatsApp hi, max 2 touch, STOP maanenge | Q6 |
| 8 | Bhasha | English pehle. Hindi native check ke baad | Q7 |
| 9 | Claims | Koi price nahi, koi customer naam nahi, koi savings claim nahi | Q8 |
| 10 | Report | Hafte me summary file + CSV | Q10 |
| 11 | Data | CSV export, dashboard par masked | Q11 |
| 12 | Approval | Template + pehle 5 records par uska OK | Q12 |

---

## D. Kya cost badhata hai (estimate me alag likhna hai, base me nahi)

Rs = hours x Rs 500 (cost). Kisi bhi jagah margin nahi jodi. Hours ASSUMPTION jahan source nahi.

| Agar Sridhar kahe | Extra mehnat (ghante) | Rs 500/ghanta par | Source |
|---|---|---|---|
| Aur district (Bilaspur wagairah) | 0.5 se 1 ek baar | Rs 250 se 500 | script ka `--districts` option |
| Size filed project cost se + group resolution | 2 se 4 ek baar | Rs 1,000 se 2,000 | `enrichment.md` section 4 |
| Purchase / accounts persona jodna | 4 se 6 ek baar + 5 se 10 min per builder | Rs 2,000 se 3,000 + Rs 2,000 se 4,000 per 50 builder | ASSUMPTION |
| Email doosre channel ke roop me | 4 se 6 ek baar | Rs 2,000 se 3,000 | ASSUMPTION |
| MP ki list haath se, per 50 builder | 25 se 38 | Rs 12,500 se 19,000 | `unit_costs.md` |
| Hindi version + native check | 1.5 se 2.5 | Rs 750 se 1,250 | ASSUMPTION |
| Doosra hand-off number / team inbox | 2 se 3 | Rs 1,000 se 1,500 | ASSUMPTION |
| Forward-only (sab ke liye zaroori) | 4 / 6 / 8 | Rs 2,000 / 3,000 / 4,000 | `unit_costs.md` |
| CRM API push (API ka pata nahi) | 8 se 16 | Rs 4,000 se 8,000 | ASSUMPTION, docs dekh kar badlega |
| Live client dashboard (alag console instance) | 11 / 16 / 25.5 | Rs 5,500 / 8,000 / 12,750 | `crm_access.md` |
| Static dashboard file + CSV | 10 / 15 / 24 | Rs 5,000 / 7,500 / 12,000 | `crm_access.md` |
| Top 10 builder ke liye alag video | ~1 se 2 per 50 builder | Rs 500 se 1,000 | `page_video_effort.json` |
| 150 se zyada builder per month | har builder 4.5 se 9 min | Rs 40 se 75 per builder | `owner_notes.md` |

Ek zaroori note (estimate workstream ke liye): `unit_costs.md` ne "read-only client dashboard" ke liye 6 / 8 / 12 ghante rakhe the. Woh sirf dikhne wale hisse ka hai. Data ko safe tareeke se nikalne aur har send/reply ko record karne ka kaam usme nahi tha: +6 / 9 / 14 ghante. Detail `crm_access.md` section 4 me.

---

## E. Hamari apni cheezein jo pehle pakki karni hain (Sridhar se nahi poochna)

1. BSP (Fortius): Rs 1.5 per marketing message sirf DELIVERED message ka hai ya submit ka? (Meta ab delivered par charge karta hai, 1 Jul 2025 se: FACT `unit_costs.md`. BSP ka apna billing likhit me confirm karna.) GST upar se lagega ya andar hai? Plan ka monthly fee? INR billing 31 Dec 2026 se pehle?
2. +91 number: kya ek WABA me doosra phone number add ho sakta hai? Kitna lagega? Display name approve hone me kitne din? Number ke hisaab se webhook alag set ho sakta hai ya nahi (forward-only isi par tikta hai).
3. Forward-only: kaise banega: (a) alag number + alag webhook, ya (b) hamare CRM webhook me rule ki "is number par aaya to AI nahi, sidha Sridhar ko alert". 4 se 8 ghante (`unit_costs.md`). Jab tak yeh bana nahi, koi asli builder ko message nahi jayega.
4. Meta quality rating aur business verification ki aaj ki sthiti (unknown). Naya portfolio 24 ghante me 250 unique recipient tak limited (FACT, hamari 14 Oct research).
5. Claude ka kharcha: client kaam hamare Claude subscription par nirbhar nahi hona chahiye. Isliye API-equivalent cost use karo: Rs 24 / 76 / 279 per builder (low/base/high, `unit_costs.md`). Subscription USD 100 hai aur badh bhi sakta hai: estimate API rate par hi tikna chahiye.
6. Sridhar ka title (founder, CTO, solo developer) confirm nahi. Site par koi naam nahi. Message me uska title mat likho jab tak wo confirm na kare.

---

## F. Abhi kya NAHI karna

- 10-page proposal abhi mat bhejo. Pehle ek chhota indicative estimate.
- Sridhar ko hamare +1 business number par message karne ko mat kaho. Wahan hamara AI sales agent jawab dega (real-estate WhatsApp automation ki pitch).
- Koi message kisi asli builder ko nahi jayega. Koi sample Sridhar ke phone par bhi nahi jayega jab tak uska likhit OK na ho (`demo_spec.md` section 4).
- Builder ke owner ka naam, phone ya email kisi bhi file me nahi.
- Kuch bhi "instant", "guaranteed" ya reply/demo/customer ka vaada nahi.

---

## Sources

- `proposal/owner_notes.md`, `proposal_lowprice/owner_notes.md`, `proposal_lowprice/prices.json`
- `proposal/enrichment/enrichment.md` (6-builder test)
- `proposal/unit_costs/unit_costs.md`, `proposal/employee/comparison.md`
- `proposal_lowprice/page_video/page_video_effort.json`
- `cg_rera_demo_summary.txt`, `cg_rera_demo.py`, `2_nexus360_customers_in_cg_rera.csv` (company-level matches only)
- `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, `agent/memory.md`, `agent/state/side_leads/nexus360_sridhar_patnaik.md`
- nexus360.in (read 20 Oct 2026, by the earlier workstreams)
