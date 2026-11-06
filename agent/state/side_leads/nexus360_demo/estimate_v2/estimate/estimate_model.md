# Nexus360 side lead: lean, deliverable INDICATIVE estimate (cost model v2)

Prepared Tue 20 Oct 2026 for the owner of IV Infotech. **INTERNAL.** Our cost lines, hour rates and margin are in here, so this file does not go to Sridhar. Sections marked **[LIFTABLE]** are written in plain English so they can be copied into the short estimate after the owner approves them.

All money is INR before 18% GST. The arithmetic is in `estimate_model.py` (same folder; change an input, rerun, it rewrites `estimate_model.json`). It builds on `proposal/unit_costs/unit_costs.md` and `proposal_lowprice/`.

Labels: **FACT** = sourced (URL or repo file). **INFERENCE** = my reading of facts. **OPINION** = my recommendation. **ASSUMPTION** = no source, a range is shown. Hours are IV Infotech staff hours.

---

## 0. Owner ke liye seedha jawab (Hinglish)

**1 lead ka cost (hamari side). "Lead" ko teen tarah se gino:**

| Kya gin rahe ho | Kharcha (Rs 1,000 per hour maan ke) | Seedhi baat |
|---|---|---|
| 1 builder ki research + hamara check | **lagbhag Rs 100** (kam Rs 60, zyada Rs 210) | AI Rs 23 + hamara 4.5 minute |
| 1 builder jisko WhatsApp bhej sakte hain | **lagbhag Rs 600** | kyunki 6 mein se sirf 1 ka number WhatsApp wala mila |
| 1 builder jisko message pahunch gaya (delivered) | **lagbhag Rs 1,300** (Rs 1,000 se Rs 2,000) | 45% delivery pe |
| Poora pilot ka kharcha / delivered builders (setup mila ke) | **lagbhag Rs 12,000** | setup bahut kam builders pe baat jaata hai |

- **WhatsApp ka kharcha chhota hai.** 1 message Rs 1.5, 2 message = Rs 3 per builder. Poore pilot mein WhatsApp Rs 200 se kam. **Asli kharcha hamara time hai**, WhatsApp nahi.
- **Badi problem: reach.** 6 builders ke test mein sirf 1 ka business-published number WhatsApp pe chalta tha (sach 3% se 56% ke beech ho sakta hai, kyunki sirf 6 ka test hai). Matlab 50 builders mein se shayad **8 ko hi message** ja paaye (kam se kam 2, zyada se zyada 28), aur unme se shayad 2 se 5 ko pahunche (17% reach pe). Isliye pilot "message ka test" kam hai, "research list + system chalta hai ya nahi ka test" zyada hai. Reach badhane ke raaste (email, RERA wala mobile) Section 5 mein hain. Ye aapka aur Sridhar ka decision hai.
- **Claude plan ($100) pe client ka kaam mat chalao.** Hamare 14 Oct ke notes mein koi source nahi mila jo paid, unattended service ko personal subscription pe allow kare. Client ka kaam **API key (pay-per-use)** pe chalao. Isse plan badle ya mehnga ho, estimate pe asar nahi padta.
- **Nayi baat (aaj verify ki):** Max 5x plan ($100) ke saath har mahine **$100 ka API credit** milta hai (Anthropic ka help page; 7 Oct 2026 ko announce hua, rollout dheere-dheere). Ye credit Claude Code mein nahi chalta, lekin hamari script (API) mein chalta hai. Rs 23 per builder pe ye credit lagbhag **410 builders** cover karta hai. Agar credit na dikhe ya band ho jaye, to bhi 150 builders ka AI kharcha sirf Rs 3,500 per month hai.
- **Estimate (before GST), meri recommendation:**
  - **Pilot Standard (50 builders, sirf Chhattisgarh): from Rs 48,000.** Hamari cost Rs 1,000/hour pe Rs 46,300, Rs 500/hour pe Rs 24,800.
  - **Pilot Starter: from Rs 35,000**, lekin sirf tab jab Section 4.6 ki 7 cheezein hata do. Ye Rs 930/hour tak break-even hai.
  - **Rs 35,000 Standard scope pe nahi chalega.** Standard pe Rs 35,000 sirf Rs 737/hour tak theek hai. Rs 1,000/hour pe Rs 11,300 ka loss.
  - **Monthly: from Rs 30,000, up to 100 builders** (150 builders ke liye Rs 36,000). Rs 30,000 mein 150 builders sirf tab jab review time 4.5 minute rahe; warna loss. List khatam hone ke baad (mahina 4 se) lagbhag Rs 15,000.
  - **WhatsApp:** Rs 1.5 per delivered marketing message + GST, at cost, pilot mein cap Rs 300.
- **Pehle ye confirm karo:** (1) Fortius se: Rs 1.5 sirf delivered pe lagta hai ya bhejne pe; GST alag hai ya nahi; +91 number mil sakta hai ya nahi. (2) claude.ai Settings > Billing mein "API credits" dikhta hai ya nahi. (3) 6 builders pe naya pipeline ek baar chala ke token/cost naap lo (calibration). Details Section 8 mein.

---

## 1. Short answers

1. **Cost of one lead, our side (FACT inputs, ASSUMPTION hours):** Rs 59 / 100 / 212 (low / base / high) per researched builder at Rs 1,000 an hour; Rs 38 / 63 / 137 at Rs 500 an hour. WhatsApp adds Rs 3 per messaged builder (2 messages, delivered).
2. **Cost per delivered builder:** variable Rs 1,340 at 17% reach and 45% delivery (range Rs 300 to 2,000 over the reach and delivery cases); pilot all-in about Rs 12,300 at the same point.
3. **Capacity:** on the USD 100 plan alone, unknown (no absolute quota is published). Client work goes on pay-per-use API at about Rs 23 per builder (Rs 15 to 60). Safe volume: up to 100 builders a month for months 1 to 3, then about 40.
4. **Pilot:** Standard from **Rs 48,000** (42.9 h base, cost Rs 46,300 at Rs 1,000 an hour). Starter from **Rs 35,000** with 7 cuts worth 8.3 hours. Rs 35,000 on the Standard scope is only a Rs 737 an hour price.
5. **Monthly:** from **Rs 30,000 for up to 100 builders**; Rs 36,000 for 150. Rs 30,000 for 150 is not safe.

---

## 2. (a) Cost of one lead, our side

### 2.1 Inputs

