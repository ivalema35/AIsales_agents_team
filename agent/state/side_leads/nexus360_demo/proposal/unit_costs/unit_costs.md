# Unit costs and price options: Chhattisgarh builders engine (Nexus360 side lead)

Prepared Tue 20 Oct 2026 for the owner of IV Infotech. INTERNAL: cost lines and margin are not for Sridhar. The owner decides every final price. All prices are INR before 18% GST on our invoice. The arithmetic is in `cost_model.py` (same folder; change an input, rerun).

Tags: **FACT** = sourced (URL or repo file). **ASSUMPTION** = my estimate, with a range. **INFERENCE / OPINION** = reasoning from the above.

## 1. Headline

| | Low (walk-away) | **Recommended** | High (do not exceed) | Pass-through (estimate, at cost) |
|---|---|---|---|---|
| **A. 2-week pilot, 50 builders, fixed fee** | Rs 32,000 | **Rs 75,000** | Rs 1,10,000 | Rs 30 to 310 (cap Rs 500) |
| **B. Monthly managed run, 150 builders** | Rs 24,000 | **Rs 45,000 / month** | Rs 60,000 | Rs 90 to 930 (cap Rs 1,500) |
| **C. Research-only list (no messaging)** | 50: Rs 9,000 / 150: Rs 19,000 | **50: Rs 18,500 / 150: Rs 35,000** | 50: Rs 25,500 / 150: Rs 45,000 | none |

- Marginal cost of working one more builder (research, QA, review, WhatsApp): about **Rs 150** (cash Rs 76 + human Rs 75 + WhatsApp Rs 1.7), range about Rs 45 to 510. ASSUMPTION-based.
- AI tokens are about 3% of the pilot price and 16% of the monthly price. **Meta's WhatsApp fees are under 1% of either at base (up to about 2% of the monthly price in the worst case).** The price is mostly setup time, oversight time and margin. FACT-based arithmetic, ASSUMPTION hours.
- **The pilot cannot pay for itself in customers.** At assumed rates it yields about 0.06 paying customers (range 0 to 0.2). It is bought for information plus a reusable owner list. Option B breaks even only at about a 3.3% genuine-reply rate; our own campaign is 0 of 9, so there is no evidence either way. Sell A first; sign B only after a go/no-go (section 7).
- Unknown today: what our BSP charges (platform fee, per-message markup), our WhatsApp quality rating, and the real owner-contact hit rate in Chhattisgarh.

## 2. WhatsApp (Meta + our BSP)

| Item | Value | Tag, source |
|---|---|---|
| Billing model | Per delivered message since 1 Jul 2025 (replaced conversation pricing). Failed or undelivered messages are not charged. | FACT. Meta: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing.md (read 20 Oct 2026) |
| India marketing template | **Rs 0.8631** per delivered message (was Rs 0.7846; raised 1 Jan 2026). No volume tiers for marketing. | FACT, secondary: Free Press Journal citing Meta's India card, updated 30 Sep 2026 (https://www.freepressjournal.in/tech/how-much-does-india-have-to-pay-for-whatsapp-messages-from-october-1); Monty Mobile 28 Sep 2026. Meta's page confirms "higher India marketing rate" on 1 Jan 2026 but its text shows no INR figure; I could not open Meta's INR CSV. |
| India utility / authentication | **Rs 0.115** per delivered message | FACT, same secondary sources |
| Service (free-form reply inside the 24 h window) | First 1,000 per number per month free, then Rs 0.115, from 1 Oct 2026 | FACT. Meta page (above) and Free Press Journal |
| GST | +18% on Meta and BSP charges, so marketing is about Rs 1.02 | FACT per vendors (Monty Mobile, ChatMaxima), not stated on Meta's page |
| Rate-change rule | Meta changes prices only on 1 Jan, 1 Apr, 1 Jul, 1 Oct, with 1 month notice | FACT. Meta page |
| BSP-billed examples | Gallabox list Rs 0.9926 marketing / Rs 0.1323 utility (exactly Meta x 1.15). AiSensy blog: Rs 1.09 / Rs 0.145. | FACT, vendor pages: https://docs.gallabox.com/pricing-and-billing/whatsapp-pricing/rate-card.md ; http://m.aisensy.com/blog/whatsapp-per-message-pricing-update-effective-january-1-2026/ |
| **Our BSP (waba.fortius.in.net)** | Plan fee, per-message markup, INR rate card: **UNKNOWN**. Nothing recorded in the repo or memory except that we hold pre-paid credits there. | FACT of absence: tracker.md Step 3.4; `reference_sales_whatsapp_bsp.md`. Action: read the live INR rate card in the Fortius dashboard. |
| INR deadline | WABAs must be on INR billing by 31 Dec 2026; Meta stops delivering from non-INR accounts of eligible customers from 1 Jan 2027. Ask Fortius whether our WABA is INR. | FACT. Meta page. (Monty Mobile says an existing USD WABA cannot be switched in place: vendor claim, unverified.) |

