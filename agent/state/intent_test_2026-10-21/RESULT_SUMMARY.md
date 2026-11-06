# Intent-lead prompt v1 test, 21 Oct 2026 (Claude tools, not Gemini)

Run: workflow wf_21f6c8cc-9b6. 8 agents, ~785k tokens, 190 tool calls, ~10 min. Read-only: nobody contacted, nothing sent. Full raw output: `workflow_full_output.json` (this folder, git-ignored).

## Hit rate (queries -> candidates -> verified -> survived)
| Angle | Queries | Found | Result |
|---|---|---|---|
| Explicit asks, English | 17 | 0 | Only CRM / WhatsApp-automation vendors came up; no builder posts readable |
| Explicit asks, Hindi/Hinglish/Gujarati | 22 | 0 | Phrases matched nothing; Facebook/YouTube/Instagram not readable without login |
| Hiring signals | 13 | 1 | Only angle that gave a dated, checkable signal (logged-out LinkedIn jobs page, past-2-weeks filter) |
| Meta ads + new RERA launches | 18 | 0 | Meta Ad Library unreachable (JS) and Apify blocked -> NOT tested, tooling gap |
| Complaints + owner voice | 26 | 0 | Only dated thread (Oculus Infra) was a year old and about defects |
Total: ~96 queries, 1 candidate, 0 verified owners, 0 people asking for it themselves.

## The one survivor: Satyamev Group (Ahmedabad / Gandhinagar)
- Signal: two LinkedIn sales jobs ("Real Estate Salesperson", "Sales And Marketing Specialist"), posted ~18 Oct 2026 ("3 days ago", relative date). Duties: manage leads, follow up enquiries, site visits.
- Qualifier B; skeptic could not refute but regraded to C+ (low B at best): hiring shows staffing intent, not missed enquiries; no pain observed; WhatsApp use unknown; owner not verified (LinkedIn poster label "Yash Patel, Managing Director" is self-entered and soft; qualifier thought Vijay Naranbhai Patel the best-supported principal, title not stated).
- Contact (business-published): website satyamevgroup.com homepage shows two phones and emails (sales.satyamev@gmail.com, vijay@satyamevgroup.com). No WhatsApp link. Only clean route = email to the company-domain address, "Hi team", no personal name or title, no WhatsApp assumption, no missed-enquiry claim. NOT sent; needs owner approval.
- Near misses (hiring, owner not verifiable): Vistara, VR Ahmedabad, TDS Properties, Sankalp. Names to check on Meta Ad Library: Aadi Makers, Tirupati Construction, Kailash Corporation, Sahaj Buildcon, Raghuvir Buildcon, Hrishikesh Ventures, Bhumika Buildcon, Auracle (Ue Living LLP, RERA 16 Sep 2026), Satyamev.

## Judge verdict
- Bad result, said plainly. Explicit-ask leads are NOT publicly findable in useful numbers: builders do not post "I need WhatsApp automation" in indexable text; that talk is in private WhatsApp groups and logged-in Facebook groups. Does not prove the prompt fails in Gemini Deep Research (deeper Google index), but Gemini could add 0-2 explicit leads at best and each needs re-checking.
- Only trigger signals (hiring, Meta WhatsApp-CTA ads, new RERA registration) can be found and dated; they show likely need, not a request, so expect low reply rates. Benchmark: campaign 1 = 0 replies from 9.
- Gujarat builders are pitched CRMs constantly by local vendors (Makanify, BrokerDost, Codingclave, Realatic, Rynow, VSCRM, DaeBuild). Do not lead with "CRM"; lead with the first WhatsApp reply and site-visit slot.
- BLOCKED: Apify (both connectors) "Monthly usage hard limit exceeded"; Meta Ad Library; reddit, MouthShut (403), DuckDuckGo (CAPTCHA, not bypassed), Facebook/Instagram/YouTube post text, LinkedIn profiles (999), official GujRERA JS portal. REACHED: logged-out LinkedIn public jobs pages (best), consumercomplaints.in, single-project pages on gujrera.com.
- Useful trick: GujRERA numbers end in DDMMYY = approval date (MAA17359/160926 = 16 Sep 2026), numbers above ~17400 are Oct 2026 launches.

## Prompt v2 edits recommended
1. Demote explicit asks to a footnote ("return 0 if none"); main angles = hiring, Meta Ad Library WhatsApp-CTA ads, new RERA registrations.
2. Hard exclude CRM / AI-calling / WhatsApp-automation vendors and agencies; name the known Gujarat ones.
3. Every signal needs a verbatim quote, URL and a date on the page; undated job-board listings (Weekday, TeamLease) = context only; LinkedIn "N days ago" accepted with the fetch date stated.
4. "0 leads in a section is acceptable"; add a "sources I could not access" field; no padding from snippets.
5. Owner rule: VERIFIED needs 2 independent sources; if only a poster label exists, mark UNVERIFIED and use a company-published contact with a "Hi team" opener.
6. RERA number optional (official portal not machine-readable); add the DDMMYY trick.
7. Two steps: (1) discover builders, (2) enrich owner + contact. Tier A needs stacked signals (e.g. hiring ad + active WhatsApp/Send-message ad). Hiring alone capped at B/C; add `pain_observed` yes/no.
8. Opening lines must not assume WhatsApp is the channel; ask how after-hours and portal enquiries get a first reply. Widen hiring sweep to Surat, Rajkot, Vadodara, Gandhinagar, Anand, Bhavnagar, Mehsana; add Naukri/Indeed company pages.

## Recommended next steps (none started)
1. Read-only, no-login Meta Ad Library check in the browser pane (or Apify once quota returns) for the names above: strongest untested signal.
2. Re-run (v2) in Gemini Deep Research when its quota resets, as a real A/B; re-check every item.
3. Enrich the 4 hiring near misses (website + owner).
4. Optional cheap test: one short email to Satyamev's company-published address (needs owner approval); log as a low-intent hiring test.