| Input | Low | Base | High | Tag and source |
|---|---|---|---|---|
| BSP price per MARKETING message | Rs 1.5 | Rs 1.5 | Rs 1.5 | FACT (owner, 20 Oct). Meta's list rate of Rs 0.8631 is NOT used. **Billing basis unknown**: Meta itself charges a business only for messages that were delivered (FACT, Meta pricing page read 20 Oct 2026), our BSP may differ. Confirm with Fortius, and whether Rs 1.5 is before GST |
| Touches per messaged builder | 2 | 2 | 2 | Owner rule (first message plus one follow-up) |
| Numbers messaged per builder | 1 | 1 | 1 | ASSUMPTION |
| Share of builders with a business-published number wired for WhatsApp | 17% | 35% | 56% | **FACT for 1 of 6** (n = 6, 95% Wilson interval 3% to 56%; `enrichment/enrichment.md`). 35% is an ASSUMPTION |
| Share of builders with an owner or decision-maker named | 67% (4 of 6, interval 30% to 90%) | | | FACT, n = 6, none of the four fully verified |
| Delivery of a cold marketing template | 30% | 45% | 60% | FACT anchors: our own campaign delivered 2 of 7 on time (29%); 3 of 7 if the one 4 hours late counts (43%) (`CAMPAIGN1_DIAGNOSIS_2026-10-20.md` item 4) |
| AI per builder, current agent-workflow style (owner's note) | Rs 24 | Rs 76 | Rs 279 | FACT as recorded in `unit_costs.md` (FX 88/90/95, 20% contingency) |
| AI per builder, lean pipeline (Section 3) | Rs 15 | Rs 23 | Rs 60 | ASSUMPTION design target; prices FACT. Measured by a 6-builder calibration before the price is final |
| Human review per builder | 2.5 min | 4.5 min | 9 min | 4.5 = 3 min dossier check + 1.5 min message check (20 Oct model). 9 min = manual registry lookups, enrichment test said 5 to 10 min |
| Value of one staff hour | Rs 500 | Rs 1,000 | Rs 1,500 | Owner's range is Rs 500 to 1,000; Rs 1,500 is a stress test |
| Video render | master only, about Rs 2 | | | see 2.4 |
| Voice licence | Rs 0 | Rs 540 a month | Rs 1,100 | FACT in our notes (ElevenLabs Starter USD 6 has the commercial licence); Rs 0 if Sridhar records the voice |
| USD to INR | 92 | 96.5 | 100 | ASSUMPTION. Last datapoint found: 96.5 on 22 Jul 2026 (pluang.com; 52-week range 86.25 to 96.96). The 20 Oct unit-cost file used 90, so its AI figures are about 7% light |

### 2.2 Variable cost of one researched builder (our side)

AI (lean) + human review + about Rs 2 for page, render share and hosting. WhatsApp is separate (passed through).

| Hour value | Low (16 + 2.5 min) | **Base (23 + 4.5 min)** | High (60 + 9 min) |
|---|---|---|---|
| Rs 500 an hour | Rs 38 | **Rs 63** | Rs 137 |
| Rs 1,000 an hour | Rs 59 | **Rs 100** | Rs 212 |
| Rs 1,500 an hour | Rs 80 | **Rs 138** | Rs 287 |

- Per builder with an owner named (4 of 6): Rs 100 / 0.67 = about Rs 150 (INFERENCE).
- Fixed items spread over a 50-builder pilot add about Rs 21 per builder (voice Rs 540 plus hosting Rs 500, divided by 50); over a 150-builder month about Rs 14.
- If the AI cost were the owner's as-is figures (Rs 76 base, Rs 279 high) instead of lean, the 50-builder pilot costs Rs 2,600 (base) or Rs 11,000 (high) more in cash.

### 2.3 Cost per messageable and per delivered builder (the reach problem)

Only builders with a business-published WhatsApp-capable number can be messaged. Whole 50-builder pilot, base cost. "Variable" = research + review + messages for all 50, divided by the builders who got a message. "Pilot all-in" = Rs 46,302 (cost at Rs 1,000 an hour, 42.9 h, cash Rs 3,386) divided by the same count.

| Reach (builders messageable) | Builders messageable of 50 | Variable per messageable builder (Rs 500 / 1,000 an hour) | Pilot all-in per messageable builder (Rs 500 / 1,000) |
|---|---|---|---|
| 17% (observed 1 of 6) | 8.3 | Rs 378 / **603** | Rs 2,981 / **5,556** |
| 35% (assumption) | 17.5 | Rs 181 / 288 | Rs 1,420 / 2,646 |
| 56% (top of interval) | 28 | Rs 114 / 180 | Rs 887 / 1,654 |

Cost per DELIVERED builder (first message delivered), at Rs 1,000 an hour:

| Reach | Delivery | Builders delivered of 50 | Variable per delivered builder | Pilot all-in per delivered builder | Monthly run (150 builders) all-in per delivered builder |
|---|---|---|---|---|---|
| 17% | 30% | 2.5 | Rs 2,009 | Rs 18,521 | Rs 3,218 |
| 17% | **45%** | 3.8 | **Rs 1,340** | **Rs 12,347** | Rs 2,145 |
| 17% | 60% | 5.0 | Rs 1,006 | Rs 9,260 | Rs 1,609 |
| 35% | 30% | 5.3 | Rs 958 | Rs 8,819 | Rs 1,532 |
| 35% | 45% | 7.9 | Rs 640 | Rs 5,880 | Rs 1,022 |
| 35% | 60% | 10.5 | Rs 481 | Rs 4,410 | Rs 766 |
| 56% | 30% | 8.4 | Rs 600 | Rs 5,512 | Rs 958 |
| 56% | 45% | 12.6 | Rs 401 | Rs 3,675 | Rs 639 |
| 56% | 60% | 16.8 | Rs 302 | Rs 2,756 | Rs 479 |

At Rs 500 an hour the pilot all-in figures are about 46% lower (for example Rs 6,625 at 17% reach and 45% delivery).

How many builders must be researched to get 30 delivered first messages (a number that starts to say something about replies):

| Reach | 30% delivery | 45% | 60% |
|---|---|---|---|
| 17% | 600 | 400 | 300 |
| 35% | 286 | 190 | 143 |
| 56% | 179 | 119 | 89 |

**INFERENCE:** reach, not volume or WhatsApp fees, decides what a lead costs. A 50-builder pilot cannot give a reply-rate verdict (the owner notes already say about 150 builders at least). What it tests is: can we name owners with evidence, does the pipeline run inside budget and caps, do messages and hand-offs work, and does Sridhar like the records.

### 2.4 Video render time: what I can verify

- **5 minutes**: an older planning figure (the 19 Oct playbook). `CAMPAIGN_LEARNINGS.md` already says "~1.5 min each, not 5" and to plan 2 to 5 min until re-measured.
- **About 1.45 minutes (87 s) per 38-second video: VERIFIED.** Wave 2 rendered 4 videos from 12:20 to 12:26 on 19 Oct (`CAMPAIGN_LEARNINGS.md`, "Time and cost"). Two of those files in `agent/state/outreach/assets/renders/` carry modification times 87 seconds apart (12:21:50 and 12:23:17), which fits. `render_master.py` captures frames at 30 fps through Playwright and encodes with ffmpeg.
- **About 40 seconds**: the page-and-video workstream's figure for the new 17-second Nexus360 animatic. It is a calculation (510 frames at the campaign's 13.1 frames per second), not a measured render of that video. No Nexus360 video has been rendered yet.
- **Cost:** machine time only, on our own PC, so Rs 2 per video is an ASSUMPTION for electricity and wear. The lean pilot renders ONE master video, so render cost is about Rs 2 in total. The per-builder video option is priced in Section 5 (D2).