All-in per delivered marketing message, with GST: **Rs 1.02** (Meta list), **Rs 1.17** (Gallabox-like), **Rs 1.29** (AiSensy-like). I use Rs 1.02 / 1.17 / 1.29 as low / base / high.

Volume arithmetic (ASSUMPTIONS: 1.0 / 1.3 / 1.6 numbers per builder, 2 / 2 / 3 template touches, 30% / 55% / 100% delivered. Delivery anchor: campaign 1 sent 7 cold templates, 2 arrived on time, 1 about 4 h late, 3 failed, 1 silent for 3 days; FACT, `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`):
- Pilot: 50 x 1.3 x 2 = 130 sent; x 55% = 71.5 delivered; x Rs 1.171 = **Rs 84** (low Rs 31, high 50 x 1.6 x 3 = 240 x 100% x 1.286 = Rs 309).
- Monthly: 150 x 1.3 x 2 = 390 sent; x 55% x 1.171 = **Rs 251** (low Rs 92, high Rs 926).
- Hand-off alerts to Sridhar: about 10 to 30 a month. Our existing alert template was categorised MARKETING by Meta (FACT, agent memory 19 Oct), so about Rs 1.02 each, under Rs 40 a month. Free-form alerts inside his 24 h window fall under the 1,000 free.
- New Meta portfolios are capped at 250 unique recipients per 24 h until business verification (FACT, our research 14 Oct; our verification status is unknown). Not binding at 50 to 150 a month.

## 3. AI and data cost per researched builder

**Observed token use (FACT, `agent/memory.md`):**

| Run | Tokens | Agents | Candidates | Qualified | Per candidate | Per qualified lead | Per agent |
|---|---|---|---|---|---|---|---|
| Round 1 research, 15 Oct | 2.2M | 14 | 17 | 10 | 129k | 220k | 157k |
| Round 2 research, 19 Oct | 4.1M | 26 | 34 | 12 | 121k | 342k | 158k |
| Campaign diagnosis, 20 Oct (analysis, not research) | 3.3M | 14 | n/a | n/a | n/a | n/a | 236k |

Model for a Chhattisgarh builder (ASSUMPTION): **200k / 300k / 500k tokens** per builder. The register already gives the candidate list (no scouting waste), but finding the real owner is deeper than our Gujarat qualification, and drafting and QA add tokens.

