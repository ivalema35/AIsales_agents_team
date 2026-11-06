# Owner notes: Nexus360 proposal (for you only, do not forward)

Prepared Tue 20 Oct 2026, rebuilt after the skeptic review. Nothing has been sent. The PDF Sridhar sees is `proposal.pdf` (10 pages, A4; body text 8 pt or more, smallest text inside the figures 7 pt). He can read it alone in about 10 minutes.

## 1. Files

| File | What it is |
|---|---|
| `proposal.pdf` | The proposal. Send this. |
| `proposal.html` | Same document, one self-contained file (fonts and images inside). On a phone it reflows; on a desktop it shows A4 pages. Good for a screen share. |
| `page_1.png` to `page_10.png` | Each PDF page as an image (for checking). |
| `whatsapp_message.txt` | The short message to send with the PDF (under 90 words, one question, signed IV Infotech). |
| `prices.json` | Every price and the main switches. Edit, then rebuild (below). |
| `build_proposal.py`, `proposal_assets/` | Rebuild script, template, CSS, figure images, figure capture script. |
| `dashboard/dashboard.html` + 2 PNGs | The sample dashboard, safe to screen-share after the fix described in section 5. PNGs re-rendered 20 Oct. |
| `page_video/` | Sample builder page, video animatic and storyboard. No rendered MP4 exists yet. |
| `enrichment/`, `unit_costs/`, `employee/` | INTERNAL workstream files. Do not send. `enrichment/` names private individuals and shows phone endings. |

Rebuild after editing `prices.json`: `C:/ivtools/venv/Scripts/python.exe build_proposal.py` from this folder (about 1 to 2 minutes). Add `--html` for the HTML only, `--noviews` to skip the two HTML screenshots. The build stops and prints OVERFLOW if any page does not fit.

## 2. Defaults I applied (change if you disagree)

You had not decided these, so I used the safe choice. Each is easy to reverse.