---

## 3. (b) Capacity under the Claude plan, and a cheaper per-builder pipeline

### 3.1 What our heavy workflows consumed (FACT from our own files)

| Run | Reported tokens | Agents | Time |
|---|---|---|---|
| Round 1 lead research, 15 Oct | 2.2M | 14 | about 34 min |
| Round 2 lead research, 19 Oct | 4.1M | 26 | 63 min |
| Retrospective, 19 Oct | 1.7M | 6 | 20 min |
| 6 PM check, 19 Oct | about 1M | 8 | n/a |
| Campaign-1 diagnosis, 20 Oct | 3.3M | 14 | 40 min |
| **All 17 campaign workflows, 15 to 19 Oct** | **14.55M** (research 6.30M, tooling reviews 4.39M, QA and fact-check 3.42M, script 0.44M) | n/a | 218 min |

Sources: `agent/memory.md`, `agent/docs/CAMPAIGN_LEARNINGS.md` ("Time and cost"), `CAMPAIGN1_DIAGNOSIS_2026-10-20.md`. Tokens per qualified lead: about 220k (round 1) and 342k (round 2); per candidate about 121k to 129k.

What those runs did to the plan: the weekly limit was 94 to 95% used on 15 to 16 Oct with a hard cut on 15 Oct 12:13 IST (`CAMPAIGN_LEARNINGS.md`, `memory.md`); on 20 Oct the proposal workflow's fix step hit the session limit (`memory.md`, 20 Oct entry).

### 3.2 What is honestly unknown

- **Plan quota: UNKNOWN.** Anthropic publishes no absolute numbers for Pro or Max, only relative limits (Max gives 5x or 20x Pro's usage per 5-hour session) plus weekly limits (claude.com/pricing, read 20 Oct 2026); our own 14 Oct research reached the same conclusion, that 24/7 capacity cannot be estimated from the docs. Web, desktop and Claude Code draw from one pool. Our plan name is not recorded in our files; USD 100 matches the entry Max tier (the pricing page shows Max as "From $100").
- **Unit mismatch.** The figures above are workflow-reported agent totals. How many of them were cheap cache reads, and how they map to plan percent, is unknown. I will not convert them into a builders-per-month number for the plan.
- **What the rough comparison does say (INFERENCE):** the workflows of 15 to 19 Oct alone add up to about 14.55M reported tokens, and that week already had a hard cut (15 Oct) before today's session limit. One lean 50-builder pilot is about 6.7M tokens (134k each). The as-is style (300k each) would be 15M, the same as those five days. A 150-builder month is 20M (lean) or 45M (as-is). Nothing here leaves room for client work on the plan next to our own work.
- **Terms (FACT from our 14 Oct research, `research_subscription_24x7_2026-10-14.json`, medium confidence):** Consumer Terms section 3 bars automated or non-human access (bots, scripts) unless it goes through an API key or Anthropic explicitly permits it; the Claude Code legal page says developers building products or services should use API keys, and that customers may not resell or intermediate Claude usage on behalf of their own end users. No source permitting an unattended paid service on a personal subscription was found. The owner accepted the subscription route for supervised use of our own operator, not for a paid client pipeline.

### 3.3 New finding that changes the plan (checked 20 Oct)

**Max 5x includes USD 100 a month of API credit; Max 20x USD 200.** Sources: Anthropic's help article https://support.claude.com/en/articles/17154008-api-credits-for-max-and-team-plans and the platform page https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers (the 7 Oct 2026 announcement date and the staged rollout come from third-party write-ups found by search; Anthropic's page shows no date).

