# CAMPAIGN LEARNINGS (campaign 1, written 2026-10-19)

For: the next AI operator (no memory of this session) and the owner.
Data cut-off: 19 Oct 2026, about 14:40 IST. The wave-2 WhatsApp round (15:30 IST) had not run yet. Update section 2 when its result is known.
Campaign 1 = IV Infotech's AI sales operator selling WhatsApp automation (auto-reply to ad enquiries) to Gujarat real-estate developers.
Sources: five analyst reviews (lead research; outreach and monitoring; content and claims; process and owner; strategy and metrics). No contact details are in this file.

Tags: [generic] = holds for any vertical. [real-estate] = Gujarat real-estate only, rebuild per vertical.

Words used:
- Wave 1 = Pride, Brij, NB, Elenza, Rivanta (16-19 Oct). Wave 2 = Great Spaces, Swagat, Parshwanath, Space Age (19 Oct).
- Round 1 / round 2 = the two research rounds (15 Oct with Apify credit; 19 Oct with free sources).
- Hunger score (0-10) and Hungry / Warm / Cold = "pays for enquiries and is reachable". It is NOT proven need.
- OK code = single-use approval the owner sends from his own WhatsApp before any real send. Chat words are not approval.
- Console = the Agent Console (lead cards, engagement). Ad Library = Meta Ad Library. GujRERA = the Gujarat RERA public register and API.

---

## 1. Executive summary

1. We proved the machine, not the message. A 4-lead wave now goes from the owner's "go" to ready-to-send in about 56 min of agent time (wave 1 took about 23 h). The approval gate was never bypassed and no longer blocks real work.
2. Results so far: 22 leads researched, 9 contacted, 15 real sends, 0 replies, 0 button taps, 0 demos. Two page opens look human (Brij, Pride) but neither is attributed; they may be our own team.
3. 0 of 9 only rules out a true reply rate above about 28-34%. It does not show the approach fails. Nothing about subject, send time, language, grade or channel order can be concluded. A/B tests need 30-140 leads per arm; one research round gives 10-12.
4. "Zero replies" is not even measured for email. Replies go to a shared mailbox that neither the agent nor any automation reads, and 12 of 15 sends were email.
5. Email delivers (11 of 12). Cold WhatsApp MARKETING templates to business-published numbers did not (0 of 3), as the 14 Oct research predicted. Wave 2 repeats the bet at the owner's choice; result pending.
6. Lead quality came from the adversarial skeptic, the independent fact-check and cheap deterministic checks (MX, site fingerprint, send-day ad recheck), not from more scouts. 75% of first-pass A grades were lowered.
7. Grade and hunger score measure "pays for enquiries and is reachable", not "needs us". Need was never observed. All 9 contacted leads scored 7-8, so the score cannot be calibrated yet.
8. Our errors come in classes: unverified claims about the lead's ads, defaults shipped as fact ("free", "your ads"), a pitch that sold "a video", unread inbound mail, and false engagement signals (6 of 8 early signals were scanners or our own team).
9. The lever never tried at scale is a human voice (a named person calls or WhatsApps). We spent about 0.9M sub-agent tokens and about 2 approval codes per contacted lead for zero conversations.
10. NOT yet shown: that need exists; that email beats WhatsApp or the reverse; that the hunger score predicts anything; that heavy per-lead assets beat a light note; that any send time or language matters; that real estate is the right vertical. Next step is about 10 human conversations and a light-vs-heavy comparison with pre-registered rules, before campaigns 2-4.

---

## 2. Numbers worth remembering