1. **Lead with Option A**, the two-week pilot for 50 builders at Rs 35,000 + GST, fixed. Option C (research only, Rs 12,000) is shown as the lowest-risk alternative.
2. **Pilot gate is strict.** Zero genuine replies from owner-level messages means we recommend the research-only list or stopping, not the monthly run. "Delivered" now means delivered to owner-level numbers. Page 6 says plainly that this pilot mainly tests coverage, delivery and hand-off, not reply rate, and that a reply-rate read needs about 150 builders.
3. **Report on Day 17**, not Day 14: second messages go out on Days 10 to 13 and a 3-day reply window follows. The fee is still for the 14-day pilot.
4. **No private individual's name anywhere in the PDF** (`show_owner_names` is `false`). The record table shows roles only. Names exist only in `enrichment/`, which you do not send.
5. **Dee Vee and Biltech are LIKELY, not Verified.** The page headline is "4 likely", with the 95% range 30% to 90%, the note that two of the six are large groups, and "2 of 4" for small or medium builders.
6. **"Founder" is gone** from the PDF, the video frames, the storyboard and the page sample. Page 9 asks him to confirm his title. "20+ projects by 200+ people" is attributed to nexus360.in.
7. **The headline promise now matches the evidence:** research of the real owner, then WhatsApp where a business-published number exists. The PDF states 1 of 6 builders had a number wired for WhatsApp and 0 of 6 a verified direct owner number, and that a builder with no WhatsApp-capable published number is researched but not messaged (a person would phone it, outside the pilot). Measure 2 counts builders with a WhatsApp-capable published number.
8. **Meta wording.** I wrote "2 of 7 arrived on time. 3 failed: Meta refused 2 under a per-recipient marketing limit, 1 was undeliverable", not "3 were refused by Meta". The campaign diagnosis separates error 131049 (twice) from 131026 (once). "No replies" became "9 contacted, no confirmed genuine reply".
9. **Reply wording:** "No AI conversation with an owner: two fixed, approved messages go out; every reply goes to you." Button taps count as replies and are handed over. Replies on his own number (the page's "Book a demo on WhatsApp" button) are logged or forwarded by him and counted by hand. The PDF says the forward-only reply rule is not built yet and will be set up and tested before any send.
10. **Price page:** shared-risk alternative (Rs 30,000 + Rs 3,000 per demo held) promoted to a proper card beside the table, with the honest line that the monthly run is about 1.2 times one employee and not cheaper on cost alone. Page 8 says the monthly price is not firm yet and why (4.5 minutes of our time per builder assumed; a manual registry lookup can take 5 to 10).
11. **Pass-through:** pilot 100 to 150 messages if every builder had a WhatsApp-capable number (likely fewer), about Rs 30 to Rs 200, cap Rs 500. Monthly 300 to 450 messages, about Rs 90 to Rs 580, cap Rs 1,500. Alert templates are inside the cap.
12. **Terms I wrote:** payment 50% on approval and 50% at the Day 17 report (suggested); no credit of the pilot fee against month 1 (the pilot covers the set-up a run without a pilot would pay for); data export as CSV at the end and on request, either side can stop at any month end, retention agreed before Day 0. Employee row says "excludes travel, gratuity and leave".
13. **Contact route:** "IV Infotech, Mehsana, Gujarat. Reply on the WhatsApp chat you received this from." No phone number or email is in the PDF. An approved-by and date line is on page 10.
14. **Labels:** the 5 to 20 owner-level messages figure is tagged ASSUMPTION. The sample pipeline on page 4 uses 50 builders and is marked "Sample: invented numbers" in grey. DPDP bullet says "may fall outside the Act ... ask your own counsel".
15. **Dashboard builder table** (`dashboard.html`): already rebuilt before this pass so that only the four builders we really researched carry a result (Likely or Unknown, "Researched in test") and the other eleven read "Not researched". I kept those real test results rather than forcing every row to "Unknown", because Unknown for a Likely builder would contradict page 3. The "Chhattisgarh not tested" note is gone and the video label reads 17 seconds.
16. **Pages:** the PDF is 10 pages. Section badges are gone; the index on page 1 cites page numbers.

## 3. Decisions you still must make before sending

- Confirm the lead price and structure (A first). Rs 30,000 monthly is about 0.8 times one employee (Rs 36,900 all-in); this LOW-PRICE version is the owner-recommended one (see chat).
- Confirm hours and margin before quoting the monthly price (see section 4).
- First-touch channel and sender: WhatsApp template from IV Infotech's line (10 to 25 a day, STOP line, stop on a Meta warning), ideally on a separate +91 number. Alternative: first touch from his own number or a call to the office line.
- Build the forward-only reply rule for this account before the first send. Today a first inbound reply reaches our AI sales agent first.
- Whether to keep the correction on page 10 about the first pitch ("92+ staff hours", "Rs 23,000+ overhead saved") and the offer to ask MP RERA for permission (not promised).
- Whether to disclose "9 contacted, no confirmed genuine reply" (`show_campaign1_reply_count` in `prices.json`; "2 of 7 on time" stays).

## 4. Found in review

- **WhatsApp-reachability gap.** In the 6-builder test only 1 of 6 had a business-published number wired for WhatsApp, and 0 of 6 a verified direct owner number. The other routes were landlines, role inboxes, a sales line or a RERA-filed mobile. The pilot is WhatsApp-only, so most builders would be researched but not messaged. The PDF now says so on pages 1, 3, 6 and 10.
- **Tofler terms.** Director names for two builders came from Tofler, whose terms bar scraping and are non-commercial. Using it at scale needs a licence or API. The pilot does lookups by hand; the licence is not priced.
- **The Biltech link is an inference** (a shared address and name connect the partnership firm to the group company whose managing director was named). Dee Vee's director lists conflict with each other. Both are now LIKELY.
- **Dashboard table risk is fixed** (see default 15). Re-check it once on screen before a screen share.
- **Hours and margin conflict.** The price is built on Rs 1,000 an hour with 30% margin and 4.5 minutes of our time per builder. The comparison workstream used Rs 375 an hour (cost to serve about Rs 13,600 to Rs 21,400 a month), and the enrichment test says a manual registry lookup takes 5 to 10 minutes. At 9 minutes per builder and Rs 1,000 an hour, the monthly run costs about Rs 46,000 to serve, which is no margin on Rs 45,000. There may be room to lower the monthly fee if Rs 375 is right. The pilot still covers its cost (about Rs 57,900 at Rs 1,000 an hour against Rs 75,000).
- **BSP rates unknown.** Our provider's per-message rate, plan fee, markup and INR billing status are not known. Meta's INR rate (Rs 0.8631) comes from a news report.
- **Meta quality rating and business verification status unknown.** A restriction on the shared line is an unpriced risk. The proposal says "IV Infotech's line", not "verified".
- **Hindi lines have no native-speaker check.** Page and video wording is our draft.
- **No rendered video yet.** `page_video/` has an animatic and a storyboard. The PDF says "storyboard, not yet a rendered file". The storyboard file still shows its earlier placeholder styling; the PDF frames and `video_animatic.html` use amber placeholders.
- **"Founder"** is not on nexus360.in (the site names no individual). Your Sridhar file calls him a solo developer and acting CTO.
- **Earlier wording fixed:** the first version of these notes called Biltech a company. It is a partnership firm, and Sendh is a project company. The notes now say "firms".

## 5. Numbers and where to change them

In `prices.json`: pilot fee, builders, days, report day, touches, WhatsApp estimates and caps, message counts; monthly fee, builders, estimate range, cap, set-up if no pilot, shared-risk structure, price status text; research-only fees; GST rate; validity days; payment, credit and data-exit text; employee cost components (they must add up to the all-in figure or the build stops); pilot gate shares (40% owner coverage, 30% WhatsApp-capable, 60% delivery, 1 genuine reply); Meta per-message rates; display switches.

Fixed in the template or script: employee research cost per 100 builders (Rs 5,200 to Rs 14,000, from 15 to 40 minutes at Rs 210 an hour), pool sizes (424 and 798 promoters), "about 4 new builders a month", "up to about 21%" and "5 to 20 messages" on page 6, "10 to 25 a day", "about 7 days to first send", the weekly review, the sample message wording, the funnel counts (from `cg_rera_demo_summary.txt`; the pool recount differs by about 1% to 2%).

Not in the document on purpose: your hourly value, the 30% margin, cost to serve, per-builder AI cost, the illustrative conversation funnel, and our BSP unknowns.

## 6. What each page proves (and what it does not)

| Page | Proves | Does not prove |
|---|---|---|
| 1 Summary | You listened (every question has a page). The price is on page 1. The reachability gap is stated up front. | Anything about results. |
| 2 How it works | The process, who does what, the two fixed messages, and that his RERA point is partly right. | That every step is live today. Hand-off routing and "stop after a reply" are built for the pilot. |
| 3 Demo 1 | Register data is real and filterable (2,173 to 72). Six records of real research, with the 1-of-6 and 0-of-6 figures. | A hit rate (n = 6, not random). The 72 uses a stand-in size rule, and says so. |
| 4 Demo 2 | What he would watch. Layout of pipeline and lead card. How replies are handed over, including taps on his own number. | Real counts. All outreach numbers are invented and labelled. |
| 5 Demo 3 | Page and video can be made for Nexus360 from his public site. | That the Hindi is right, or that his recordings exist. |
| 6 Pilot | Strict rules agreed in advance. An honest channel and sample-size statement. | A reply-rate verdict. It will not give one (50 builders). |
| 7 Estimate | A clear number with arithmetic and GST, and a shared-risk option. | That it is cheap. |
| 8 Comparison | A fair comparison that does not hide that we are not cheaper. | That the system beats an employee. Unknown until measured. |
| 9 Timeline and needs | Relative days, who does what, what we need from him. | That Meta approvals will arrive on time. |
| 10 Limits and terms | Plain limits, compliance in short, terms, acceptance line. | Legal safety. It is a risk summary, not legal advice. |

## 7. Likely follow-up questions from Sridhar

1. **"Can you give me the owner's WhatsApp number for every builder?"** No. In our test of six, an owner or decision-maker was named for four (all Likely), a number wired for WhatsApp existed for one, and a verified direct owner number for none. Where there is no WhatsApp-capable published number the record comes to him for a phone call; that step is outside the pilot and was not tested.
2. **"Why is the monthly run more than hiring one person?"** It is, about 1.2 times. A person can talk to owners and the system cannot. The system starts in days, keeps a source and date for every fact, and can be stopped at any month end. That is why we suggest the pilot first (about two months of one employee), and the shared-risk option if cost is his main concern.
3. **"How many customers will this bring?"** We do not know. Our first campaign: 9 contacted, no confirmed genuine reply, too few to conclude. The pilot measures coverage, delivery and hand-off; a reply-rate read needs about 150 builders.
4. **"The WhatsApp account is yours. What if Meta blocks it, and what do I keep?"** The risk is ours, hence a separate +91 number and a pause on any Meta warning. Records and logs are exported to him as CSV at the end and on request.
5. **"Can you do Madhya Pradesh too?"** Not automated. MP RERA's robots.txt disallows bots. We could ask for permission or build a list by hand later. Neither is promised or priced.

## 8. Demo files: what to check before you share them

- `dashboard/dashboard.html`: scroll to the builder table once and confirm only four rows carry a result. The funnel middle counts (146, 135, 131) differ slightly from a replay of the saved list (151, 140, 136); I used `cg_rera_demo_summary.txt`.
- `page_video/builder_page_sample.html` (add `?builder=Sample+Builders&project=Sample+Heights&city=Durg`) and `video_animatic.html` are fine to screen-share. Amber boxes are placeholders for his recordings.
- Page and video text for a real send needs a native Hindi check and his recordings.

## 9. Open gaps (not mine to fill)

- Our BSP (Fortius) per-message rate, plan fee and INR billing status (deadline 31 Dec 2026). Meta's own INR rate card (a news report was used).
- Whether you price and run the AI work on an API key or a personal subscription for a paid client service.
- The cost workstream said a video render takes 5 minutes; the page and video workstream measured about 40 seconds. No render time is in the document.
- His own numbers (first-year value of a customer, demos per month by source) are not known. They decide whether any option is worth it.