- Covers the Claude API, Managed Agents, the Agent SDK and `claude -p` run with an API key from the linked Console organisation. **Does not cover interactive Claude Code** (so not our desktop sessions) and does not raise plan limits.
- You link one Console organisation (Owner/Admin/Billing role there); credits arrive each billing cycle; **unused credits expire** at cycle end; new subscribers can claim after 7 days. Spending is capped per workspace if you set a limit. When the balance is gone, requests stop; usage is never charged to the plan.
- Credit terms (https://www.anthropic.com/legal/credit-terms, read 20 Oct): credits may be used only by the account holder, may not be transferred or sold, have no cash value. They are silent on client work. **So I treat the credit as our own prepaid balance, price AI at API-equivalent cost, and never resell tokens.** If the credit turns out not to apply to client work, we buy credits; the estimate does not move (AI is 2.4% of the Rs 48,000 pilot).
- Our own account may not show the offer yet (staged rollout) or may be a different tier. Check claude.ai Settings > Billing > API credits.
- **Operational trap (FACT, `memory.md`):** `claude -p` uses an API key whenever one is in the environment. Run the client pipeline as its own script/service with its own key and its own Console workspace spend limit, never in the shell that holds the subscription login.

### 3.4 The cheaper per-builder pipeline (design target)

Principle: scripts do everything that is rules (no tokens), a small model does the bulk reading, ONE deeper call per builder does the hard part (who is the real owner). A hard budget meter stops a builder at Rs 100 or 300k tokens and writes UNKNOWN.

| # | Step | Done by | Tokens in / out (base) | USD (base) |
|---|---|---|---|---|
| 1 | Pull the full CG register list (one request, about 11 MB) | script, exists (`cg_rera_demo.py`) | 0 | 0 |
| 2 | Filters: district, valid, last 18 months, housing, not government; size by the **filed project cost** (free on the detail page) instead of "3 or fewer projects" | script | 0 | 0 |
| 3 | Detail page for each shortlisted builder (authorised name, promoter type, address, cost, filed contact): one per about 13 s, so 50 take about 11 minutes | script, polite pace | 0 | 0 |
| 4 | Group resolution (one business under several promoter names): cluster by authorised name, email domain, address | script | 0 | 0 |
| 5 | Builder website: render JavaScript sites, open About / Director / Contact, read footers, `tel:`, `wa.me`, `mailto`, the WhatsApp widget number | Playwright script | 0 | 0 |
| 6 | Page text to structured facts (names, roles, quote under 15 words, contact class) | small model (Haiku 5.5), each call under 100k tokens | 70k / 6k | 0.010 |
| 7 | **Owner identification, one targeted call with web search** (6 searches), evidence URLs, label VERIFIED / LIKELY / UNKNOWN | deeper model (Sonnet 5.5), 1 call | 45k / 4k | 0.130 + 0.060 search |
| 8 | Record write-up and message slot fill | small model | 8k / 1k | 0.001 |
| 9 | Rule checks: the quoted name really appears on the cited page, evidence under 30 days old, contact class | script | 0 | 0 |
| 10 | Human gate, 4.5 minutes | a person | n/a | n/a |

**Target tokens per builder: about 134k (low 84k, high 253k), hard cap 300k.** About two thirds go to the small model. **Cost with 20% contingency: Rs 15 / 23 / 60 (USD 0.16 / 0.24 / 0.60 at Rs 92 / 96.5 / 100).** Prices (FACT, platform.claude.com/docs/en/about-claude/pricing, read 20 Oct 2026): Haiku 5.5 USD 0.10 in / 0.50 out per million tokens for prompts up to 100k; Sonnet 5.5 USD 2 / 10; web search USD 10 per 1,000; Batch API is 50% off and not counted.

Honest notes:
- **Tokens are not much below our observed 121k to 342k per candidate** (INFERENCE). Cost is lower because most tokens move to a model about 20 times cheaper, the shortlist comes from a script (no scouting waste), nothing is re-read by multi-agent loops, and no Apify is needed (Apify's monthly limit was hit on 15 Oct and still blocked on 19 Oct, `CAMPAIGN_LEARNINGS.md`).
- **Quality of the small model on owner extraction is untested (UNKNOWN).** Gate 0 below tests it before we quote a fixed price.
- Gujarat figures came from a discovery job; the Chhattisgarh job starts from a given list, so they are only a rough upper reference.

**Gate 0, calibration (about 1.5 h, about Rs 140 of API):** run the pipeline on the 6 builders we already researched by hand. Pass if: tokens at or under 250k and cost at or under Rs 60 per builder; owner or decision-maker found for at least 3 of the 4 we named by hand; the one WhatsApp-wired number found; no invented names (every named person appears on the cited page). Measure tokens from the `usage` field the API returns on every call. Fail means: fall back to the current agent workflow with a budget cap (Rs 76 base, Rs 279 high per builder) and accept the extra Rs 2,600 to 11,000 on the pilot.

### 3.5 AI price and plan shocks (Rs per builder, with contingency)

| Case | Low | Base | High |
|---|---|---|---|
| Today (lean) | 15 | **23** | 60 |
| All AI prices double | 30 | 47 | 119 |
| All AI prices x5 | 76 | 117 | 298 |
| Deep call on Opus 5.5 (USD 4 / 20) | 25 | 38 | 100 |
| Deep call on Fable 5.1 (USD 10 / 50) | 55 | 84 | 223 |
| Small model withdrawn, all on Sonnet 5.5 | 30 | 48 | 98 |

Even x5 at base is Rs 5,800 on a 50-builder pilot, 12% of Rs 48,000. A plan price rise from USD 100 to 200, or a cut in plan limits, changes nothing in the client estimate because client work is not on the plan.

### 3.6 Monthly builders we can safely serve

| Limit | What it allows | Basis |
|---|---|---|
| AI money, USD 100 credit (Rs 9,650) if claimable | 414 builders (lean base), 162 (lean high), 127 (as-is base), 35 (as-is high) | calculation |
| AI money without the credit (pay-per-use) | no limit; 150 builders cost Rs 3,500 (base) to 8,900 (high) | calculation |
| Our review hours: 20 h a month (ASSUMPTION) minus the fixed monthly hours (7.6 h base, 12 h high) | about 166 builders at 4.5 min; 53 at 9 min | calculation |
| The pool of builders | 72 shortlisted now; about 424 on a loose rule (3 districts, 3 or fewer projects, no date limit); all CG about 798; then about 4 new qualifying builders a month (8.4 new valid approvals a month) | `cg_rera_demo_summary.txt`, `unit_costs.md` section 6B |
| Meta new-portfolio cap | 250 unique recipients per 24 h until business verification: not binding at 100 a month | FACT, our research 14 Oct |
| Plan quota (if the plan were used) | UNKNOWN | 3.2 |

**Recommendation (OPINION):** run client work on a pay-per-use API key with its own Console workspace and spend limit, funded first by the plan's USD 100 credit if it can be claimed. Safe volume: **up to 100 builders a month for months 1 to 3**, then about 40 a month plus follow-ups, because the pool runs out (424 / 100 is about 4 months). The binding limits are the pool and our review time, not AI money.

**Clause to add [LIFTABLE]:** see Section 4.8, clause "price_change".

---

## 4. (c) The temporary estimate: pilot (and monthly run)

### 4.1 Scope and explicit caps [LIFTABLE]

Pilot of up to 50 builders in Chhattisgarh, about 14 days of sending, report on Day 17. Start about 7 working days after we have Sridhar's inputs (Meta approved our earlier template in 16 to 20 minutes, but whether our BSP can give a +91 number is unknown, see Section 8).

1. **Builders:** up to 50, Chhattisgarh only, chosen from the public RERA register by rules agreed at the kickoff call.
2. **Research depth:** one record per builder with sources and date, a VERIFIED / LIKELY / UNKNOWN label, up to 10 manual company-record lookups, and a time-box per builder; a builder we cannot resolve inside it is marked UNKNOWN.
3. **Messages:** WhatsApp only, English only, at most 2 per builder and 100 in total, only to numbers the business itself published, only after our check, STOP honoured at once, sending paused on any Meta quality warning.
4. **Video and page:** ONE master video (up to 45 seconds) and one personalised page per messaged builder, built from register fields. No per-builder video.
5. **Hand-off:** every genuine reply forwarded to one person and number Sridhar names; up to 30 alerts. The AI never answers an owner.
6. **Dashboard:** read-only view for up to 2 people for the pilot plus 14 days; CSV export at the end.
7. **Reports:** one mid-pilot note and one final report on Day 17, with an updated estimate for what comes next.
8. **Change rounds:** one round of changes to page, video or message text; further rounds quoted in hours before work starts (Rs 1,000 an hour).
9. **Not included:** calls, email, CRM integration, Hindi or Gujarati, other states, Madhya Pradesh, any reply handling by us.
10. **Sridhar provides:** districts and exclusion list of his customers; name and WhatsApp number of the person who takes replies; two short screen recordings of Nexus360 (or permission to use his website visuals); logo; approval of the message text; a 20-minute call each week.

### 4.2 Hours: what is in, what was cut (Standard)

| Line | Low | Base | High | Previous base (20 Oct low-price model) | What changed |
|---|---|---|---|---|---|
| S1 Research pipeline: detail-page pull, group resolution, contact extraction, model calls, budget meter, record format, Gate 0 calibration | 6 | 9 | 14 | 5 | **+4 h on purpose.** Scripts replace agent work, so AI cost falls and no plan is needed. Reusable for every later run |
| S2 ONE master video (English) + script-filled builder page | 4 | 6 | 9 | 15 | **-9 h.** No per-builder video, no Hindi cut, designs, animatic and sample page already exist, Sridhar supplies recordings |
| S3 +91 number, display name, 2 templates, BSP rate and billing confirm, Meta approvals | 3 | 4 | 5 | 4 | same |
| S4 Forward-only reply routing to Sridhar, STOP rule, alert test | 4 | 6 | 8 | 6 | same (Sridhar's own rule) |
| S5 Read-only view (viewer login scoped to this campaign only, numbers masked, CSV) | 3 | 5 | 8 | 8 | **-3 h.** Reuse existing pages, no new charts |
| S6 Claims and copy QA, test sends to our phones, go-live check | 2 | 3 | 4 | 3 | same |
| **Setup** | **22** | **33** | **48** | 41 | -8 |
| R1 Review 50 builders (2.5 / 4.5 / 9 min each) | 2.1 | 3.75 | 7.5 | 3.75 | same |
| R2 Daily send and reply check, 14 days (3 / 5 / 10 min) | 0.7 | 1.2 | 2.3 | 1.7 | -0.5 |
| R3 Kickoff call and requirement capture | 0.75 | 1.0 | 1.5 | in syncs | |
| R4 Mid-pilot note + final report and review call | 1.75 | 3.0 | 4.5 | 4.5 | -0.5 versus 2 syncs + report |
| R5 Upkeep (Meta quality, template and script fixes) | 0.5 | 1.0 | 3.0 | 1.0 | same |
| **Running** | **5.8** | **9.9** | **18.8** | 10.9 | -1.0 |
| **Total hours** | **27.8** | **42.9** | **66.8** | **51.9** | **-9.0** |

Cuts that keep the price down by leaving things out (hours avoided if they were in; from the driver table, all ASSUMPTION): per-builder video (3 to 5 h once plus 1 to 2.5 h per 50), Hindi or Gujarati variant (4 to 7 h), CRM integration (not quotable, bracket 6 to 40 h), email (5 to 9 h once), calls by us (8 to 25 h per 50), another state (8 to 20 h each), faster start (4 to 12 h), custom dashboard views (3 to 8 h), extra reports (2 to 4 h a month).

### 4.3 Cash (excluding WhatsApp, which is passed through)

| Line | Low | Base | High |
|---|---|---|---|
| AI, 50 builders, lean | 757 | 1,166 | 2,980 |
| Report and dashboard model calls | 90 | 180 | 450 |
| Voice licence (0 if Sridhar records) | 0 | 540 | 1,100 |
| +91 number, domain, setup (BSP fee for a second number is UNKNOWN) | 0 | 1,000 | 3,000 |
| Hosting allocation | 0 | 500 | 1,500 |
| **Cash** | **847** | **3,386** | **9,030** |

### 4.4 Price test: our cost, and margin or loss (Standard scope)

Our cost (cash + hours x rate), matching low/base/high for hours and cash:

| Hour value | Low (27.8 h) | **Base (42.9 h)** | High (66.8 h) |
|---|---|---|---|
| Rs 500 | 14,737 | **24,844** | 42,447 |
| Rs 1,000 | 28,627 | **46,302** | 75,860 |
| Rs 1,500 | 42,517 | **67,761** | 109,275 |

Margin (+) or loss (-) in Rs, Standard scope:

| Price | Hour value | Low hours | **Base hours** | High hours |
|---|---|---|---|---|
| **Rs 35,000** | 500 | +20,262 | **+10,156** | -7,447 |
| | 1,000 | +6,370 | **-11,302** | -40,864 |
| | 1,500 | -7,522 | -32,761 | -74,280 |
| **Rs 48,000** (recommended) | 500 | +33,262 | **+23,156** (48%) | +5,553 |
| | 1,000 | +19,370 | **+1,698** (3.5%) | -27,864 |
| | 1,500 | +5,478 | -19,761 | -61,280 |

Break-even hour value (the highest value of an hour at which the price still covers cost):

| Price | Low hours | Base hours | High hours |
|---|---|---|---|
| Rs 35,000 | 1,229 | **737** | 389 |
| Rs 40,000 | 1,409 | 853 | 463 |
| Rs 45,000 | 1,589 | 970 | 538 |
| **Rs 48,000** | 1,697 | **1,040** | 583 |
| Rs 50,000 | 1,769 | 1,086 | 613 |

**Reading:** Rs 35,000 on the Standard scope is only right if an hour is worth Rs 737 or less and hours stay at base. Rs 48,000 covers base hours up to Rs 1,040 an hour, which is the top of the owner's Rs 500 to 1,000 range. The high-hours case (66.8 h) is covered only at Rs 583 an hour; the protection is the caps: the per-builder time-box, the AI budget meter, 10 manual lookups, one change round, and the rule that extra scope is quoted first. The old Rs 75,000 was cost at Rs 1,000 an hour plus 30% margin on 51.9 h; Rs 48,000 is cost at Rs 1,000 an hour with 3.5% margin on 42.9 h.

If the AI cost turned out as in the owner's as-is notes instead of lean, add Rs 443 / 2,634 / 10,970 (low / base / high) to cash; base margin at Rs 48,000 and Rs 1,000 an hour then becomes -Rs 937.

### 4.5 Delivery test: does 30% versus 60% delivery change our margin?

At Rs 48,000, base hours and cash, Rs 1,000 an hour:

| Reach | Delivery | Messages sent (of max 100) | Delivered | Billed to Sridhar (pass-through, before GST) | **Our margin if the BSP bills delivered only** | Our margin if the BSP bills every message sent |
|---|---|---|---|---|---|---|
| 17% | 30% | 16.7 | 5.0 | Rs 7.5 | **+1,698** | +1,680 |
| 17% | 60% | 16.7 | 10.0 | Rs 15 | **+1,698** | +1,688 |
| 35% | 30% | 35 | 10.5 | Rs 16 | **+1,698** | +1,661 |
| 35% | 60% | 35 | 21 | Rs 32 | **+1,698** | +1,677 |
| 56% | 30% | 56 | 16.8 | Rs 25 | **+1,698** | +1,639 |
| 56% | 60% | 56 | 33.6 | Rs 50 | **+1,698** | +1,664 |

**Delivery does not move our margin** because WhatsApp is passed through at the same Rs 1.5. The worst case if the BSP bills on submission rather than delivery is a Rs 10 to 59 loss. What delivery moves is the value Sridhar gets (Section 2.3). The most the pass-through can reach inside the caps is 100 messages + 30 alerts = Rs 195 (Rs 230 with GST); expected Rs 8 to 50.

### 4.6 Starter pilot (the Rs 35,000 version)

Standard minus 8.3 hours of cuts (base), so that Rs 35,000 can be defended:

| Cut | Hours saved (base) |
|---|---|
| Calibrate on 3 builders, group resolution by hand for flagged ones only | 1.0 |
| Page and video: reuse the sample page and animatic, captions only, no new recordings, one hook | 1.0 |
| Hand-off: alert and reply log only, STOP rule kept, no routing rules | 2.0 |
| Read-only view as a daily static snapshot page (unlisted link, numbers masked) instead of a login | 2.0 |
| QA and test sends trimmed | 0.5 |
| Final report only (no mid-pilot note) | 1.0 |
| Lighter check-ins and upkeep | 0.75 |
| **Total** | **8.3** |

Starter: hours 22.5 / **34.7** / 54.1, cash Rs 847 / 2,846 / 7,930 (no voice licence). Cost at base hours: Rs 20,179 (Rs 500 an hour), **Rs 37,513 (Rs 1,000)**, Rs 54,847 (Rs 1,500).

| Price | Hour value | Low | **Base** | High |
|---|---|---|---|---|
| **Rs 35,000** | 500 | +22,884 | **+14,821** | +6 |
| | 1,000 | +11,615 | **-2,513** | -27,058 |
| | 1,500 | +345 | -19,847 | -54,122 |

Starter break-even hour value: Rs 35,000 gives **Rs 928** at base hours (Rs 1,515 low, Rs 500 high). Rs 38,000 would cover Rs 1,000 an hour (+Rs 487). OPINION: the Starter is fine if the owner values an hour at Rs 900 or less, and it is the honest way to say "Rs 35,000": a smaller product, not the same product for less.

### 4.7 Monthly run

Fixed monthly hours 7.55 (daily check 22 x 5 min = 1.8; four weekly notes 2.0; monthly call 0.75; upkeep 2.0; pool refresh and RERA pull about 1.0) plus review 4.5 min per builder. Fixed monthly cash Rs 1,840 (voice 540, hosting 500, number allocation 500, report model calls 300) plus AI per builder.

Cost per month (hour value Rs 1,000):

| Builders | Low | **Base** | High (9-min review, no cap) | Time-boxed worst case (6-min review cap, AI budget Rs 50 a builder) |
|---|---|---|---|---|
| 50 | 7,940 | **14,306** | 26,980 | n/a |
| 100 | 10,780 | **19,221** | 37,460 | 24,390 |
| 150 | 13,620 | **24,137** | 47,941 | 31,890 |

At Rs 500 an hour: 100 builders base Rs 11,696; 150 builders base Rs 14,737. At Rs 1,500: Rs 26,746 and Rs 33,537.

| Offer | Break-even hour value, base | Margin at Rs 1,000/h, base | Time-boxed worst case at Rs 1,000/h | High case at Rs 1,000/h |
|---|---|---|---|---|
| Rs 30,000, up to 100 builders | Rs 1,716 | +10,779 | **+5,610** | -7,460 |
| Rs 30,000, up to 150 builders | Rs 1,312 | +5,863 | **-1,890** | -17,941 |
| Rs 36,000, up to 150 builders | Rs 1,631 | +11,863 | **+4,110** | -11,941 |

**Answer for the owner's Rs 30,000 a month:** deliverable for **up to 100 builders**. For 150 builders it is only deliverable if review stays at 4.5 minutes; in the time-boxed worst case it loses Rs 1,890. So quote 150 builders at Rs 36,000. Each extra 50 builders cost about Rs 4,900 at base (Rs 2,800 low, Rs 10,500 high), so add **Rs 6,000 per extra 50**. From month 4 (the pool is mostly worked), 40 builders a month cost about Rs 13,300 at Rs 1,000 an hour: quote **about Rs 15,000**.

Monthly WhatsApp pass-through at 150 builders: Rs 20 to 200 (reach 35% to 56%, delivery 45% to 60%), cap Rs 500.

The earlier shared-risk idea (Rs 20,000 retainer plus Rs 4,000 per demo) is below cost for 150 builders at Rs 1,000 an hour; I have not re-priced it here.

Cross-check, research-only list (the earlier Rs 12,000 for 50 builders): first list including the pipeline build is 14.75 h and about Rs 1,350 cash, so break-even is **Rs 722 an hour**; a repeat list is 5.75 h and break-even is Rs 1,853 an hour. Fine as a follow-on, tight as a first sale.

### 4.8 Recommended "from" prices and clauses

| Offer | Recommended | In plain words |
|---|---|---|
| **Pilot Standard** (up to 50 builders, CG) | **from Rs 48,000 + GST** | covers base hours up to Rs 1,040 an hour |
| **Pilot Starter** | **from Rs 35,000 + GST** | only with the 7 cuts in 4.6 |
| **Monthly run** | **from Rs 30,000 + GST for up to 100 builders**; Rs 36,000 for 150; +Rs 6,000 per extra 50; about Rs 15,000 from month 4 | |
| WhatsApp | Rs 1.5 per delivered marketing message + GST at cost; pilot cap Rs 300; month cap Rs 500 | |
| Change rate | Rs 1,000 an hour | |

OPINION on which to send: send ONE number, the Standard "from Rs 48,000", unless the owner values an hour at Rs 900 or less, in which case send the Starter. Both say "indicative, can change when requirements arrive".

**Clauses [LIFTABLE]:**

- *Indicative:* "This is an indicative estimate. It can change once we have your written requirements. We confirm a fixed price in writing before any work starts, and nothing is charged before you approve it."
- *WhatsApp:* "WhatsApp: Rs 1.5 per delivered marketing message, billed at our provider's rate with no markup, plus GST. Estimated Rs 10 to 100 for the pilot; the most it can reach inside the caps is Rs 195; we do not bill more than Rs 300 without your approval. Any other third-party fee we cannot know today (for example a fee for an extra number or a licensed data source) is passed through at cost only with your prior approval."
- *Price change:* "This price assumes AI, messaging and platform prices as of 20 October 2026. If any of them rises so that our direct cost per builder or per message rises by more than 25%, we pass the actual increase through at cost after 30 days' written notice, and you may stop at that point without penalty. No other price change happens without your written approval."
- *Change requests:* "Anything outside the caps is quoted in hours before work starts (change rate Rs 1,000 per hour)."
- *Inputs:* "The clock starts when we have the items on your list of inputs. If they arrive late, the dates move by the same number of days."

**Short estimate text for Sridhar [LIFTABLE, wording for the other workstream to polish; signed IV Infotech]:**

> **Indicative estimate, Chhattisgarh builders pilot.** From Rs 48,000 + GST for up to 50 builders: research records with source links and an owner-confidence label, one master video and a personalised page, WhatsApp messages (up to 2 per builder, English, only to numbers the business published and only where a WhatsApp-capable number exists), every genuine reply forwarded to you, a read-only dashboard, and a final report on Day 17. WhatsApp is billed at Rs 1.5 per delivered message + GST (estimated Rs 10 to 100, capped at Rs 300). Not included: calls, email, CRM integration, Hindi or Gujarati, other states. We do not promise replies, demos or customers, and not every builder will have a number we can message. The price can change after we receive your requirements; we confirm it in writing first. - IV Infotech

---

## 5. (d) Driver table: requirement to effect on price

Effects use the **change rate of Rs 1,000 an hour**; every hour figure is an ASSUMPTION unless noted. Hours stay internal; Rs ranges and the "what it changes" line are what the owner can pass on. Low to high ranges.

| # | If Sridhar asks for | One-time effect | Monthly effect | Notes |
|---|---|---|---|---|
| D1 | **More builders** (each extra 50, CG) | none | **Rs 2,900 to 10,500** per +50 (2.1 to 7.5 h + AI Rs 760 to 2,980); base Rs 4,900 | The pool is the limit: 72 shortlisted, about 424 loose, about 4 new a month. Above about 150 the small/medium rule must be loosened (his decision) |
| D2 | **Per-builder video** | Rs 3,000 to 5,000 (3 to 5 h) | Rs 900 to 2,800 per 50 | 1.45 min render each (MEASURED), plus a person checking; 2 of 6 campaign-1 renders needed rework for a wrong name. Per-recipient video in a template header on this BSP: UNKNOWN. No evidence a name in the video lifts replies |
| D3 | **Hindi (or Gujarati) variant** | Rs 4,000 to 9,000 per language (4 to 7 h + up to Rs 2,000 native check) | Rs 250 to 1,000 | No native-speaker check exists yet. Sridhar records voice clips. Gujarati is not relevant to CG |
| D4 | **Another state's RERA fetcher** (only where allowed) | Rs 8,000 to 20,000 per state | Rs 1,000 to 3,000 | Includes robots and terms check. From our 20 Oct table: Odisha, Gujarat, Rajasthan readable; Telangana has an image CAPTCHA (we do not bypass); UP errors |
| D4b | **Madhya Pradesh** | not automated | Rs 250 to 670 per builder if hand-built (15 to 40 min each) | MP RERA robots.txt says Disallow all. Hand-built list or a permission request; neither promised |
| D5 | **Nexus360 CRM integration** | **quoted after we see his API** (free 1 to 2 hour review first) | after review | Internal planning bracket only, NOT a quote and not for Sridhar: file import 3 to 6 h, one-way push 8 to 20 h, two-way sync 30 h or more |
| D6 | **Email as a second channel** | Rs 5,000 to 9,000 (5 to 9 h) | Rs 1,000 to 4,300 (1 to 2.5 h + possible mail plan up to Rs 1,800, ASSUMPTION) | Needs a monitored reply path (9 of 12 campaign-1 emails had an unmonitored Reply-To). The cheapest way to raise reach: 4 of 6 tested builders had some business-published channel, but that count includes landlines |
| D7 | **Calls by us** | none | Rs 170 to 500 per builder (10 to 30 min for up to 3 tries), so Rs 8,300 to 25,000 per 50 | Telecom rules for B2B calls not established. We recommend his team calls the warm ones. WhatsApp voice notes cannot open a conversation (templates carry text, image, video or document headers: INFERENCE from general knowledge, not rechecked today) |
| D8 | **Faster start** | Rs 4,000 to 12,000 (about 25% of setup as overtime) | none | Cannot beat outside waits: Meta approval, +91 number availability (UNKNOWN), his own inputs |
| D9 | **More reports** (extra weekly report, extra call) | none | Rs 2,000 to 4,000 | Custom analysis 2 to 4 h each |
| D10 | **Licensed registry data source** | Rs 4,000 to 8,000 (4 to 8 h) + **licence fee UNKNOWN, passed through at cost** | saves about Rs 400 to 1,000 in manual lookups | We do not guess the fee. The free sites bar scraping, so today these are manual single lookups |
| D11 | **Separate +91 number and display name** | **inside the lean price** (row S3) | possible BSP fee Rs 0 to 1,500 (ASSUMPTION; UNKNOWN) | Not yet known: can our BSP give one, fee, Meta display-name approval, business-verification status (new portfolios capped at 250 unique recipients per 24 h) |
| D12 | **Forward-only reply routing** | basic version **inside the lean price** (S4); extras Rs 3,000 to 6,000 | Rs 500 to 1,545 | Extras = second recipient, working-hour rules, fallback alert by another channel. Each alert from our number is a marketing-category message at Rs 1.5 (as seen 19 Oct) |
| D13 | **Also message the mobile filed on the RERA page** | Rs 1,000 to 3,000 | Rs 800 to 2,000 | Lifts reach a lot (every tested builder had a filed mobile) but Sridhar himself says these are not the owners, and Meta opt-in risk is higher (error 131049 hit 2 of 7 in campaign 1). Owner and Sridhar must decide. Not legal advice |
| D14 | **Third or fourth follow-up** | Rs 500 to 1,000 | Rs 100 to 400 + Rs 1.5 per delivered message | More touches raise Meta block risk |
| D15 | **One more change round** | Rs 2,000 to 4,000 per round | none | One round is inside the price |
| D16 | **Custom dashboard views, more viewers** | Rs 3,000 to 8,000 | Rs 250 to 1,000 | Two viewers and standard views are inside the price |

**What raises the price most, in order (INFERENCE):** CRM integration (unknown, possibly the largest), another state (Rs 8,000 to 20,000 each), calls by us (Rs 8,000 to 25,000 per 50), email (Rs 5,000 to 9,000 once), per-builder video, then the rest. What raises the VALUE most is not a cost line: it is reach (D6 and D13).

---

## 6. (e) The promise boundary [LIFTABLE]

**We promise (once Sridhar's inputs arrive):**
- Research records for up to 50 Chhattisgarh builders from the public RERA register, each fact with a source link and date and a label VERIFIED / LIKELY / UNKNOWN for the owner or decision-maker. Where we cannot find one the record says UNKNOWN.
- A first WhatsApp message and at most one follow-up, in English, only to numbers the business itself published (own website, own ad or the register), only after a person on our side has checked the record, from our +91 line, with a STOP line.
- One master video and one personalised page per messaged builder, built from register fields.
- Every genuine reply forwarded to the person Sridhar names, with no AI answer to the owner. We stop messaging a builder at once after any reply or STOP.
- A read-only view of the pilot data (funnel counts, builder table with labels, send and reply log) and a CSV export.
- One mid-pilot note and one final report on Day 17, with the funnel, what we learned, and an updated estimate.

**We never promise:**
- Replies, demos, meetings, customers or any reply rate. Our own first campaign: 9 contacted, no confirmed genuine reply; 2 of 7 cold WhatsApp messages arrived on time.
- A direct WhatsApp number or verified personal contact for every owner. Tested on 6 builders: owner or decision-maker named for 4 (LIKELY or VERIFIED labels, n = 6), a number wired for WhatsApp for 1, a verified direct owner number for 0.
- That every builder can be messaged. Builders without a business-published WhatsApp-capable number are researched and handed over as records, not messaged.
- Delivery of every message. Meta decides.
- Madhya Pradesh automation (its RERA site disallows bots), other states, email, calls, Hindi or Gujarati, CRM integration. Each is a priced option, not included.
- A reply-rate verdict from 50 builders. Roughly 8 to 28 of them can be messaged and a few delivered; a verdict needs about 90 to 600 researched builders depending on reach.
- Anything about Nexus360's own sales results or savings.

[INTERNAL note] Wording rules for anything Sridhar sees: avoid the two banned words from the owner's brief, no price for Nexus360 itself, no builder names or numbers, signed IV Infotech, no staff names.

---

## 7. (f) Sensitivity: how many builders per month before we lose money

**At the monthly fee of Rs 30,000** (base AI, our fixed month Rs 1,840 + 7.55 h): number of builders at which the month turns to a loss, by hour value and review time:

| Case | Rs 500 an hour | Rs 1,000 an hour | Rs 1,500 an hour |
|---|---|---|---|
| Low (2.5 min review, AI Rs 15) | 755 | 438 | 292 |
| **Base (4.5 min review, AI Rs 23)** | **401** | **210** | **124** |
| High (9 min review, AI Rs 60) | 145 | 64 | 26 |

**At the pilot price per builder** (Rs 48,000 / 50 = Rs 960):
- Rs 960 per builder against a variable cost of Rs 100 (base, Rs 1,000 an hour): money is lost only if one builder takes more than **about 56 minutes** of staff time (Rs 1,000 an hour) or 112 minutes (Rs 500 an hour). The lean pipeline plans 4.5 minutes; fully manual research is 15 to 40 minutes (ASSUMPTION), so even a manual fallback does not lose money per builder at the pilot rate.
- The fixed monthly overhead (about Rs 9,400 at Rs 1,000 an hour) is covered from **11 builders a month** (6 at Rs 500 an hour).

**So the money is never the ceiling.** The ceiling is our review time (about 166 builders at 4.5 min on 20 hours; 53 at 9 min), the pool (Section 3.6) and Meta limits. That is why the monthly offer is capped at 100 builders with a time-box rather than priced per builder without limit.

---

## 8. Open items and decisions

**Confirm before sending any number (owner, 10 minutes):**
1. **Fortius (BSP):** (a) is Rs 1.5 charged per delivered or per submitted marketing message; (b) before or after GST; (c) any platform, per-number or template fee; (d) can we get a +91 number, how fast, what display name; (e) is our WABA on INR billing (Meta deadline 31 Dec 2026); (f) current quality rating and messaging tier.
2. **Anthropic:** claude.ai Settings > Billing > API credits: is the USD 100 credit visible, which plan are we on, then link a Console organisation with its own workspace and spend limit.
3. **Gate 0:** run the lean pipeline on the 6 hand-researched builders and read the token and cost figures from the API (1.5 h). Pass criteria in 3.4.

**Owner decisions:**
1. Value of an hour (decides Starter at Rs 35,000 versus Standard at Rs 48,000).
2. Whether to also message RERA-filed mobiles and/or add email (D13, D6). Without one of them only about 8 of 50 builders get a message.
3. Monthly: accept "up to 100 builders" for Rs 30,000.
4. Client work on pay-per-use API, not on the subscription (my recommendation: yes).
5. Whether to disclose "9 contacted, no confirmed genuine reply" (switch in the earlier `prices.json`).

**Risks not priced:** a Meta restriction on the shared WABA (campaign 1 already had 3 of 7 failures; the +91 line is meant to keep the sales agent and owner alerts safe); a +91 number that turns out unavailable (then the pilot cannot start as designed); the viewer login must show only this campaign (campaign 1 data must never be visible; test it by trying other URLs as the viewer); Hindi lines unchecked by a native speaker; owner names partly come from aggregator pages that bar scraping (manual single lookups only); India personal-data rules start about May 2027 (not legal advice).

**What is still UNKNOWN:** our BSP billing basis, GST treatment and +91 availability; our plan name and whether the API credit applies; the small model's quality on owner extraction; the real reachable share (n = 6); the real review minutes; the value of an hour; Sridhar's requirements and CRM API.

## 9. Sources

- Repo: `agent/state/side_leads/nexus360_demo/proposal/` (`unit_costs/unit_costs.md`, `cost_model.py`, `prices.json`, `employee/comparison.md`, `enrichment/enrichment.md`, `owner_notes.md`, `page_video/page_video_effort.json`), `proposal_lowprice/`, `cg_rera_demo.py`, `cg_rera_demo_summary.txt`; `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, `agent/docs/CAMPAIGN_LEARNINGS.md`, `agent/docs/research_subscription_24x7_2026-10-14.json`; `agent/memory.md`; `agent/state/side_leads/nexus360_sridhar_patnaik.md`; `agent/video/render_master.py`; `console/app.py` (one owner login today, so a scoped viewer login is new work).
- Web, read 20 Oct 2026: Claude API pricing https://platform.claude.com/docs/en/about-claude/pricing; Claude plans https://claude.com/pricing; API credits for Max and Team https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers and https://support.claude.com/en/articles/17154008-api-credits-for-max-and-team-plans; credit terms https://www.anthropic.com/legal/credit-terms; Meta WhatsApp pricing https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing.md; USD/INR https://pluang.com/en/tools/currency-converter/usd-inr (22 Jul 2026 datapoint, the latest found).
- Files in this folder: `estimate_model.py` (rerun to refresh), `estimate_model.json` (all numbers, driver table, caps, clauses, promise boundary).