**Price per token (FACT, https://platform.claude.com/docs/en/about-claude/pricing, read 20 Oct 2026), USD per million tokens:** Sonnet 5.5 input 2, output 10, cache read 0.10, 5-minute cache write 2.50. Opus 5.5 input 4, output 20. Haiku 5.5 0.10 / 0.50. Web search $10 per 1,000 searches. Batch API is 50% off.

What I do not know: the model mix of those runs (the agent files set none, so they inherit the session model) and the cache-read share of the reported token figure. So I use a blended **$0.50 / $1.50 / $3.50 per MTok** for Sonnet 5.5 (cache-heavy mix 90% reads + 5% cache writes + 3% input + 2% output is about $0.48; fresh-heavy 85% input + 15% output is about $3.20). Opus 5.5 would be double.

| Per builder | Low | Base | High |
|---|---|---|---|
| LLM (tokens x blend) | 200k x $0.50 = $0.10 | 300k x $1.50 = $0.45 | 500k x $3.50 = $1.75 |
| Web search if run on the API (10 / 15 / 40 searches x $0.01) | $0.10 | $0.15 | $0.40 |
| Data tools (Apify, Ad Library scraper, registry lookups) | $0.03 | $0.10 | $0.30 |
| Total USD | $0.23 | $0.70 | $2.45 |
| INR at Rs 88 / 90 / 95 per USD | Rs 20 | **Rs 63** | Rs 233 |
| With 20% re-run contingency | Rs 24 | **Rs 76** | Rs 279 |

- Opus 5.5 for everything at the high setting: $4.20 = Rs 399 per builder.
- Cross-check (INFERENCE): our own blueprint estimated about $0.49 LLM per fully worked lead (`agent/docs/AGENTIC_SALES_BLUEPRINT.md`, an estimate, not a measurement). Base here is $0.45. Apify about $0.05 per surviving lead there; $0.10 here.
- FX: Rs 90 per USD is an ASSUMPTION. The last datapoint I found is Rs 88.70 on 30 Oct 2025 (newsonair.gov.in); I found no October 2026 quote.
- **Subscription caveat (FACT + INFERENCE):** our research runs so far ran on a Claude subscription login, so our out-of-pocket AI cost was a flat plan fee. The table above is the API list-price equivalent. Our own note (14 Oct) found no source that permits an unattended paid service on a personal subscription. I price on the API basis so the number holds either way.

## 4. Video, page, hosting

- Master video about 36 to 38 s; each builder's copy is the same video with personalised on-screen slots (builder, project, city), one shared narrator MP3. FACT, `agent/memory.md`, `agent/video/render_master.py`.
- **About 5 min local render per video** (FACT, given). 50 videos = 4.2 machine-hours; 150 = 12.5 machine-hours a month on one PC. Unattended; electricity is negligible (ASSUMPTION under Rs 2 each). One PC is enough up to about 150 a month.
- Voice: the narration is a one-off recording. Free ElevenLabs audio is not licensed for commercial use (FACT, our notes); the Starter plan includes a commercial licence at **$6 per month** (Rs 540); Creator $11 (FACT, https://elevenlabs.io/pricing, read 20 Oct 2026). No per-builder TTS cost.
- Optional bespoke illustrated video per builder (kie.ai): about 250 credits = **$1.25 = Rs 113** each (FACT: our run; 1 credit = $0.005 per kie.ai). Not in any price below; offer only for a few top builders.
- Page and video files live on our existing VPS under ivinfotech.com/campaign/. Files are 2 to 12 MB (FACT: 2.3 MB and 11.6 MB versions), so 150 videos is at most about 1.8 GB. Marginal cost about zero; I allocate Rs 500 a month (ASSUMPTION).
- A separate +91 WhatsApp number, display name and domain: ASSUMPTION Rs 0 / 1,000 / 3,000 one-time plus any BSP fee for a second number (unknown, ask Fortius). The diagnosis says a +1 US-looking sender is wrong for Indian builders.

## 5. Human time (the main cost)

Hourly value is an owner decision. I use **Rs 500 / 1,000 / 1,500 per hour** (ASSUMPTION; the repo records no internal rate).

**One-time setup for the client (pilot), hours low / base / high (ASSUMPTION):**

| Task | Low | Base | High |
|---|---|---|---|
| Adapt the Chhattisgarh register fetch (script exists) and enrichment to "find the real owner" | 3 | 5 | 6 |
| Builder-facing master video (script, voice, scenes) and page template | 10 | 15 | 20 |
| +91 number, display name, 2 to 3 templates, Meta approval | 3 | 4 | 5 |
| Forward-only hand-off: reply goes to Sridhar at once; the AI never answers owners; kept apart from our own sales agent | 4 | 6 | 8 |
| Read-only client dashboard view on the Agent Console | 6 | 8 | 12 |
| Claims and copy QA, test sends to our own phones | 3 | 3 | 5 |
| **Total** | **29** | **41** | **56** |

**Running hours (ASSUMPTION):** per builder 3 min dossier QA (identity and owner-source check) + 1.5 min message and video review; daily check of replies and health 10 min; client sync 45 min; upkeep (templates, Meta quality, fixes).

| | Low | Base | High |
|---|---|---|---|
| Pilot, 2 weeks, 50 builders: 50 x 4.5 min = 3.75 h + 10 x 10 min = 1.7 h + 2 syncs and final report 4.5 h + upkeep 1 h | 6.4 h | **10.9 h** | 19.8 h |
| Month, 150 builders: 150 x 4.5 min = 11.25 h + 22 x 10 min = 3.7 h + 4 syncs = 3 h + upkeep 3 h | 11.1 h | **20.9 h** | 39.8 h |
| Research-only list: setup 6 h + 150 x 3 min = 7.5 h + delivery 2 h (50 builders: 2.5 h) | 8.8 h (150) | **15.5 h** (150) / 10.5 h (50) | 27 h (150) |

## 6. The three options (cost-plus arithmetic)

Method: `floor` = base cash + base hours x Rs 500, no margin (walk-away). `Recommended` = (base cash + base hours x Rs 1,000) x 1.30 margin. `High` = (base cash + base hours x Rs 1,500) x 1.30. Margin of 30% is an ASSUMPTION.

### A. Two-week pilot, 50 builders, fixed fee

- **Cash (base):** research 50 x Rs 76 = Rs 3,780; voice Rs 540; report and dashboard LLM Rs 180; number and domain Rs 1,000; hosting Rs 500 = **Rs 6,000**. WhatsApp is passed through, not in the price.
- **Hours (base):** 41 setup + 10.9 running = 51.9 h x Rs 1,000 = Rs 51,900. Cost = **Rs 57,900**; x 1.30 = Rs 75,300, so **Rs 75,000**.
- **Band:** low Rs 32,000 (Rs 6,000 + 51.9 h x Rs 500); high Rs 1,09,000, so **Rs 1,10,000** (51.9 h at Rs 1,500). The high also equals about 2 years of one small customer's subscription (section 7).
- Unit view: Rs 1,500 per builder worked; about Rs 6,100 per owner-level reachable builder if 12 of 50 are reachable (ASSUMPTION: 55% get a named owner x 45% of those with a usable number; range 6 to 21).
- **Included:** dossiers for 50 Chhattisgarh builders from the public RERA register (real owner or decision-maker named where findable, each fact with its source link, best contact route); one builder-facing video and page with per-builder personalisation; WhatsApp messages from our number (up to 2 touches, then stop); every genuine reply forwarded to Sridhar at once, the AI never talks to owners; live dashboard link; final report with the funnel (researched, owner named, number found, delivered, read, page opened, replied, handed off).
- **Not included:** any guarantee of replies, demos or customers; email, calls or ads; Madhya Pradesh (its RERA robots.txt disallows bots); replies handled by us; CRM integration beyond a read-only view of our own data; bespoke kie.ai videos; GST; Meta/BSP charges beyond the cap. Sridhar supplies product facts, a demo link, a named person and number for hand-offs, and his customer list for exclusion.
- **WhatsApp pass-through:** delivered-message charges at our BSP's billed rate plus GST, no markup by us; estimate Rs 30 to 310, cap Rs 500 unless he approves more.

### B. Monthly managed run, 150 builders

- **Cash (base):** research 150 x Rs 76 = Rs 11,340; voice refresh Rs 540; report LLM Rs 450; number and BSP allocation Rs 1,000; hosting Rs 500 = **Rs 13,830**.
- **Hours (base):** 20.9 h x Rs 1,000 = Rs 20,900. Cost = **Rs 34,700**; x 1.30 = Rs 45,200, so **Rs 45,000 per month**.
- **Band:** low Rs 24,000; high Rs 59,000, so **Rs 60,000** (only if the pilot shows a reply rate of about 4% or more).
- Unit view: Rs 300 per builder worked; about Rs 1,200 per owner-level reachable builder (37 of 150 at base).
- **Optional structure B2 (OPINION):** retainer Rs 30,000 + Rs 3,000 per demo held with an owner-level contact (at least 15 minutes, confirmed by Sridhar). Total Rs 30,000 at 0 demos and Rs 39,000 at 3 demos; it shares the risk, which suits a first-time client. Needs a clear demo definition to avoid low-quality bookings.
- **Included:** everything in A for 150 new builders a month, weekly report, dashboard, template upkeep, monthly review call. If no pilot was bought, month 1 adds a one-time setup of about Rs 53,000 (41 h x Rs 1,000 x 1.30).
- **Not included:** as A. **Pool limit (INFERENCE from the saved register `cg_rera_public_list.csv`, my recount):** promoters with 3 or fewer registered projects and a valid registration, housing only, government removed: 74 approved in the last 18 months in Raipur, Durg, Rajnandgaon; 424 in those districts with no date limit; across all of Chhattisgarh 157 (last 18 months) and 798 (no date limit). At 150 a month that is about 2.8 months of runway for the three districts, about 5.3 for the state, before any repeat touch. Before Sridhar's own customers are removed. "Small/medium" is a stand-in rule, not a register field.
- **WhatsApp pass-through:** estimate Rs 90 to 930 a month, cap Rs 1,500.

### C. Research-only list (no messaging)

| | 50 builders | 150 builders |
|---|---|---|
| Cash (research x Rs 76) | Rs 3,780 | Rs 11,340 |
| Hours (base) | 10.5 | 15.5 |
| Cost at Rs 1,000/h | Rs 14,280 | Rs 26,840 |
| **Recommended (x 1.30)** | **Rs 18,500** (Rs 370 per builder) | **Rs 35,000** (Rs 233 per builder) |
| Low / high | Rs 9,000 / Rs 25,500 | Rs 19,000 / Rs 45,000 |

- **Included:** one row per builder: company, promoter as registered, real owner or decision-maker where findable, the source link for each fact, best contact route and how it was published, fit notes, confidence; CSV plus dashboard view; one correction round in 14 days.
- **Not included:** video, page, any message sent, hand-off handling, a guarantee that every builder has a reachable owner (unreachable ones are marked as such).
- The first list carries a one-time 6 h setup; a repeat list is about Rs 7,800 cheaper (6 h x Rs 1,000 x 1.30).
- Compare: manual research of one builder is roughly 30 to 45 min (ASSUMPTION), so a 50-builder list is about 25 to 38 hours of an employee's time. The salary side is in the hiring-comparison workstream, not here.
- Owners' mobile numbers are personal data. We deliver only business-published contacts with a source URL; the India data-protection law's core duties start about May 2027 (our blueprint, not legal advice).

## 7. Value-based sanity check

**Public SaaS price anchors (the price of Nexus360 itself is NOT published: nexus360.in says "Ask for pricing", checked 20 Oct 2026, so none is assumed):**
- Makanify Builder plan: Rs 1,000 per user per month, billed annually; WhatsApp credits extra (FACT, ItechGuides review, facts checked 22 Sep 2026, https://www.itechguides.com/products/makanify/).
- Sell.do blog: "roughly Rs 700 to Rs 3,000+ per user per month"; example 20 users at Rs 1,200 is Rs 2.88 lakh a year (vendor content, updated 17 Aug 2026, https://www.sell.do/blog/real-estate-crm-pricing-india-2026).
- SiteSetu: Rs 2,500 (small) and Rs 5,000 (mid) per active project per month (FACT, third-party listings only, not verified at the vendor).
- Zoho CRM tiers Rs 720 / 1,200 / 2,100 per user per month (weak: undated listicle).

**INFERENCE:** a small builder with 4 to 5 users at a Makanify-like price pays about Rs 48,000 to 60,000 a year. I model **Rs 40,000 / 50,000 / 60,000 per customer per year**, 3-year life (ASSUMPTION) = **Rs 1.2 / 1.5 / 1.8 lakh** lifetime revenue. Real ARPA could be higher (several users, several projects); if it doubles, every break-even rate below halves.

**Funnel (ASSUMPTION, no sourced benchmark for builders):** genuine owner reply per builder messaged 0% / 2% / 5% (our own: 0 of 9; vendor blogs claim 1 to 3% for autonomous cold outreach, but they sell competing products); reply to demo held 40%; demo to paying 10% / 15% / 20%.

| | Low | Base | High |
|---|---|---|---|
| Pilot, 50: genuine replies / demos / paying customers | 0 / 0 / 0 | 1 / 0.4 / 0.06 | 2.5 / 1 / 0.2 |
| Expected 3-year revenue from the pilot (at Rs 1.5 lakh) | Rs 0 | Rs 9,000 | Rs 30,000 |
| Month, 150: replies / demos / customers | 0 / 0 / 0 | 3 / 1.2 / 0.18 | 7.5 / 3 / 0.6 |
| Expected 3-year revenue per month of B | Rs 0 | Rs 27,000 | Rs 90,000 |

- **Pilot at Rs 75,000** needs 0.5 customers to repay, i.e. a 16.7% genuine-reply rate. Not realistic. It is an information purchase (OPINION): does an owner-level contact exist, is it reachable on WhatsApp, does anyone reply? Value ceiling about Rs 1.1 lakh, which is why that is the high end.
- **Monthly at Rs 45,000** breaks even at about 3.3% genuine replies (0.3 customers a month). Base 2% loses about Rs 18,000 a month in expected value; 5% gains about Rs 45,000. So B is a bet on a reply rate we have never measured (OPINION).
- **Suggested go/no-go gates for B, set before the pilot (OPINION):** at least 40% of builders with a named owner; at least 60% of sent messages delivered; at least 2 genuine replies from owner-level contacts; no Meta quality warning. If the pilot has 0 genuine replies, offer C or stop.

## 8. Risks and unknowns (not priced)

1. **Meta opt-in (FACT, our research 14 Oct):** a marketing template to a number scraped from a website is not valid opt-in as written; enforcement is reactive (blocks, then a 5/7/30-day send block, then lock). The WABA is ours, not Sridhar's, so IV carries the risk. Campaign 1 already shows 3 of 7 failures. OPINION: use a separate +91 number so the demo line, the sales agent and owner alerts are not hit. No cost line covers a restriction.
2. **Delivery is not guaranteed:** 2 of 7 on time in campaign 1. The price is independent of delivery; the pass-through falls when fewer messages arrive.
3. **Owner-contact yield is unknown.** Observed: an owner or decision-maker was named for 6 of 9 contacted Gujarat leads (FACT, diagnosis); that is a name, not a phone number.
4. **Human hours drive the price.** At Rs 500 / 1,000 / 1,500 per hour the pilot is Rs 41,500 / 75,300 / 1,09,000 and the month Rs 31,600 / 45,200 / 58,800 (same cash, base hours, 30% margin). The monthly run assumes 21 h; hours should fall once the batches settle.
5. **Run-rate caps:** one local PC for rendering; owner review is the bottleneck above about 150 builders a month.
6. **INR WABA migration by 31 Dec 2026** may need a new WABA; confirm with Fortius before any January 2027 run.
7. **Policy:** `agent/kb/pricing_policy.md` stops our AI from quoting prices anywhere; this estimate is a written proposal the owner approves and sends himself, never an agent reply.

## 9. Decisions for the owner

1. Hourly value and margin (I used Rs 1,000 and 30%).
2. Which option to lead with (my view, OPINION: A first, then B gated on the pilot; offer C as a fallback).
3. Whether to use B2 (retainer plus per-demo fee).
4. Whether to credit part of the pilot fee against month 1 if Sridhar continues.
5. Read the Fortius INR rate card and any per-message markup or platform fee, then replace the BSP lines.
6. Separate +91 number and its cost.
7. API-priced AI versus subscription for a paid client service.

## 10. What can go to Sridhar

Prices, inclusions, exclusions, the pass-through rule and cap, and the pilot gates. Do not send the internal cost, margin, hour rates, funnel assumptions or this file. Do not describe the funnel numbers as expected results, and do not promise replies, demos or customers.

Also used: Monty Mobile (https://montymobile.com/blogs/whatsapp-business-api-pricing-in-india-inr-rates-gst-and-the-2026-currency-migration-deadline), kie.ai (https://kie.ai/pricing), nexus360.in. Repo: `agent/memory.md`, `agent/docs/CAMPAIGN1_DIAGNOSIS_2026-10-20.md`, `agent/docs/AGENTIC_SALES_BLUEPRINT.md`, `agent/docs/research_raw_2026-10-14.json`, `agent/state/side_leads/nexus360_demo/*`, `tracker.md`, memory note `reference_sales_whatsapp_bsp.md`.
