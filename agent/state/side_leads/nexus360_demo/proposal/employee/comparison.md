# Sales employee vs our system vs hybrid

Nexus360 side lead, Chhattisgarh builders. Written Tue 20 Oct 2026. Working file for the owner; sections tagged [LIFTABLE] are written so they can go into Sridhar's proposal, sections tagged [INTERNAL] must not.

## 0. Labels, units, and what this file does not decide

- FACT = taken from a listed source (id in brackets, section 10) or from our own files. INFERENCE = calculated from facts. OPINION = judgement. ASSUMPTION = no source; a range is shown and the pilot should replace it.
- Money is in Indian rupees (Rs), before GST unless stated. Employee figures are per month. USD to Rs is ASSUMPTION 95 (range 90 to 97; the only rate found was about 96.5, undated [S21]).
- **QC (qualified conversation)** = the real owner, or a decision-maker, of a builder has a two-way exchange about Nexus360 (call or written) and does not say no. Every comparison below uses this one unit.
- **The system's fee is not set here.** The estimate workstream sets it. This file uses a placeholder S and shows results for Rs 20,000, 35,000 and 50,000 a month.
- The arithmetic is in `calc_comparison.py` (same folder); the numbers are in `comparison_numbers.json`.
- Limits of the evidence: AmbitionBox, Naukri and Glassdoor pages could not be fetched (HTTP 403 or not returned), so their figures appear only through secondary pages. No India-specific B2B SDR benchmark and no India ERP sales-cycle figure was found. Statutory bonus, gratuity and paid leave are not modelled (they add roughly 2 to 5% for low-paid staff).

---

## 1. Bottom line [INTERNAL]

1. **What an employee costs (INFERENCE from S1 to S9).** One mid-level business-development executive in Raipur, Bhilai or Rajnandgaon costs about **Rs 36,900 a month all-in** (Rs 25,000 fixed pay plus about Rs 11,900 of on-top costs), about Rs 4.4 lakh a year. The band is Rs 20,000 (junior caller) to Rs 67,000 (experienced). A metro-hired equivalent is about Rs 60,000.
2. **The Chhattisgarh list is small.** The public register gives 72 small and medium promoters after our filters, about 115 unique recent promoters before the type and size filters, and about 470 promoters with three or fewer valid registrations if we look back further (FACT, own count). New qualifying builders arrive at only about 4 a month. One person can call all 72 three times in about a week. **So capacity is not the deciding factor. Who can reach the real owner, and whether the owner replies, is.** (INFERENCE)
3. **The system has no proven reply rate.** 0 replies from 9 contacts (true rate could still be up to 28%, one-sided 95%) and only 2 of 7 WhatsApp messages on time (95% interval 3.7% to 71%) [S19]. We cannot show today that the system beats an employee on cost per qualified conversation.
4. **Break-even (arithmetic, section 7).** The system beats an employee on cost per QC when `QC_system >= QC_employee x S / Rs 36,929`. At S = Rs 35,000 the system must produce about as many QCs as the employee (0.95x). At Rs 20,000, about half (0.54x). At Rs 50,000, 1.35x.
5. **On an illustrative funnel (all ASSUMPTION, section 7.3), the system gets about 0.28 of an employee's QCs.** That puts the cost-per-QC break-even fee near Rs 10,000 a month. On today's evidence the system does not win on cost per QC. It does win on **speed to start** (days, not 4 to 8 weeks plus a 3-month ramp), **research coverage and documentation**, and **cost flexibility** (the fee can fall after the first sweep; a salary cannot).
6. **Neither option replaces the closer.** In every option Sridhar (or one executive) talks to the owner. The system never converses with an owner, by his own requirement.
7. **OPINION: decide by a measured pilot, not by argument.** Fix the success measures before the first message (section 8), cap the downside at about three months of one hire (about Rs 1.1 lakh), and hire an executive only if owners actually reply.
8. **Fourth option not modelled:** a commission-only or part-time caller. Worth Sridhar's thought; we have no data on it.

---

## 2. The three-way table [LIFTABLE; row 15 is illustrative, see 7.3]

Definitions. **(1) Employee** = one full-time mid-level BDE hired by Sridhar. **(2) System** = our research, enrichment, personalised WhatsApp (page + video), follow-up, dashboard and hand-off, with Sridhar taking every genuine reply. **(3) Hybrid** = H1: the system finds and warms, Sridhar closes (no hire); H2: the system plus one executive who phones warmed leads and closes with Sridhar.