**Funnel (to 19 Oct 14:40 IST)**
- 22 leads researched (10 + 12). 9 contacted (41%): 5 wave 1, 4 wave 2. 13 not contacted (5 from round 1, 8 from round 2).
- 15 real lead sends = 12 emails + 3 cold WhatsApp templates. Emails: 11 of 12 delivered; first touch 8 of 9 delivered; 1 hard bounce (Elenza's published sales address, 61 s after send).
- Cold WhatsApp: 0 of 3 delivered. Brij code 131049 five seconds after send; NB 131026 (number cannot receive); Elenza no status for 16+ h. Four more templates queued for 15:30 IST 19 Oct, result unknown.
- Replies 0, STOP 0, complaints 0, real CTA taps 0, real demo starts 0. Page opens that look human: 2 (Brij 17 Oct 09:02 IST; Pride 19 Oct 09:10 IST plus a video play). Not attributable.
- 6 of 8 engagement signals seen in 4 days were false (owner test click, boss test, mail auto-open +20 s and +30 s, scanner +6 s, team demo test).
- Old rule-based CRM baseline: 299 leads, 100 outreached, 4 engaged, 1 hot.

**Statistics**
- 0/9: 95% upper bound ~34% (28% one-sided). 0/21: 13%. 0/30: 9.5%. P(0/9) is 63% if the true rate is 5%, 39% at 10%, 8% at 25%.
- Leads per arm for 80% power: 5% vs 15% = 140; 5% vs 30% = 36; 10% vs 40% = 32; 20% vs 50% = 39.

**Research**
- Round 1 (15 Oct, Apify): 14 agents, ~34 min, ~2.2M tokens, ~US$2.85 (estimate), 10 leads, 0 A / 10 B, hunger 5 Hungry / 4 Warm / 1 Cold.
- Round 2 (19 Oct, free): 26 agents, 63 min, ~4.1M tokens, 34 candidates, 12 qualified (22 never qualified), 2 A / 9 B / 1 C, hunger 9 Hungry / 3 Warm. 8 first-pass A; skeptic lowered 6.
- Tokens per qualified lead: ~220K (round 1) vs ~342K (round 2).
- Apify: ~US$0.00075 per ad row, ~US$0.012 per Facebook page, ~US$0.004 per Maps place. All rounds 9-15 Oct ~US$7.2 (estimates; the connector returns no real cost). Monthly hard limit hit 15 Oct; still blocked 19 Oct.
- Freshness: 4 of 11 pool names could not be found again after 5 days. The 30-second send-day recheck kept 4 of 4.
- Contacts: round 1, 6 of 10 had a business email; round 2, 10 of 12. All 22 qualifiers wrote "email first"; 19 warned against a cold template. Every email used is a role inbox. GujRERA: 7 of 159 fresh promoters have a business email (~150 are Gmail). Of ~150 Gujarat real-estate advertisers only ~20 own a website.

**Content and QA**
- Five QA runs: 142 findings, 55 major/high (page v1 43/21; r2 pass 1 30/13; pass 2 23/11; video v1 24/5; v2 22/5). Each pass ~7 min and ~0.5M tokens.
- Pre-build fact-check: 4 agents, 9.3 min, ~0.5M tokens, 32 problems; 4 of 4 draft hooks needed correction.
- Email mix of 12: 6 video-first v1, 2 offer-first v2f, 4 v3 (wave 2).

**Time and cost**
- Wave 2: go 12:03 -> ready 12:59 (56 min). Research 10:52-11:55; fact-check 12:08-12:17; 4 renders 12:20-12:26 (~1.5 min each, not 5); QA 6.4 + 7.2 min; ad recheck 0.5 min; deploy 12:57. Owner OKs 14:07 (68 min after proposals). Emails 14:07-14:09.
- Wave 1: research done 15 Oct 17:49 to last send 16 Oct 16:35, about 23 h.
- All 17 campaign workflows 15-19 Oct: 218 min, 14.55M tokens = research 6.30M (43%), tooling reviews 4.39M (30%), QA/fact-check/preflight 3.42M (24%), script 0.44M. Lead-facing work ~7.8M = ~0.9M per contacted lead.
- Meta template approval: 16-20 min. Owner voice take: ~35 min each; 4 MP3s made 9-16 Oct.
- Weekly Claude limit: 94-95% used 15-16 Oct (hard cut 15 Oct 12:13 IST). Current percent unknown.

**Approvals and ops**
- 28 proposals; 20 consumed; 4 wasted (wording changed, provider failure, expired unsent); 4 approved but held. Median proposal-to-send 10.2 min. 19 real-lead codes for 9 leads (2.1 per lead). Codes live 12 h.
- 16 Oct: 23 min of friction because chat "send" is not an approval. 52 owner WhatsApp pings on 15-16 Oct caused owner-quiet mode.
- VPS reboot 17 Oct 11:14-11:37 IST (found by the owner). Heartbeat log gap ~39 h. Main-chat classifier denials: 11 (7 on 15-16 Oct, 1 on 19 Oct, 0 during wave 2).
- Owner sent 123 messages 15-19 Oct, median 66 characters.

---

## 3. Lessons by stage

Format: Rule / Why / (evidence). IDs are used by the checklists.

### 3.1 Research

**R1 [generic]** Rule: call it a pay-signal score. Compute it in code from separate sub-scores (pay observed / fit / reachability / resistance), each with url + date. Write the predicted tier into the lead BEFORE the send. Put 1-2 Warm leads in every wave as controls. Call every tier "unvalidated" until replies exist.
Why: need was inferred, never observed; wave 1 sent only Hungry 7-8, so tiers cannot be compared. (Round 1 had no rubric and was hand-scored afterwards; Nitya with zero paid ads scored 6; SuperCITY scored 8 but is grade B.)

**R2 [generic]** Rule: the skeptic is mandatory and uses a different method (live Ad Library, raw HTML via curl, not a model-summarised page). Run it on every A and every score >= 7, then re-score hunger. Cap a grade at B without two dated observations, a verified identity and a working contact route.
Why: round 2 skeptic kept 2 of 8 first-pass A. The 5 real-estate A rows of the 14 Oct Apify CSV came back B, B, not qualified, B, B on live recheck. (Scout claims failed on re-read: NB "no contact on homepage" was truncated WebFetch text; Beverlynn "no website" was wrong; Swagat Group Ahmedabad was confused with Swagat Developers Surat.)

**R3 [generic]** Rule: live Meta Ad Library cards are the best pay signal. Pull the list in bulk (Apify, `cta_type == WHATSAPP_MESSAGE`, ~1,500 rows for ~US$1) and use the browser only to verify the top advertiser pages. Take counts only from the advertiser page.
Why: the browser gives ~30 cards per query (~150 advertisers seen, ~20 with a website). Bulk actors under-count (Swarna 1 vs 13, 1 Clik 9 vs 20) and cap "total" (identical 175 for two leads).

**R4 [real-estate]** Rule: second list = GujRERA filtered by approval-date window and business-domain email, joined to the Ad Library on the RERA-number token. Drop Maps-for-complaints, web-search launch discovery and domain guessing. Re-check last round's near-misses first.
Why: Great Spaces (round 2's top lead) came from the email filter. Maps gave 200 places, 81 reviews, 0 reply complaints for ~US$1. Search engines were blocked (captcha, 429); ~60,000 domain probes mostly hit namesakes. Pool-recheck was round 2's best scout (5 of 12 qualified). One call returned all 277 applications.

**R5 [generic]** Rule: script deterministic work (GujRERA pull, domain/MX/HTML fingerprint, ad-card parse) and keep agents for judgement. Preflight Apify credit and search quota before launch. Stagger qualifiers after scouts. Write tokens, minutes and dollars per phase into a campaign cost file.
Why: round 1 hit Apify's monthly hard limit mid-run with ~US$3 of a US$15 budget used. Round 2 qualifiers shared one WebSearch quota; both A leads were graded with no web search. "Free" round 2 cost ~1.5x tokens per lead, but that is n=1 each, and round 2 was partly seeded by the Apify pool.

**R6 [generic]** Rule: "business-published contact" is not "working contact". Gate on MX lookup, role/free/business class, verified_at date and suppression before a lead counts as reachable. Tag every published WhatsApp number "enquiry line, unverified". Send free-mail-only leads to the human-call lane. Never store whole register records (they hold PAN and ID fields).
Why: Elenza's own-site address bounced; swarnagroup.in has no MX; SuperCITY's MX points to itself; 4 of 10 round-1 leads had only free mail; every email used is a shared inbox.

**R7 [generic]** Rule: every ad fact carries first_seen and observed_at. "Hungry" needs ads seen twice >= 48 h apart or older than ~3 days (younger = "burst, unproven"). Expire pool entries after ~3 days without a recheck. The send-day Ad Library recheck is a gate.
Why: Swagat's ads were 21 h old at qualification; Pride's ~180 ads all started 9-10 Oct (one burst); 4 of 11 pool names vanished within 5 days.

**R8 [generic]** Rule: every sentence in a hook, page or console summary traces to a dated, quoted observation. Run the fact-check between qualify and console push. Generate console entries from the fact-checked dossier (single source). Record `whatsapp_path = observed | possible | unknown` per lead.
Why: the fact-check fixed 4 of 4 hooks ("book a site visit" was Novarra's wording; "4B3HK" is the developer's label; Parshwanath is 2 BHK only; Space Age resells Arvind Sensora). The 12 round-2 console entries were pushed before the fact-check and still say Parshwanath uses a "Facebook lead form" (unverified).

**R9 [generic]** Rule: keep a persistent seen-ledger (campaigns/seen.jsonl) keyed by RERA promoterId / Facebook page ID / domain / phone last-10, with status, reason, date, source. Scouts return a stable id and qualifiers echo it. Count independent sources only (Ad Library and RERA are two systems; pool-recheck plus Ad Library is one).
Why: `found_in` was empty for 10 of 10 round-1 leads and 3 of 12 round-2 leads (both A leads). 22 of 34 candidates were never qualified. Near-miss lists sat in free text.

**R10 [generic]** Rule: do not start a round while the unsent A/B pool is >= 2x the next wave's capacity, or while the last wave is younger than its decision window with no decision recorded. Qualify just-in-time (lead next in line, with the send-day recheck). If the owner asks anyway, state the rule once, then comply and log it.
Why: 13 of 22 leads were unsent and wave 1 had no replies when round 2 started. The operator's own 17 Oct advice was overridden and the start message did not restate it. The bottleneck is per-lead assets and language, not discovery.

**R11 [generic]** Rule: run a fingerprint script on every candidate site before paying for a qualifier: fbq/GTM/AW tags, utm hidden fields, "crm." / api_lead / webhook hosts, chat-widget vendors (Kenyt.ai, "Powered by SAI"), Firebase/Supabase names, sitemap lastmod. Auto-penalise a confirmed CRM or bot and keep the evidence URL.
Why: Swarna's in-house CRM (Firebase "swarna-group-crm") was found only after a full qualifier run (score -2). At least 9 developers with websites were rejected for existing automation.

**R12 [real-estate]** Rule: "reachable by email" and "needs automation" pull in opposite directions. Treat phone-first leads as a separate lane (owner's team calls, as done for Pride) and pilot 3 of them next to the email lane.
Why: only developers with websites have an email, and they more often already automate. 16 phone-only click-to-WhatsApp advertisers were held back. The merge score gives +2 for a published email and silently decides who is researched.

### 3.2 Content and claims

**C1 [generic]** Rule: write a claims ledger before the first asset (id, wording, allowed surfaces, evidence, owner-decision status, banned variants). Build scripts, the template spec and the voice script pull wording from ledger ids. Write QA rules as "on ALL surfaces" and give pass 2 the ledger plus a diff of pass 1.
Why: one wrong claim ("your ads / ads that open a WhatsApp chat") lived in up to seven places: page H1, h3, FAQ, hero default, voice lines, video headline, template body, sent emails. Each QA pass found it somewhere new. QA scoped "never say your ads" to email only.

**C2 [generic]** Rule: no default values for factual slots. The build fails and names the lead and field. Add `ads_owner_verified` (true only if the advertiser page is linked from the lead's own site); "your ads" only when true. After fixing a claim, grep built files for the old wording.
Why: defaults ("runs ads that open a WhatsApp chat", "We saw your ads for X") turned wave-1 assumptions into claims about wave-2 leads. Swagat got it by omission; Rivanta's built page still says it after the hook was fixed and the email went out.

**C3 [generic]** Rule: open owner decisions gate the build. Anything depending on an unanswered decision is rendered neutral. Ask the 4-5 open questions in ONE message before the first voice take. Verify reviewer-suggested feature lines against the service facts.
Why: `demo_free: True` was a default; "The demo is free" is baked into all 10 renders and 9 pages while the decision was still open. "Site visits land on your calendar" was copied from a QA fix suggestion without checking the product has a calendar.

**C4 [generic]** Rule: the voice-over carries only claims true for ALL leads and already decided (benefit, steps, "can"). Lead-specific or undecided claims ("your ads", "free", project name) go on-screen, in the page or in the email. Keep one WhatsApp template per lead class (verified-ads developer / reseller / unverified ad owner).
Why: one MP3 serves every lead. Changing it means a new ElevenLabs take by the owner, a rebuild of the timeline and 10 re-renders (~15-50 min), plus a new Meta template for any body change (approved in ~20 min). Template {{2}} is used twice, so "We saw your ads for {{2}}" is false for resellers. Pass 2 called the voice untrue for Great Spaces and Parshwanath; accepted "for now".

**C5 [generic]** Rule: add an offer-alignment check to every QA set: does this message sell what we sell, and what is the single ask? Store a one-line offer and ask. Subject names the outcome, not "a video"; first paragraph says what we do before what we made; the first 8 s of the video state the product.
Why: 6 emails went out as "A short video for X". The owner caught it 2 minutes after the fifth first-touch: "hume whatsapp automation bechna he, video nahi". No QA lens tested it.

**C6 [generic]** Rule: email copy that worked in QA: project name first in the subject (phone inbox cuts ~40 chars), outcome before asset, no staff names, no "free", "instant" or "your ads", address-source line in the footer, opt-out line, "under 40 seconds". Submit a new Meta template when copy rules change, with separate variables for "what we saw" and "what we made".
Why: v1 -> v2 -> v3 each fixed issues from the owner, the fact-check and the recipient-lens QA.

**C7 [real-estate]** Rule: model resellers and third-party brands with `entity_type`, `advertises` (the third-party project, plain text, never in subject, banner, video chrome or template params) and `made_for` (the recipient's own name). Build refuses entity_type=reseller when made_for equals advertises. Non-affiliation sentence above the fold.
Why: the Space Age video was first rendered as "Arvind Sensora" (2 of 6 wave-2 renders were rework). About 87 resellers advertise Sensora, so never imply exclusivity.

**C8 [real-estate]** Rule: unit labels verbatim (4B3HK stays 4B3HK; plots in sq yd; a shop is not a BHK; 2-BHK-only means no "other size" chip). Say "scheduled", never "registered" or "booked". No price anywhere. Check name collisions (Aaroham vs Ashiana Aaroham; Swagat Developers / Builders / SWAGATBUILDCON; Parshwanath Corporation Ltd is a different company).
Why: all were found by the fact-check or QA. The fact-check itself suggested "Other size" for a 2-BHK-only project, so its output also needs a check.

**C9 [generic]** Rule: turn every mechanical QA class into a script run on every build with worst-case names (lint_all: banned phrases per surface, display name <= 20 chars, hook <= 160 chars, {{n}} reuse, contrast, chips equal the unit field, hero CTA y < 800, no overlap with the play button). Human lenses judge new design only.
Why: test_subs.py and FORBIDDEN_NUMBERS worked. Still re-found by LLM lenses: a 20-char name spans 16-389 px of a 405 px poster; a 238-char hook pushed the CTA below the fold; contrast 3.27:1 and 2.15:1; play button covered the chip row after poster_at changed.

**C10 [generic]** Rule: rebuild ALL slugs for production (no single-key shortcut), write a build manifest with a hash of the lead's fields next to each asset, and refuse a send when the hash differs. Keep gate scripts (fact-check, ad recheck, preflight) in agent/workflows/.
Why: the five wave-1 pages (built 09:28) still carry claims that two QA passes removed from the wave-2 pages, and their leads already got emails linking to them. Parshwanath's video said "Other size" while its page said "Tell me more".

**C11 [generic]** Rule: the owner's approval must show the claims, not just the text: ledger ids, truth-sheet as_of time, QA verdict, and sha256 of header video, banner and page. Per lead, show whether the number is labelled WhatsApp.
Why: the approval hash covers email/template text only. Claims in video, page and banner are approved by nobody. Ad facts decay in days (wave-2 ads were 1-16 days old).

### 3.3 Outreach and monitoring

**O1 [generic]** Rule: email is the primary channel; WhatsApp is lead-initiated (a wa.me button) or a human 1:1 from a staff phone. If cold templates are used: write the success criterion first ("at least 1 of the first 3 delivered"), code a circuit breaker (2 failures with 131049 / 131026 / no status after 10 min stops the wave and posts the Meta quality rating), and never read an own-number test as a delivery forecast. Cold templates go OFF after 3 consecutive non-deliveries.
Why: 0 of 3 delivered. The only "delivered" WhatsApps were the owner's and boss's own numbers. The owner sent NB 3 minutes after hearing of Brij's failure, and chose all 4 wave-2 sends although several scouts wrote "Do NOT cold-template".

**O2 [generic]** Rule: one fixed order: email first; WhatsApp only to numbers the business labels WhatsApp, at least 3 h later, only if no reply / tap / STOP is seen. Do not write "we will also WhatsApp you" in the email unless that send is conditional in code.
Why: wave 1 order was inconsistent (WhatsApp 55-80 min before email for Brij and NB; Elenza WhatsApp 14 s after the email, before the bounce). Wave 2 gap was ~80 min, QA said 3-4 h. A promise the template cannot keep is worse than silence.

**O3 [generic]** Rule: measure email deliverability before scale: MX per address, SPF/DKIM/DMARC of the sender domain recorded, a seed test to 3 own mailboxes (Gmail, Outlook/Yahoo, Zoho/Workspace), a neutral From (not a staff name), a dedicated subdomain before ~20 leads, and a rule that any complaint pauses the wave.
Why: SPF/DKIM/DMARC and the seed test were planned on 16 Oct and no result is recorded. "Delivered" is not "inbox": with 0 genuine opens, not-read cannot be told from spam.

**O4 [generic]** Rule: make inbound email machine-readable before any send that promises an opt-out: Resend inbound webhook or an IMAP poll of the Reply-To mailbox, writing `email_reply` rows to the console, auto-suppressing STOP wording and alerting the owner. Replace the mailto List-Unsubscribe with an HTTPS one-click endpoint. Until then, name one human and log their check before each WhatsApp slot.
Why: nobody reads the mailbox. The first three first-touch emails had no Reply-To (replies go to a personal-name inbox). The "skip WhatsApp if replied" rule cannot see email replies.

**O5 [generic]** Rule: start every wave with one sentence: "Chat words are not approval; send OK CODE from your own WhatsApp." Create proposals only after copy is frozen (any change = new code). Show ONE consolidated message 10 minutes before an agreed send hour.
Why: on 16 Oct the owner typed "send" three times and wrote "time waste" (send at 16:20, 23 min later). 4 codes were wasted by late copy changes or a provider failure. The wave-2 delay (68 min) was owner availability, not code count. The gate itself is sound.

**O6 [generic]** Rule: "approved but held" needs machine state. Extend the existing no-model approval watcher (not a new lane) with a job file: not_before, hold flag, code. It enforces window, weekday and festival, suppression, ignore list, no reply/tap/STOP, page and video 200, ad-recheck stamp from today, 2-min gap, status read at +60 s, and the circuit breaker. One actor reports send state, from sends.jsonl and crm.py only.
Why: the 15:30 checks existed only in the operator's head; the heartbeat woke three times just to decide "not executing". On 16 Oct the heartbeat said "lead got nothing" for a send that happened, while the fast lane said "not sent"; truth was "sent, not delivered".

**O7 [generic]** Rule: define a "qualified signal" before anyone reads a rate: a written reply, an answered call, a CTA/demo from a non-team number, or a page/video event >= 60 s after delivery outside ignore windows. A bare page GET is "fetched". Email opens never count. Never mark a lead hot from a web event alone. Store signal_confidence on every row. Log every dropped event.
Why: Great Spaces "engaged" 6 s after send; NB and Rivanta "opened" within 30 s; Pride's card went HOT from the team's demo test; level_of() still treats any non-bot GET as engaged. Scanner thresholds (30 s page / 60 s click) come from n=1.

**O8 [generic]** Rule: write a watch matrix into the playbook. Agent = sends, +60 s status read, console check every 30 min during a wave. VPS cron = engagement and email webhooks. Named human = shared info mailbox and company phone line. Owner = console glance at day start and end. Add a free alert path for four events (reply, demo "Yes/person", STOP/complaint, bounce spike) that ignores quiet mode, and an external uptime check; no wave if it is red.
Why: owner-quiet removed all push alerts; the heartbeat needs the PC on (no line for ~39 h); the 23-min VPS outage was found by the owner ("crm bnad he"). The site footer shows the boss's personal number on every page, so a lead could call him unbriefed.

**O9 [generic, hypothesis]** Rule: weekday-only sends with a festival block list; email 10:30-11:30 IST; assets frozen the evening before; codes requested by 10:00. Log first-reaction time per lead.
Why: Brij's page open came ~16.5 h after a Friday email; Pride's ~47 h after a Saturday email. n=2. Stop touches by ~5 Nov (Diwali ~8 Nov).

### 3.4 Process and owner

**P1 [generic]** Rule: reuse is the speed lever. For a same-product, same-vertical wave, only add leads.json entries. For a new vertical, at T+0 start in parallel the owner's voice take, the design pack and the Meta template; these are the only parts the agent cannot compress. Plan renders at ~1.5 min each.
Why: master voice, template and page template existed, so wave 2 took 56 min. Wave 1 took ~23 h; the long poles were human or Meta.

**P2 [generic]** Rule: speed to send is solved; speed to learn is not. Gate campaign 2 on the Day-3 and Day-5 reads. Do not add volume while replies are 0; change the offer or message (human 1:1 first, a live demo number).
Why: 71 h after the first send there are 0 replies. Timeline: 15:30 today WhatsApp round; Thu 22 Oct touch 2 for wave 2; Mon 26 Oct read results; prep that touches nobody can run meanwhile.

**P3 [generic]** Rule: verify the pitch premise per lead before building. Record per-ad CTA destination (WhatsApp / lead form / website / unknown) and a `premise_proven` flag; rank proven leads first. Never put lead-specific premises in the audio.
Why: for 2 of 4 wave-2 leads the evidence does not show their ads open WhatsApp. Both QA passes flagged it; it still ships in the narration.

**P4 [generic]** Rule: send the owner one Day-0 list: (1) Apify credit; (2) voice slot if the vertical or language is new; (3) who watches the info mailbox, and a neutral From; (4) confirm the `vps_run.sh` allow rule exists; (5) a fixed daily send hour; (6) team test phones and IPs; (7) who makes human calls; (8) open claim decisions (free demo? what does "Yes" send?); (9) secrets only through the hidden-prompt script.
Why: everything else the operator does alone (research, fact-check, build, render, QA, deploy, propose, send after OK, monitor).

**P5 [generic]** Rule: steer like the owner works. Short Hinglish answers, ask questions only when blocked, end each chunk with one line "what I need from you". State a risk once, then comply inside the gate. Before any draft show 3 lines: what we sell, what the subject promises, the one ask. Keep a decision register at the top of the campaign file. Log every discussion point in memory.md.
Why: 123 messages, median 66 characters. His words:
- "bas tu meri bato ka jawab deta jaa aur kuch mat puch" (answer my points, ask nothing back)
- "email first nahi, WhatsApp bhi saath me" (19 Oct, both channels)
- "hume call nahi karna" (14 Oct, no calls)
- "first impression, full force" (first-touch doctrine)
- "UNHE 3.30 KO BHEJO TAKI KOI ISSUE AYE TO ME YAHA HU" (send at 3:30, so I am at my desk)
- "result aane do kitna time lagega" (he waited 63 min on research)
He flipped plans often (plain email -> video-first -> full-force WhatsApp; Gujarati for all -> English for 4; email-first -> both channels).

**P6 [real-estate]** Rule: contactability is the narrowest stage (9 of 22 contacted). Make email_mx_ok, email_source_url, a phone for a human call and the lead's language mandatory scout outputs. Do not rank a lead sendable if its language has no voice or template yet. Stop research at `target_good`.
Why: blockers were language (5 Gujarati/mixed leads waiting for a voice take), no email route, no MX, bounce risk, low grade. Gujarati clips have been pending since 17 Oct.

**P7 [generic]** Rule: do everything through ONE door script (`vps_run.sh`, owner-added allow rule), owner-held secrets and the hidden-prompt secret script. Never mint approvals, write secrets, edit settings.local.json or start daemons yourself. Write scripts with the Write tool; set PYTHONIOENCODING=utf-8.
Why: classifier denials fell from 7 on 15-16 Oct to 0 during wave 2. The remaining refusals were correct (Secret-Store Writes: a clipboard file path was stored as the Resend secret). A chat-token workaround was refused as a security weakening.

**P8 [generic]** Rule: do not extend the unattended lanes. The loop is: attended chat + the no-token approval watcher + the VPS engagement cron (5-min) + the 24/7 demo responder. Keep the heartbeat read-only or off. Budget a 4-lead wave at 4-6M tokens (research 2.2-4.1M, fact-check 0.5M, 2 QA passes 1.0M, preflight 0.4M). Use 3-lens code review only for NEW code.
Why: 30% of campaign tokens went to reviewing tooling and ~99 min to building lanes before any reply existed. The fast lane has been down since 15 Oct. The heartbeat executed 2 of 20 live actions.

### 3.5 Strategy

**S1 [generic]** Rule: show every rate as k/n with a 95% interval and a "too early" flag. Never write "0 replies = failed" or "2 opens = promising". Judge designs on high-base-rate upstream metrics (delivered, qualified human open, video >50%, CTA tap); read replies one by one.
Why: see section 2. At n=30 upstream metrics give about +/-15-18 points.

**S2 [generic]** Rule: pre-register hypothesis, metric, n_min and decision rule in the console before a wave is sent. Keep templates identical across campaigns 2-4 so samples pool (3 x ~12 leads = ~36 per arm). Only LOG subject, send time, offer wording, language and lead type until pooled n is large enough.
Why: subject change, day, lead and touch number are confounded in wave 1. The planned Hungry-vs-Warm comparison was silently dropped and the stored campaign plan (cap 10, template-only first touch) no longer matches practice.

**S3 [generic]** Rule: test the human voice. A named team member calls or WhatsApps 10 of the Hungry leads (5-10 min each); the agent prepares dossier, 4-line script, objection answers and logs each call. Send the page/video AFTER the call as a leave-behind. Log: answered? decision-maker reached? how enquiries are handled today? reaction? objection?
Why: 16 of 22 researched leads had a call in the channel plan; 29 of 30 earlier Meta-ad leads are "phone call first". The 14 Oct "no calls" rule blocked it. The only human contact so far is the Pride hand-off, and its outcome is unrecorded.

**S4 [generic]** Rule: record `route_type` per lead (named_person | personal_mobile | role_inbox | webmail | form_only) and rank by route type before grade. Prefer a named decision-maker with a personal mobile for the first human contact.
Why: 12 emails went to shared inboxes and produced no conversation; Space Age's personal mobile was chosen on purpose. Test only after >= 20 leads per class.

**S5 [generic]** Rule: heavy first touch vs light first touch is a hypothesis, not a doctrine. Give the 12 researched-but-unbuilt leads (4 Warm from round 1 + 8 from round 2) the LIGHT touch (4-line personal note, one generic page, a call). Gate per-lead video and page behind a signal in campaigns 2-4, or build one shared page per segment.
Why: ~0.9M tokens, ~25 min of build/QA and ~2 codes per contacted lead, zero conversations. "First impression, full force" was never compared with a lighter touch.

**S6 [generic]** Rule: make the console answer hypotheses. Unit = unique leads with explicit denominators. Add to each lead: arm, lead_type, route_type, language, copy_version, subject_variant, asset_weight, first_touch dow/hour, frozen hunger score, outcome (no_signal | seen | replied | conversation | positive | meeting | pilot | won | lost | stopped). Add an `experiment` entry per hypothesis and a `scoreboard` entry per campaign and arm. Also log copy_version and arm in sends.jsonl.
Why: campaign_totals() mixes messages, opens and leads; repeat opens count; no outcome can be tied to a variant. The console is schema-light, so no migration is needed. Show the scoreboard to the owner only once a campaign has 20 leads.

**S7 [generic]** Rule: what transfers to another vertical: research workflow (change the CAMPAIGN text and sources), the skeptic, the fact-check, the email stack, the page template and the demo-responder engine. Rebuild per vertical: hook language and unit labels, demo questions and texts, video narration (one voice take), proof point, a vertical claim list and the hunger weights.
Why: one Ad Library run found 30 leads across 10 verticals for ~US$0.94. Real-estate-specific parts are GujRERA, RERA claim rules, unit labels, reseller handling, name collisions, launch urgency and Diwali timing. For clinics, keep the demo to appointment booking; no patient data.

---

## 4. Our own mistakes, honestly

1. The boss's personal number went onto the WhatsApp button and call line of 4 live pages (16 Oct). The owner caught it; build_pages.py now refuses it. The footer still shows it on every page.
2. Six emails sold "a short video" (subject and copy). The owner, not QA, caught it 2 minutes after the fifth first touch.
3. "Free" was a default. It is in all 10 voice renders and 9 pages while the decision was open.
4. No MX check in round 1; Elenza's published address bounced. The MX check was added by hand in round 2, after the workflow.
5. No stop-loss after the first template failure. Brij failed at ~15:20; NB (15:39) and Elenza (16:35) were still sent; wave 2 schedules 4 more.
6. First three emails had no Reply-To; List-Unsubscribe is a mailto to a personal-name inbox; SPF/DKIM/DMARC and the seed test were planned and never recorded; the dedicated-subdomain advice was not followed.
7. The fact-check started only in wave 2, after 5 leads had been contacted. Even then, console entries were pushed before it ran and never re-synced.
8. Wave-1 hooks went beyond the evidence ("every tap to one WhatsApp chat" for Pride; "many ads invite WhatsApp" for Rivanta, where one ad had the button); caught by claims review, not by research.
9. Reported false signals as facts: Pride "Delivered" (boss test), Brij page use (the owner's click), Great Spaces "engaged" at +6 s, Pride HOT (team test), mail auto-opens. A heartbeat told the owner "lead got nothing" for a send that went out. A smoke test on the real todo file sent the owner the same video 3 times (15 Oct).
10. Built scanner thresholds from one observation (n=1) and left level_of() counting any non-bot GET.
11. Hunger scores shown with false precision ("Hungry 8/10"). The same agent found and scored the lead; 14 of 22 sit at 7-8; round 1 was hand-scored; the validation plan was dropped without updating the campaign entry.
12. Launched three Apify scouts with US$3 caps each without checking remaining credit. Ran 12 qualifiers and 6 scouts on one WebSearch quota; both A leads had no web search. Did not notice `found_in` empty in two rounds.
13. Treated the older Apify pool's A grades as usable. All five real-estate A rows downgraded.
14. Did not restate the 17 Oct stop rule when round 2 was requested; did not reuse round 1's near-miss lists or RERA-token advice.
15. Over-built tooling before any reply existed: fast lane, operator lane, Telegram lane, sandbox kit, Console v1 (judged "bohot kharab", rebuilt as v2), public pages inside the console before the owner redirected hosting. About 4.4M tokens (30%) went to reviewing tooling.
16. Burnt or wasted approval codes: one consumed before a provider app-id read failed (now read-before-consume), one expired unsent, two superseded by copy changes.
17. Pulled copy straight from QA suggestions ("Site visits land on your calendar") and hand-copied fact-check output into leads.json ("Other size" for a 2-BHK-only project). Changed a poster frame after the play-button fix, hiding the chip row.
18. Did not rebuild the five wave-1 pages after the template fix; left gate scripts outside agent/workflows/; left the voice re-record backlog open for 3 days so it grew.
19. Chose send times by availability (Fri 16:29, Sat 10:05, Mon 14:07), cut the QA-advised 3 h gap to ~80 min without logging it as an experiment, and wrote a plan (cap 10, template-only first touch, Hungry then Warm) that owner reversals overtook within four days.
20. No external uptime monitor: the VPS reboot took down landing pages linked from live emails and was found by the owner. Nobody was assigned to the info mailbox before the first sends.

---

## 5. Checklists

### PRE-BUILD (before any page, video, email or template exists)

Campaign, once:
- [ ] Day-0 list (P4) sent to the owner in ONE message and answered.
- [ ] One-line offer and single ask written ("automatic WhatsApp replies for enquiry ads; ask: watch 40 s / try the demo").
- [ ] Service-facts and decisions registers filled, or the item is rendered neutral (is the demo free; what does "Yes, send the demo" send; forms; calendar; is "about a minute" measured end to end).
- [ ] Claims ledger exists. Voice script and WhatsApp template body use only rows true for ALL leads. Banned until proven: "your ads" (unless ads_owner_verified), "free" (unless decided), "instant", "gets", "every", "never share", personal numbers.
- [ ] Budget preflight: Apify credit, WebSearch quota, weekly Claude percent, expected tokens (4-6M per 4-lead wave).
- [ ] Stop rule (R10) passed: unsent A/B pool < 2x next wave, last wave past its decision window.
- [ ] Hypotheses, metrics, n_min and decision rules entered in the console (section 7).

Per lead:
- [ ] Skeptic ran with a different method. Grade <= B unless two dated observations + verified identity + working contact route.
- [ ] Contact gate: MX ok, role/free/business class, verified_at, suppression checked. Published WhatsApp number tagged "enquiry line, unverified". Free-mail-only goes to the human lane.
- [ ] Resistance fingerprint run (CRM, bot, webhook, Firebase). Confirmed CRM or bot = penalty.
- [ ] Fact-check done BEFORE the build, as typed fields: exact project name + collisions, entity_type, advertises vs made_for, verbatim unit labels, ads count / CTA per ad ID / destination known? / start date, ads_owner_verified, whatsapp_path, "no price", "scheduled" wording, do_not_claim, as_of date.
- [ ] Build has no factual default; a missing field fails the build.
- [ ] The lead's language has a voice and a template; otherwise it is not sendable.
- [ ] Hook <= 160 chars; display name <= 20 chars or a short_name.
- [ ] ALL slugs rebuilt; lint_all passes; worst-case-name stress render passes; manifest hashes written.
- [ ] QA lenses (claims, recipient, visual, offer alignment) run ONLY for a new template or the first email of a new copy version, with ledger and truth sheet as ground truth.

### PRE-SEND (evening before / morning of; assets frozen)
- [ ] Manifest hashes of live page, video, banner and header video equal the audited build (wave-1 pages rebuilt after any template fix).
- [ ] Seed test to 3 own mailboxes done; SPF/DKIM/DMARC of the sender domain recorded; Reply-To set on every email; HTTPS one-click unsubscribe or a named human.
- [ ] Inbound path live: script or named human reads the Reply-To mailbox; STOP wording reaches suppression; who checks before each WhatsApp slot is logged.
- [ ] Team test phones, IPs and browsers are in DEMO_TEST_NUMBERS and engagement_ignore.json. Team tests use the [Test] email to the owner, never lead links. The boss is briefed about calls from the footer number (or the footer number is changed by the owner's decision).
- [ ] External uptime check green on one landing page and the webhook route.
- [ ] Proposals created only after copy is frozen. Approval text shows ledger ids, as_of time, QA verdict, hashes and, per lead, whether the number is labelled WhatsApp.
- [ ] One consolidated message to the owner 10 minutes before the agreed hour. First sentence: "Chat words are not approval; send OK CODE from your own WhatsApp."
- [ ] Send hour set: weekday, not a festival, email 10:30-11:30 IST, codes requested by 10:00; WhatsApp (if any) >= 3 h later and before 17:30.
- [ ] If cold WhatsApp is used: success criterion and circuit breaker written down (O1).
- [ ] Watch matrix (O8) written and each role named.

### SEND-DAY
- [ ] Ad Library recheck for every ad-dependent claim (~30 s); stamp from today. If an ad is gone, use the prepared fallback wording and rebuild, or drop the lead.
- [ ] Page, video and hosted assets return 200.
- [ ] Engagement and email-reply check before each WhatsApp slot; skip any lead that replied, tapped, opened or wrote STOP.
- [ ] Email first; WhatsApp only to labelled numbers, 2-min gap; read the previous status before the next send.
- [ ] Read delivery status at +60 s after each send (131049 / 131026 = not delivered). Read the Meta phone-number quality rating after cold templates.
- [ ] Log per send: copy_version, arm, route_type, subject_variant, asset_weight, dow/hour, claims shown.
- [ ] Drop scanner-timed events (page < 30 s, click < 60 s after delivery) but log each one.
- [ ] Console check every 30 min during the wave. Tell the owner only: visit after 60 s, video play, button tap, reply, STOP, bounce.
- [ ] End of day: append the discussion points to memory.md; scoreboard as k/n with intervals; Day-3 and Day-5 reads scheduled.

---

## 6. Automation: what exists, what needs a human, what to build next

**Automated today**
- Research workflow (scouts, qualify, skeptic), fact-check, video render, page and email build, QA lens workflows, deploy through `vps_run.sh`.
- `propose.py`, the no-token approval watcher and sender (after an OK code), suppression, daily caps, send window, duplicate guard.
- 24/7 on the VPS: demo responder, 5-min engagement sync cron, Resend webhook, scanner filter, ignore windows.

**Still needs the human (owner or team)**
- OK codes. ElevenLabs voice takes (owner in the web UI). Apify credit. Secrets (hidden-prompt script only).
- Reading the info mailbox and the company phone line. Human calls. Claim decisions (free demo, pricing, forms, calendar). Gujarati voice. Meta business verification. Citing a proof point (Takshashila permission).
- The allow rule for `vps_run.sh`. Brief to the boss about the footer number.

**Automate next, ordered by value**
1. Inbound email capture: reply-class rows in the console, STOP -> suppression, HTTPS one-click unsubscribe, owner alert (O4). This closes the biggest blind spot.
2. Deterministic contact gate and site fingerprint scripts (MX, role/free class, CRM/bot/pixel hosts) run before any qualifier (R6, R11). Zero tokens.
3. Claims ledger, no-default build, lint_all, stress render, build manifest and hash check (C1, C2, C9, C10). Zero tokens.
4. Watcher upgrade: held-until state, weekday and festival calendar, engagement skip, ad-recheck stamp, +60 s status read, cold-WhatsApp circuit breaker (O6). Teach heartbeat_check.py "held" so it stops waking.
5. Console: experiment and scoreboard entries, cohort tags, signal_confidence, the qualified-signal rule, unique-lead denominators (S6, O7).
6. Free alert path for four events outside quiet mode, plus an external uptime check (O8).
7. Research scripts: GujRERA pull, bulk Ad Library pull (needs Apify credit), seen-ledger, cost file (R3-R5, R9).
8. Deliverability preflight: SPF/DKIM/DMARC check, seed test, dedicated sending subdomain (O3).
9. Batch approval (one wave code binding exact action hashes). Lowest priority: it saves ~90 s of owner time per 8 sends. Build only if the owner explicitly accepts a security-model change and an independent review confirms the agent cannot mint approvals.

---

## 7. Hypotheses and the experiment plan for campaign 2

Every row goes into the console as an `experiment` entry BEFORE the first send: hypothesis, metric, arms, n_min, decision rule, start date.

**Step 0 (real estate, now to 26 Oct): human sprint and decision**
- 15:30 IST today: apply the cold-WhatsApp rule to the 4 wave-2 results.
- Owner decides whether a named team member may call (see section 9). If yes: 10 calls on Hungry leads (S3).
- Thu 22 Oct: touch 2 for wave 2 and calls attempted. Mon 26 Oct: checkpoint. Stop all touches by ~5 Nov.

**Ranked hypotheses (most information per lead first)**

| ID | Hypothesis | Metric | n needed | Rule |
|---|---|---|---|---|
| H1 | Human call or personal WhatsApp beats email-only | Two-way conversation within 7 days | 20 to describe (+/-22 pts); 32-42 per arm to compare 10% vs 40% | Describe first, compare when pooled |
| H2 | Lead-initiated wa.me tap, or human 1:1, beats cold template | Delivered, then demo start | Lead-initiated starts per 30 emails | Cold templates on stop-loss (O1) |
| H3 | Light first touch matches heavy at far lower cost | Conversations per 10 leads; tokens per lead | 12 light vs 9 heavy (descriptive) | Adopt light by default if similar |
| H4 | Pay-signal score predicts response | Reply and page-open rate by tier and by source | 15 at >= 7 and 15 at <= 6, same touch, score frozen | Judge only at n >= 30 |
| H5 | Route type matters (named person / personal mobile vs role inbox; phone-first lane vs email lane) | Conversation rate | >= 20 per class | Pilot 3 phone-only advertisers now |
| H6 | Outcome-first subject beats video-first | Human page open within 72 h | ~39 per arm (~80 pooled) | Log only until then |
| H7 | Send slot matters (08:30-09:30 vs 10:30-11:30 vs afternoon / Fri / Sat) | Hours to first human open | >= 30 per slot (~90 sends) | Log dow/hour only |
| H8 | Offer: free demo vs free 7-day pilot vs one-question opener | Positive reply | >= 40 per arm | Owner must define pilot and price first |
| H9 | Gujarati voice/text beats English for Gujarati-first leads | Positive reply | ~8 candidates | Descriptive only |
| H10 | Developer vs reseller/broker/solo owner | Conversation rate | >= 20 per class | Log only |

Also observe (no arms): email inbox vs promotions vs spam (seed test); whether `whatsapp_path = observed` predicts response better than `unknown`; whether the "we will also WhatsApp you" line changes opt-outs (needs an A/B to test).

**Success metrics** (unique leads, k/n, 95% interval, "too early" flag): Reached (delivered) -> Seen (qualified human signal) -> Engaged (CTA or demo start) -> Replied (written reply or answered call) -> Positive (asks for the demo, books a call, asks the price) -> Meeting or pilot. Add hours-to-first-signal and cost per lead (tokens, dollars, human minutes).

**Decision rules (my proposal; the owner confirms)**
- At least 2 positive in at least 10 real conversations: continue and scale this segment.
- 0 positive in at least 10 conversations: change the offer or segment, not the channel.
- Fewer than 10 conversations because nobody answers: reachability problem; shift to warm sources (the 4 engaged + 1 hot in the old CRM; the 3 clients with real testimonials on the pilot page).
- Call the approach failed only after 21 or more fully worked leads with 0 positive (bound 13%), or 30 (9.5%). Call it working only on named positive conversations, not on opens.
- Cold WhatsApp at 15:30: 2 or more of 4 delivered = keep templates only for personal mobiles; 0-1 = off for cold leads.

---

## 8. Three recommended next campaigns

Gate for all three: the real-estate sprint has reported (~26 Oct), the owner has added Apify credit (~US$3 per segment; ask for US$5-10), and the weekly Claude limit is checked. Real estate keeps running as the control. Do NOT spend a Gujarati voice take on the 5 wave-3 leads before the sprint results.

For each campaign: research >= 30 candidates with route_type recorded; a 5-call discovery sprint before any per-lead asset; a light note plus one shared segment page; per-lead assets only after a signal; the same template and logging schema so results pool. The 14 Oct CSV grades are scraper-only and must be re-checked live (all 5 real-estate A rows downgraded).

1. **Solar installers / EPC.** Strongest time-boxed need (ads push the PM Surya Ghar subsidy deadline of 31 Mar 2027), easiest email route (3 of 3 had email + website + ads; 2 of 3 graded A), qualification flow (bill, roof, pincode) maps one-to-one onto the demo. No proof point: label it a demo only. Example: Grando ran 4 click-to-WhatsApp ads from 9 Sep.
2. **Education, study-abroad and coaching.** WhatsApp-heavy admissions funnel; the only real proof point (Takshashila institute ERP, +40% admission conversion) and an existing product. Needs the owner's permission to cite it (TODO in proof_points.md). Career Compass and Angel Edunext have forms, callback popups and no chatbot.
3. **High-ticket clinics: IVF/fertility, hair transplant, multi-branch dental only.** Best fit for the human-call lever (doctor-owner has a published mobile). Skip single-ad solo dental (4 of 5 dental leads are B with 1 ad and 28-155 followers). Regulated: medical ad claims and DPDP; appointment booking only, no patient data in samples.

CSV pool by vertical (30 rows; analysts counted 11 or 12 real estate): real estate 11-12, dental 5, solar 3, IVF 3, study-abroad 2, coaching 1, hair clinic 1.

---

## 9. Open questions for the owner

1. May a named team member call or WhatsApp the Hungry leads? This reverses the 14 Oct "hume call nahi karna". Who, which hours, what SLA? What happened with Pride (who answered, what they said)?
2. Who reads the shared info mailbox and the company phone line, daily? Can we use a neutral From address and a dedicated sending subdomain? Is Resend inbound available on the plan, or do we poll IMAP?
3. Is the demo free? What exactly does "Yes, send the demo" send, who answers "Yes, contact me", what are business hours? (The page and voice wording depend on it.)
4. Pricing, pilot offer, deal value and expected close rate are undefined. Without them "success" cannot be a number.
5. What is the success metric and stop-loss for campaign 1 (replies, meetings, by what date), so campaign 2 is a decision and not a default?
6. Who records the Gujarati voice, and when? Is the ElevenLabs plan licensed for commercial use? Do we add an AI-voice disclosure and a real Privacy Policy page (footer links go to "#")?
7. The boss's personal number shows in the site footer on every page. Change it, or brief him?
8. Will the owner add Apify credit (~US$5-10) and approve a small click-to-WhatsApp ad test for volume? When does the Apify monthly cap reset? What percent of the weekly Claude limit remains?
9. Does the owner accept a campaign-level approval, or one agreed send hour with one consolidated message? (The agent may never mint approvals.)
10. May Warm leads (Beverlynn, Silver, Lotus, Trinetra) be contacted as controls for the hunger-score test?
11. May we cite Takshashila (+40%)? Is the owner open to solar, education and clinics as campaigns 2-4?
12. Meta business verification and the 250-unique-recipients-per-24-h cap: what is the status? What did the 15:30 round do to the phone-number quality rating or messaging tier?
13. Should the five live wave-1 pages be rebuilt now, and should the voice lines ("Every enquiry from your ads gets...", "your WhatsApp ads") be re-recorded premise-free before more sends?

Operator-side unknowns to settle: the 15:30 delivery result; whether Brij's and Pride's page opens were the leads or the team; whether Cordelia's RERA approval of 12 Oct is real (one direct GujRERA API call settles it); whether the 22 never-qualified candidates were weaker or only scored lower on sourceCount + email; whether a personal or free-mail inbox is read more than a role inbox (n=1, Pride).

---

## Appendix A. Where the analysts disagreed, and what we decided

1. **Render time.** Playbook and two analysts say ~5 min per video. File timestamps show 4 renders in 5.8 min (~1.5 min each). We use 1.5 min and plan 2-5 min until re-measured. Ten re-renders = 15-50 min.
2. **Batch approval.** Outreach says build a wave code; process says not worth it (~90 s of owner time per 8 sends); strategy says a campaign-level approval. Decision: do the free fixes first (agreed send hour, one consolidated message, copy frozen before proposals, "chat is not approval" first). Batch approval is last on the build list (section 6, item 9) and needs the owner's explicit security decision.
3. **New executor vs "do not extend the lanes".** Decision: extend the existing no-model approval watcher; add no new lane; heartbeat stays read-only.
4. **More QA vs less asset building.** Decision: scripts and lints (zero tokens) always. LLM QA lenses (~0.5M tokens per pass) only for a new template or a new copy version. Test the light touch (H3) before adding gates per lead.
5. **Cordelia RERA 12 Oct.** Round-1 scout and round-2 qualifier say approved; the fact-check could not verify. Treat as unverified, say "scheduled", and settle with one direct API call. The console text from r2_overrides.json still carries this and the Parshwanath "Facebook lead form" phrase; fix both.
6. **Token cost per lead.** ~0.9M (lead-facing work 7.8M / 9 contacted) vs 14.55M total. Both are right; the second includes 4.39M of tooling reviews. Quote the scope.
7. **Email count.** "12 emails, 11 delivered" and "8 of 9 first touches delivered" are the same data (9 first touches + 3 follow-ups).
8. **Email-first vs both channels.** Research and QA say email first. The owner chose "WhatsApp bhi saath me" on 19 Oct. His choice stands for wave 2; the 15:30 data decides next time.
9. **Calls.** Research wants calls; the owner's 14 Oct rule blocks them; Pride's hand-off on 19 Oct was a call by his team. Unresolved: the owner must decide (question 1). Do not propose calls as already allowed.
10. **What comes next.** Lead research wants more real estate with scripted gates; strategy wants new verticals; process says it depends on replies. Decision: step 0 is the real-estate human sprint and the 26 Oct checkpoint; campaigns 2-4 follow only then; real estate stays as the control.
11. **Free vs Apify research.** Tokens per lead favour Apify (~220K vs ~342K) but n=1 each and the pools differ. We recommend US$5-10 of credit plus scripts, not a firm claim that free is worse.
12. **Pool counts.** The 14 Oct CSV has 11 or 12 real-estate rows and 12 or 13 A grades depending on the analyst. The count does not change any decision; re-check live before use.