| # | Dimension | (1) One full-time employee | (2) Our system | (3) Hybrid |
|---|---|---|---|---|
| 1 | **Monthly cost** | **Rs 36,900 all-in** (band Rs 20,000 to 67,000; metro about Rs 60,000). Fixed pay Rs 25,000 + PF Rs 1,600 + incentive Rs 5,000 + phone, CRM, equipment Rs 2,700 + hiring and ramp spread over 24 months Rs 2,600 [3.3] | **Fee S** (placeholder Rs 20,000 / 35,000 / 50,000; set by the estimate) plus Meta message fees: about Rs 0.86 per delivered marketing message before BSP markup and GST, under Rs 400 for 100 builders x 3 touches [S16, S17] | H1: S. H2: S + Rs 36,900 |
| 2 | **Cost per 100 builders researched** | **Rs 15,700 to 31,500** (central Rs 21,000): 0.75 to 1.5 h per dossier at Rs 209 an hour all-in | Not priced separately. Fee divided over the first-month sweep of 150 builders: **Rs 13,000 / 23,000 / 33,000** at S = 20k / 35k / 50k, and that fee also covers messaging, follow-up and dashboard | Same as (2) |
| 3 | **Time to start** | 4 to 8 weeks to hire (ASSUMPTION) + 3.0 months to ramp (US average [S10]). First full-speed month is about month 4 to 5 | Researched list within days of Sridhar approving the segment; first messages about 1 to 2 weeks after his inputs and the Meta set-up (ASSUMPTION; a template approval took 16 to 20 min in our records; a dedicated number's business verification is untimed) | H1: as (2). H2: as (1) for the executive |
| 4 | **Builders researched per week** | 13 to 27 alongside calling; 27 to 53 if researching full time (ASSUMPTION) | 60 to 140, limited by human checking at 5 to 12 min each (about 12 staff hours a week), not by compute. Gujarat round 2: 34 candidates in 63 min with 26 agents [S19] | As (2) |
| 5 | **Builders contacted per week** | About 200 to 350 dial attempts, which is 70 to 120 builders at three tries each (Bridge Group phone teams 56 dials a day [S10]; Tier-2 vendor figure 68 to 80 [S12], weak) | 50 to 125 at the paced 10 to 25 a day we would use to protect the number (OPINION). Meta limits a new portfolio to 250 new recipients per 24 h until business verification [own blueprint] | As (1) + (2) |
| 6 | **Quality of research** | Can confirm by phone and local knowledge who really owns a firm: exactly the RERA gap Sridhar described. Slower, uneven, usually not written down | Written dossier with evidence for every claim. Our own record: 34 candidates gave 12 qualified; the first-pass grades were cut by a skeptic for 6 of 8; a fact-check found 32 problems in 4 drafts; an owner/decision-maker was named for 6 of 9 contacted leads (named is not the same as a reachable number) [S19]. **Needs a human check pass** | System dossier + human phone confirmation: the best of both, at the cost of both |
| 7 | **Relationship building** | Strong: voice, repeat calls, site visits, local network, trust over months | None. It can open a door; it does not build a relationship | H1: Sridhar builds it. H2: the executive and Sridhar |
| 8 | **Handling objections and calls** | Yes | **No, by design.** Owners do not want to talk to a bot, so every genuine reply goes to Sridhar at once. No voice calls | Sridhar or the executive |
| 9 | **Language and Hindi** | Native spoken Hindi and local dialect; in person | Hindi (Devanagari), Hinglish and English text: yes (drafts exist). Spoken Hindi: no. Chhattisgarhi: not tested. Voice-over for the video needs a decided voice | Executive covers spoken |
| 10 | **Consistency and logging** | Depends on discipline; logs often incomplete unless the CRM is enforced | Every send, delivery, reply logged on the dashboard. Read and page-open signals are noisy (6 of 8 early signals in our campaign were false: scanners, auto-opens, our own tests), so we count **replies**, not opens [S19] | Both |
| 11 | **Risk** | Hire does not work out; attrition (US SDR median 40% a year [S10]); promotional voice calls fall under TRAI rules, B2B treatment not verified [S20]; personal-data duties under the DPDP Act from about 2027 [own blueprint] | Meta limits and quality rating on cold numbers (our own: 3 of 7 failed, 2 on time); account is **ours**, so a restriction hits our number; reputational risk to Sridhar's brand if messages feel like spam; same DPDP duties. Mitigation: a dedicated number, opt-out in every message, a stop rule | Both sets |
| 12 | **When the person leaves** | Contacts and relationships walk out unless logged; 4 to 8 weeks vacancy (ASSUMPTION) + 3 months re-ramp; replacement about Rs 25,000 + Rs 37,500 of ramp | The research, templates and logs stay in the dashboard. The dependency moves to IV Infotech continuing to run it (data export terms to be agreed) | Mixed |
| 13 | **Scalability** | Linear: each extra builder-owner needs more hours; a second person doubles the cost | Near-linear and cheap per extra builder compared with a person's hour; bounded by the pool, Meta limits and checking time. **Madhya Pradesh is not automated** (its RERA site disallows bots); an MP list would be human-built | Mixed |
| 14 | **Cost behaviour** | Fixed whether the list is full or empty | Can be stepped down after the first sweep (new qualifying builders about 4 a month) | H1 flexible; H2 fixed for the hire |
| 15 | **Qualified conversations per month (pool 150, ILLUSTRATIVE: pessimistic / central / optimistic)** | 0.2 / 0.8 / 2.9 | **0 / 0.23 / 1.1** | H2: 0.2 / 1.0 / 3.7. H1 = system numbers |
| 16 | **Sridhar's own time** | 4 to 6 h a week managing (ASSUMPTION) | 2 to 4 h a week reading the report and answering hand-offs, plus 30 to 60 min per genuine reply (ASSUMPTION) | H1: as (2). H2: both |
| 17 | **What it CANNOT do** | Research 100+ builders a week with a written dossier each; work nights or festival bursts; log everything by itself; be replaced overnight; guarantee a single reply | Talk to an owner; phone; visit a site; negotiate or close; verify a number by asking a neighbour; guarantee delivery or a reply; reach Madhya Pradesh automatically; fix a weak offer | Does not fix a weak offer; adds coordination; two cost lines |

---

## 3. What a sales employee costs [LIFTABLE]

### 3.1 Pay bands found (annual figure converted to a month by dividing by 12)

| Profile / place | Annual | Monthly | Source, date, strength |
|---|---|---|---|
| BDE, Raipur: Indeed "common" | Rs 2,79,641 (typical range Rs 1,79,734 to 4,35,082) | **Rs 23,300** (Rs 15,000 to 36,300) | S1, page updated 19 Oct 2026; method not stated; moderate |
| BDE, Raipur: PayScale | Rs 1,75,600 | Rs 14,600 | S2; page says last updated Jan 2021, 2 responses; **weak, outlier** |
| BDE, Raipur: job postings seen | | Rs 15,000 to 30,000 (one at Rs 10,000 remote) | S3, Indeed, Apna and employer pages; posting dates not verified; moderate |
| Telecaller / caller, Raipur | Indeed: Rs 1.87 to 2.25 lakh common | Rs 15,600 to 18,700; postings Rs 10,000 to 20,000 | S4; moderate |
| Inside-sales account executive, India (PayScale) | Rs 4,75,000 (25th to 75th: Rs 2.77 to 9.66 lakh); entry level Rs 2.93 lakh | Rs 39,600 (Rs 23,100 to 80,500); entry Rs 24,400 | S5, 6 profiles, updated May 2024; **weak** |
| BDE, Bengaluru: modelled median | Rs 4.9 lakh (Rs 3.2 to 8.1 lakh) | **Rs 40,800** (Rs 26,700 to 67,500) | S6, a model, not a survey, updated 7 Jul 2026; weak to moderate |
| BDE, Mumbai: modelled median | Rs 4.7 lakh (Rs 3.1 to 7.8 lakh) | Rs 39,200 (Rs 25,800 to 65,000) | S6; same caveat |
| BDE, Bengaluru / Mumbai: Glassdoor via a secondary page | Rs 6.88 lakh / Rs 4.77 lakh | Rs 57,300 / Rs 39,700 | S7; undated; secondary; weak |
| BDE, Bengaluru: Talentup | Rs 7.6 lakh base (1,029 observations, Aug 2025) | Rs 63,400 | S6b; moderate |
| BDE, Bangalore entry level: PayScale | Rs 3.52 lakh (56 profiles, updated Apr 2022) | Rs 29,400 | S5b; old |

INFERENCE: for a person who can hold a conversation with a builder-owner in the Chhattisgarh belt, the realistic fixed pay is **Rs 20,000 to 30,000 (central Rs 25,000)**; a telecaller at Rs 10,000 to 20,000 can dial but is unlikely to hold an owner-level conversation; an experienced ERP or real-estate sales person is **Rs 35,000 to 50,000** (above the postings we saw; ASSUMPTION). A metro hire costs roughly 1.6 times the Chhattisgarh central case. Sridhar knows his local market and should replace these with his own figures.

### 3.2 On-top costs

| Item | Treatment | Basis |
|---|---|---|
| Employer PF + EDLI + admin | About 13% of PF wages; PF wage ceiling is **Rs 25,000 since 17 Sep 2026** (was Rs 15,000) | FACT [S8]. ASSUMPTION: basic pay = 50% of fixed pay. Central: Rs 1,625 a month |
| Employer ESI | 3.25% of gross, only if gross is Rs 21,000 or less (Rs 488 for the junior profile) | FACT [S8] |
| Phone and data | Rs 600 to 1,000 a month | ASSUMPTION |
| CRM seat | Rs 0 (Sridhar's own Nexus360 CRM) to Rs 800 to 1,400 (Zoho CRM Standard / Professional, annual billing, ex-GST) | FACT for Zoho, from third-party price pages [S11]; central Rs 800 |
| Incentive | Rs 2,000 (junior) to Rs 10,000 (experienced) average a month; central Rs 5,000 | ASSUMPTION. PayScale shows a Raipur bonus up to Rs 43,000 a year [S2]; Bangalore entry bonus Rs 5,000 to 3,01,000 [S5b] |
| Laptop and desk | Rs 1,000 to 1,250 a month (Rs 35,000 to 45,000 over 36 months), or Rs 0 if he has one | ASSUMPTION |
| Recruitment | 0.5 to 1.5 months of fixed pay once (agency 8.33% of annual pay = one month, up to 12.5% to 16.67%), spread over 24 months | FACT for the fee convention (vendor blogs) [S9]; tenure 24 months is ASSUMPTION |
| Ramp-up | 3.0 months to full productivity (US average); counted as 1.5 months of pay for output not delivered, spread over 24 months | FACT for 3.0 months [S10]; the half-output rule is ASSUMPTION |
| Management time | 4 to 6 h a week of Sridhar's time | ASSUMPTION; shown in hours, not rupees |
| Attrition | US SDR median 40% a year (IQR 21% to 57%) [S10]; India all-sector 16.2% in 2025, e-commerce 28.7%, financial services 24.8% [S13]. No India sales-only figure found | Tenure of 24 months is conservative; 36 months lowers the central all-in by about Rs 900 |

### 3.3 All-in monthly cost by profile (from `calc_comparison.py`)

| Profile | Fixed pay | Cash cost a month (pay + PF/ESI + incentive + tools + equipment) | **All-in** (adds hiring and ramp, 24-month spread) |
|---|---|---|---|
| Chhattisgarh junior caller | Rs 15,000 | Rs 19,062 | **Rs 20,000** |
| **Chhattisgarh mid BDE (central)** | **Rs 25,000** | **Rs 34,325** | **Rs 36,929** (Rs 4.43 lakh a year) |
| Chhattisgarh experienced BDE | Rs 40,000 | Rs 54,250 | **Rs 59,250** |
| Chhattisgarh high corner | Rs 45,000 | Rs 61,575 | **Rs 67,200** |
| Metro mid-level BDE | Rs 40,833 | Rs 55,137 | **Rs 60,241** |

---

## 4. What is known about productivity [LIFTABLE]

| Metric | Number | Source | Strength |
|---|---|---|---|
| SDR daily activity | Median 112 activities (44 phone, 41 email, 19 LinkedIn, 8 text/other); phone-heavy teams 56 dials and 4.6 quality conversations a day; all teams 4.1 quality conversations a day | Bridge Group 2025, 351 B2B companies, 78% North America [S10] | Survey; moderate; mostly US, higher-priced products |
| Ramp, tenure, attrition | 3.0 months ramp; 1.9 years tenure; 40% median annual attrition (13% involuntary, 11% voluntary, 16% promotions) | S10 | Moderate |
| Cold-call funnel | 9.9% of dials connect; 24.5% of prospects reached in about 3 tries; 4.6% of conversations become a meeting; about 370 dials per meeting | Belkins, 175,000 dials in 2025, published 26 Jun 2026 [S14] | Vendor's own data, US-heavy; moderate to weak |
| Other cold-call figures | Gong: average connect 5.4% (top quarter 13.3%), meeting set rate 4.6%. Cognism: 2.3% success in 2025 vs 4.82% in 2024 | Secondary write-ups [S14b] | Weak |
| India telecalling | 68 to 70 calls per agent per day in Tier-2 vs 90 to 92 in metros; handle time 5.2 vs 4.3 min | Callyzer, a call-tracking vendor [S12] | Weak. The same vendor elsewhere claims 46 to 48% connect; another vendor 15 to 25%; definitions differ, so **not used** |
| Cold B2B WhatsApp reply rate, India | Claims range from 15 to 20% (vendor) to 1 to 2% (a blog citing an unverified analysis); 2 to 8% for generic broadcasts | Vendor blogs [S15] | **Very weak.** No independent study found |
| Our own campaign | 0 replies from 9 contacts; one-sided 95% upper bound 28%. WhatsApp: 2 of 7 on time (95% interval 3.7% to 71%), 3 failed, only 1 to 4 of 9 reached on a plausible human route | Campaign 1 diagnosis [S19] | FACT, but the sample is tiny |
| ERP demo-to-close rate and sales cycle in India | **Not found** | | Gap |

---

## 5. What the system costs Sridhar [LIFTABLE]

- **The fee S** is set in the estimate. It should be described as covering: research and enrichment of each builder, the personalised page and video for those who qualify, the WhatsApp sends and follow-ups, the dashboard, and hand-off of genuine replies.
- **Pass-through:** Meta charges per delivered message, India marketing template about Rs 0.8631 from 1 Jan 2026 [S16, S17]. Replies inside the 24-hour window are free up to 1,000 per number per month; beyond that, and for utility templates sent inside an open window, charges began on 1 Oct 2026 [S16]. A BSP markup of about 10 to 25% is reported by one source [S17]; our own BSP's plan fee is not in our files. For 100 builders x 3 touches, all delivered: 300 x Rs 0.8631 = Rs 259 before markup and GST (about Rs 350 with 15% markup and 18% GST).
- **Not included:** Sridhar's time; his CRM licence (he already owns Nexus360); any extra number or business verification fee we cannot yet confirm.

---

## 6. The pool decides what is possible [LIFTABLE]

From the public Chhattisgarh RERA list fetched 20 Oct 2026 [S18] and our own count of that file (rough name matching):

| Group | Count | Note |
|---|---|---|
| Registered projects, all state | 2,173 | script funnel |
| In Raipur, Durg, Rajnandgaon | 1,317 (1,127 still valid) | |
| Promoters with a valid registration in those districts | about 543 (349 with 1 project, 99 with 2, 22 with 3, 73 with 4+) | own count; name spelling variants not merged |
| **Promoters with 3 or fewer valid projects** | **about 470** | the widest sensible pool |
| Unique promoters approved in the last 18 months (valid) | about 115 | before type, government and size filters |
| **Small/medium promoters after the script's rules** | **72** | the demo list |
| New valid approvals a month | about 8.4 projects; about **4 qualifying builders a month** | own count; the script's filters keep 72 of 146 |

INFERENCE: one person phoning 72 builders three times is about 216 dials, or 4 to 5 working days at 40 to 60 dials. The system can research the 72 in a day or two of compute plus about 10 hours of checking. **Volume is not the constraint for either option. After the first sweep, the list refills at about 4 builders a month**, which is a reason to price the system as a pilot plus a lower run fee, and a reason not to expect an employee to be busy on this list alone. An employee would also do other Nexus360 work (demos, follow-up, existing leads); only the part spent on this outbound job should be compared.

---

## 7. Break-even [LIFTABLE; 7.3 only after the owner agrees to show an illustrative funnel]

### 7.1 Formula

Cost per QC = monthly cost / QC per month. The system beats the employee on cost per QC when

`QC_system >= QC_employee x (S / C_E)`, with C_E = Rs 36,929 (central all-in).

Equivalently, the most the system is worth on this test is `S* = rho x C_E`, where rho = QC_system / QC_employee.

| rho (system QCs as a share of employee QCs) | 0.25 | 0.5 | 0.75 | 1.0 | 1.5 |
|---|---|---|---|---|---|
| Break-even fee S* a month | Rs 9,200 | Rs 18,500 | Rs 27,700 | **Rs 36,900** | Rs 55,400 |

### 7.2 Required system QCs a month for different fees and employee outputs

| Employee QC a month | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|
| Employee cost per QC | Rs 73,900 | Rs 36,900 | Rs 18,500 | Rs 9,200 |
| System must produce, S = Rs 20,000 (0.54x) | 0.27 | 0.54 | 1.08 | 2.17 |
| System must produce, S = Rs 35,000 (0.95x) | 0.47 | 0.95 | 1.90 | 3.79 |
| System must produce, S = Rs 50,000 (1.35x) | 0.68 | 1.35 | 2.71 | 5.42 |

**Reading it:** if an employee would deliver about 1 QC a month, the system needs about half a QC a month at Rs 20,000, about one at Rs 35,000, and about one and a third at Rs 50,000.

### 7.3 Illustrative expected QCs (ASSUMPTION funnel; replace with pilot data)

The chain for each option, for a pool P over 90 days, pessimistic / central / optimistic:

| Step | Employee | System |
|---|---|---|
| Builders for whom a usable line to the **real owner** is found | 35% / 50% / 65% | 20% / 40% / 60% |
| Then: owner actually spoken to (employee) or message delivered (system) | 24.5% / 40% / 60% within 90 days. The low value is the Belkins 24.5% per prospect after about 3 tries [S14] | 29% / 45% / 60%. The low value is our own 2 of 7 on time [S19] |
| Then: agrees to a conversation (employee) or sends a genuine owner-level reply (system) | 4.6% / 8% / 15%. The low value is the Belkins conversation-to-meeting rate [S14] | 0% / 2.5% / 6%. 0% is our own 0 of 9; 1 to 2% is the low vendor claim [S15] |

Hybrid H2 = employee QCs + 0.7 x system QCs (30% overlap, ASSUMPTION). H1 = system QCs, with Sridhar as closer.

| Pool | Option | QCs in 90 days (pess / central / opt) | QCs a month |
|---|---|---|---|
| 72 | Employee | 0.3 / 1.2 / 4.2 | 0.09 / 0.38 / 1.4 |
| 72 | System | 0.0 / 0.3 / 1.6 | 0.0 / 0.11 / 0.52 |
| 72 | Hybrid H2 | 0.3 / 1.4 / 5.3 | 0.09 / 0.46 / 1.8 |
| **150** | Employee | 0.6 / 2.4 / 8.8 | 0.2 / 0.8 / 2.9 |
| **150** | System | 0.0 / 0.7 / 3.2 | 0.0 / 0.23 / 1.1 |
| **150** | Hybrid H2 | 0.6 / 2.9 / 11.0 | 0.2 / 1.0 / 3.7 |
| 470 | Employee | 1.9 / 7.5 / 27.5 | 0.6 / 2.5 / 9.2 |
| 470 | System | 0.0 / 2.1 / 10.2 | 0.0 / 0.7 / 3.4 |
| 470 | Hybrid H2 | 1.9 / 9.0 / 34.6 | 0.6 / 3.0 / 11.5 |

### 7.4 What the numbers say (INFERENCE, low confidence)

- **Central case:** rho = 0.28, so the cost-per-QC break-even fee is about **Rs 10,400** a month. A fee at or above Rs 20,000 does **not** beat an employee on this test.
- **The verdict flips if the system's reply rate is closer to the optimistic case:** system optimistic against employee central gives rho = 1.35 (break-even fee about Rs 50,000). System central against employee pessimistic gives rho = 1.14. No scenario is proven, which is the point: **rho is the quantity the pilot measures.**
- **Hybrid H2 costs S + Rs 36,900 for about 1.2 times the employee's QCs in the central case**, so it does not pay on cost per QC either. Its case is research time saved (the executive stops researching) and a higher ceiling if the reply rate is good.
- **Where the system is structurally better:** the first 3 months (an employee is still being hired and ramped), the cost of covering the whole list quickly, a written record, and the ability to cut the fee when the list is exhausted.
- **Where an employee is structurally better:** reaching an owner whose number is not public, holding a conversation, and Hindi or dialect on a phone call.

### 7.5 What a QC has to be worth

Let V be Sridhar's first-year contract value per customer (**his number; we do not have it**), c the share of QCs that become customers (ASSUMPTION 10% to 30%; no India source found), and k the share of V he will spend on getting the customer (his choice). Then cost per QC must be at most `k x c x V`.

Example with c = 20% and k = 30% (so cost per QC must be 6% of V): a cost per QC of Rs 46,000 (employee, central, pool 150) needs V of at least **Rs 7.7 lakh**; Rs 20,000 needs **Rs 3.3 lakh**; Rs 5,000 needs **Rs 0.83 lakh**. This is the real decision rule; whichever option clears it for his V is the right one.

---

## 8. How a pilot measures it [LIFTABLE]

**Fix these before the first message.** Use the same QC definition for the system and for any employee baseline.

| Measure | How counted | Baseline we have |
|---|---|---|
| Builders researched | Dossiers passing a human check | Gujarat: 34 candidates, 12 qualified |
| Owner coverage | Builders with a named real owner **and** a verified direct channel (named is not enough) | Gujarat: named for 6 of 9 contacted; direct-channel coverage not measured |
| Delivery rate | Delivered / sent, not "on time" | 2 of 7 on time (interval 3.7% to 71%) |
| Genuine reply rate | Owner-level two-way replies / delivered. Opens and reads are not counted | 0 of 9 |
| Time to hand-off | Minutes from a genuine reply to Sridhar being alerted | not yet measured on the alert path |
| Hand-off accuracy | Share of handed-off replies that were genuine (not stock greetings or auto-replies) | one stock greeting seen in campaign 1 |
| Cost per QC | (S + pass-through) / QCs, with Sridhar's hours reported beside it | |
| Employee baseline | Sridhar's last 3 months: demos booked by source, who did the outbound, time and cost | to ask him |

**Sample size (arithmetic):** at central coverage the 72-builder list gives about 29 builders with a usable line and **about 13 delivered messages** (150 builders: about 27; 470: about 85). With 13 delivered, zero replies still allows a true reply rate up to **21%** (one-sided 95%). With 27 delivered the chance of at least one genuine reply is 75% if the true rate is 5%, and 94% at 10%. With 45 delivered zero replies bounds the rate under 6.4%. **So the 72 list alone cannot give a verdict;** extend to at least 150 builders, or accept a verdict only on the signals of the first month.

**Decision rules (OPINION, to agree with Sridhar before sending):** continue if there are 2 or more genuine owner-level replies in the first 30 delivered messages to owner-level numbers (the same bar as our own playbook's "2 positives in 10 conversations"); change the offer, channel or segment if there are 0 of at least 30 delivered. Judge cost per QC against the section 7.5 rule, not against a hunch.

**Timetable (ASSUMPTION):** week 0 inputs and decisions; week 1 research and checking of the list, number and template set-up; week 2 first paced sends; weeks 2 to 5 follow-ups and hand-offs; week 6 report against this table. The pilot cannot say anything about close rate or sales-cycle length.

---

## 9. What may and may not be said to Sridhar [INTERNAL]

| May say | May not say |
|---|---|
| A fully loaded employee is about Rs 37,000 a month in Chhattisgarh (band Rs 20,000 to 67,000), with the sources and dates | That the system is "cheaper" without saying that it produces unproven conversations |
| The system is faster to start and covers the whole list; a person can confirm who the real owner is by phone | "Replaces a salesperson"; "instant"; any reply rate, meeting count or saving we cannot source |
| Our own first campaign has 0 replies from 9 contacts and 2 of 7 WhatsApp messages on time; this is why we propose a measured pilot | That delivery to cold numbers is reliable; that the AI will talk to owners; that other states are automated (Madhya Pradesh is a later, human-built list) |
| Every genuine reply goes to Sridhar immediately; the system never answers an owner | Anything about our internal cost-to-serve (Appendix A), or any Nexus360 price |

---

## 10. Sources (all read 20 Oct 2026 unless stated)

Salary and hiring
- S1: Indeed, BDE candidates Raipur, https://in.indeed.com/candidates/hire-business-development-executives-in-raipur-chhattisgarh (updated 19 Oct 2026).
- S2: PayScale, BDE Raipur, https://www.payscale.com/research/IN/Job=Business_Development_Executive/Salary/d619d36a/Raipur (last updated Jan 2021).
- S3: Raipur BDE postings via search (Apna, Indeed company pages, theindiajobs); posting dates not verified.
- S4: Indeed telemarketers / callers Raipur, https://in.indeed.com/candidates/hire-telemarketers-in-raipur-chhattisgarh and https://in.indeed.com/candidates/hire-callers-in-raipur-chhattisgarh (figures from search snippets); Indeed company pages for telecaller postings.
- S5: PayScale, Account Executive Inside Sales India, https://www.payscale.com/research/IN/Job=Account_Executive%2C_Inside_Sales/Salary (updated May 2024). S5b: PayScale Bangalore entry-level BDE, https://www.payscale.com/research/IN/Job=Business_Development_Executive/Salary/4ecf4109/Entry-Level-Bangalore (updated Apr 2022).
- S6: Hyring, BDE Bengaluru, https://hyring.com/jobseeker-toolkit/salary/business-development-executive-salary-in-bengaluru (modelled; updated 7 Jul 2026); Mumbai figure from search snippet. S6b: Talentup Bengaluru (search snippet, Aug 2025).
- S7: KnowledgeHut citing Glassdoor (secondary, undated), https://www.knowledgehut.com/blog/business-management/business-development-executive-salary.
- S8: PF ceiling raised to Rs 25,000 by S.O. 5109(E) dated 17 Sep 2026; ESI limit Rs 21,000, employer 3.25%: https://taxguru.in/?p=1086535 (7 Oct 2026) and https://www.ideasforindia.in/topics/human-development/the-ceiling-for-provident-fund-has-finally-moved-why-not-esi (9 Oct 2026). Verify against the Gazette before payroll use.
- S9: Recruitment-agency fee convention, https://goodspace.ai/blogs/recruitment-agency-fees-india and https://hyring.com/blog/recruitment-agency-fees-india/ (vendor blogs; weak).
- S11: Zoho CRM India prices via https://aaxonix.com/tools/zoho-pricing-calculator.html and https://cloudfysystems.com/blog/zoho-crm-pricing-india-2026 (third-party; confirm on Zoho's own page).
- S13: Aon India attrition 16.2% (2025), via Business Today, https://www.businesstoday.in/amp/latest/economy/story/lowest-in-five-years-what-162-attrition-really-signals-for-2026-518813-2026-03-02.

Productivity
- S10: The Bridge Group, SDR Models, Motions and Metrics 2025, https://www.bridgegroupinc.com/research/2025-sdr-models-metrics-report-the-bridge-group.
- S12: Callyzer, regional telesales benchmarks, https://callyzer.co/blog/wfh-telesales-performance-india/ (vendor; published 8 Dec 2025, updated 31 Jul 2026).
- S14: Belkins, cold calling benchmarks, https://belkins.io/blog/cold-calling-benchmarks (published 26 Jun 2026). S14b: Gong and Cognism figures via https://www.instantly.ai/blog/the-truth-about-b2b-cold-calling-in-2025-statistics-and-success-rates/ and https://ainora.lt/blog/cold-call-conversion-rate-every-study-2026 (secondary).
- S15: WhatsApp cold-outreach reply claims (vendor blogs): https://sbl.so/whatsapp/whatsapp-cold-outreach-reply-rates/ and https://firstsales.io/blog/whatsapp-cold-outreach-b2b/.

Platform, regulation, pool
- S16: Meta, WhatsApp Business Platform pricing, https://developers.facebook.com/docs/whatsapp/pricing/ (per delivered message; 1,000 free service messages a number a month; 1 Oct 2026 changes; INR billing, migrate by 31 Dec 2026).
- S17: India marketing rate Rs 0.8631 from 1 Jan 2026 (MSG91 and Fyno via search results); BSP markup 10 to 25% (one source). Our blueprint also records about Rs 0.86.
- S18: Chhattisgarh RERA public list, https://rera.cgstate.gov.in/Approved_project_List.aspx, fetched 20 Oct 2026 by `cg_rera_demo.py`; files `cg_rera_demo_summary.txt`, `cg_rera_public_list.csv`.
- S19: Our files: `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, `agent/docs/CAMPAIGN_LEARNINGS.md`, `agent/docs/AGENTIC_SALES_BLUEPRINT.md`.
- S20: TRAI, 140-series for promotional calls by registered telemarketers (search results, trai.gov.in press release no. 111 of 2026). Whether ordinary B2B calls from a 10-digit number are covered was not established.
- S21: USD/INR about 96.5, undated, https://pluang.com/en/tools/currency-converter/usd-inr.

---

## Appendix A. Our cost to serve and price floor [INTERNAL, remove before sharing]

### A.1 Cost per builder (ASSUMPTION built on measured token use)

- Measured: round 2 used about 4.1M tokens for 34 candidates (about 121,000 per candidate) and about 342,000 per qualified lead; round 1 about 220,000 per qualified lead [S19].
- Price: Sonnet 5.5 at $2 input / $10 output per million tokens [own blueprint], 85:15 mix (ASSUMPTION) = $3.2 per million; Rs 95 per dollar.
- Compute per builder: **Rs 37 (121K tokens) / Rs 76 (250K) / Rs 208 (684K, i.e. 2x the per-qualified figure for an owner hunt)**. The blueprint's own estimate is about $0.49 per fully worked lead (about Rs 47).
- Human checking: 5 / 8 / 12 min per builder at Rs 375 an hour (ASSUMPTION Rs 250 to 500) adds Rs 31 / 50 / 75.
- **Cost to serve per 100 builders researched: Rs 6,800 / 12,600 / 28,300**, against Rs 15,700 / 21,000 / 31,500 for a person doing the same depth. **On research alone the system is not dramatically cheaper; its edge is speed, coverage and records.**
- Video: Rs 0 (local render, 1.5 to 5 min) to Rs 119 (bespoke vendor, about $1.25) per qualified builder; Rs 60 used. Apify about $0.05 per surviving lead (negligible).

### A.2 Monthly cost to serve

| Month | Compute | Video | WhatsApp | Staff time | Tools | **Total** |
|---|---|---|---|---|---|---|
| Month 1 (150 builders, 50 videos, 12 h a week) | Rs 11,400 | Rs 3,000 | Rs 264 | Rs 19,350 | Rs 3,000 | **Rs 37,014** |
| Steady month (about 8 new builders plus follow-up, 6 h a week) | Rs 608 | Rs 180 | Rs 98 | Rs 9,675 | Rs 3,000 | **Rs 13,561** |
| **3-month pilot** | | | | | | **Rs 64,136, average Rs 21,400 a month** |

Tools Rs 3,000 a month (server, domain, monitoring) is an ASSUMPTION. Staff time is the real cost driver: our own blueprint says the owner's review time is, and a wave in campaign 1 needed 68 minutes of approvals after the proposals [S19].

### A.3 Consequences for the fee

- A fee below about **Rs 21,400 a month for a 3-month pilot loses money** on this accounting, unless a setup fee covers month 1 (cost Rs 37,000).
- After the sweep, the run cost is about Rs 13,600 a month; a step-down fee is possible and honest because the list refills at about 4 builders a month.
- Compare section 7.4: at the central funnel the cost-per-QC break-even fee (about Rs 10,400) is below our own cost to serve. **If the central funnel is right, no profitable fee beats an employee on cost per QC.** The case for the pilot then rests on the optimistic reply rate being real, on the research and speed advantages, and on capping Sridhar's downside. Say so to him.

### A.4 Open points and owner decisions

1. The fee S and whether it is a pilot price, a retainer, or per-builder blocks (the estimate workstream).
2. Show Sridhar the central funnel (7.3) or only the formula and the pilot measures (7.1, 7.2, 8)? Recommended: show the formula, the 0 of 9 and 2 of 7, and the pilot measures; share 7.3 only if he asks how we expect it to go.
3. A dedicated WhatsApp number for Nexus360 outreach so a restriction does not hit the shared demo, sales-agent and owner-alert number (campaign 1 diagnosis); and a routing rule for this account so that no automated agent ever answers a builder-owner (today an inbound reply reaches the AI agent first [S19]).
4. Data export and exit terms if the system is stopped.
5. Whether to put a commission-only caller in front of Sridhar as the fourth option.
6. Ask Sridhar for his real hiring cost, his last 3 months of demos by source, and his first-year contract value V.
