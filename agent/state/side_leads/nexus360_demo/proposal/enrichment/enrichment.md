# Finding the real owner: enrichment test on 6 Chhattisgarh builders

Test date: Tue 20 Oct 2026 (IST), 11:31 to 11:54 on the machine clock.
Side lead: Nexus360 / GreyBoard Consulting. Kept apart from campaign 1.
Status: research only. Nothing was sent to any builder or to Sridhar. No login, no CAPTCHA, no sign-up.

How to read this file
- [FACT] = seen on a cited page on 20 Oct 2026.
- [INFERENCE] = my reading of facts. Could be wrong.
- [OPINION] = a recommendation.
- [ASSUMPTION] = a number with no source; always given as a range.
- Masking: phones show the last 4 digits only, emails show the domain only. Full values exist only in a local scratch file, never here.
- Section 5 is written so it can be shown to Sridhar as "sample enriched records". Everything else is internal.

---

## 1. Bottom line

1. [FACT] Sridhar is right that the RERA contact is often not the owner, but the register gives more than we kept. The public Chhattisgarh RERA list already carries an "Authorised Name" per project, and each project's detail page carries the promoter type, registered address, a mobile number, an email and the filed project cost. Our earlier script threw all of that away on purpose (no contact data).
2. [FACT] In this test of 6 builders, I could name a likely or verified owner/decision-maker for 4 (2 VERIFIED, 2 LIKELY) and not for 2 (UNKNOWN). Only 1 of 6 had a business-published contact addressed to a named person. None had a verified direct WhatsApp number for the owner.
3. [FACT] Who the RERA contact is, across the 6: owner-level on evidence in 1 (Biltech: the authorised person is the managing director of the group company); a salaried-officer type in 2 (Dee Vee, Sendh: not on the director lists); the individual promoter himself in 2 (Bhaiya, Dulani) but with a filed Gmail address whose name does not match him [INFERENCE: a consultant, relative or another firm filed it]; relation unknown in 1 (Balajee, also a non-matching Gmail address).
4. [FACT] Our "small or medium" proxy (3 or fewer registered projects) is weak. Of the 6, Dee Vee describes itself as a 3,000+ person infrastructure contractor (its own claim) with a project filed at about Rs 1,226 crore, and Sendh is a 124-acre township whose directors also run the PRA highway companies. The RERA project cost is a much better size signal, and it is free on the same detail page.
5. [FACT] One real business can appear under several promoter names: the R.K. Group in Dongargarh shows up as an LLP and two individuals. 4 of the top 20 on our list have an authorised person who also fronts other promoter names. A "group resolution" step is needed or we will count one builder two or three times.
6. [OPINION] Enrichment is worth doing, but the honest promise to Sridhar is: "we name the owner or decision-maker where public evidence supports it, say UNKNOWN where it does not, and route to the business-published channel plus a human step", not "we give you the owner's WhatsApp number".
7. [FACT] n = 6 is only indicative. The 95% interval for 4 of 6 is 30% to 90%.

---

## 2. What was tested and how

Sample: 6 builders chosen from the top 20 of `cg_rera_demo_ranked.csv` (rank in brackets) for different profiles, skipping government bodies:

| # | Builder as registered (rank) | Profile chosen |
|---|---|---|
| E1 | Dee Vee Projects Limited (7) | listed-looking company with a corporate website |
| E2 | Sendh Integrated Project Private Limited (8) | company with a project website, part of a group |
| E3 | Biltech Estates (6) | partnership firm with project site and group site |
| E4 | Arun Kumaar Bhaiya, R.K. Greens-A (2) | individual promoter with a family business website |
| E5 | Shri Balajee Real Infrabuild Private Limited (1) | brand-new company, no website |
| E6 | Ravi Dulani, Samruddhi (4) | individual promoter, no website |

Method, in order: (1) the register list and one detail page per builder; (2) the builder's own website, rendered in a real browser engine because 2 sites are JavaScript apps; (3) company-register aggregator pages for directors; (4) web search; (5) Meta Ad Library keyword search; (6) one search for a CREDAI member list.

Requests made (politeness): 1 register list GET (11 MB), 6 register detail postbacks 8 seconds apart plus 6 detail GETs, about 25 builder-site page loads, about 30 web searches, 3 Tofler page views (plus one search URL that returned 404), 1 companydetails.in view, 3 Meta Ad Library queries. No parallel crawling. The register site has no robots.txt (HTTP 404) [FACT]. Its terms were not read.

Time-box: 10 minutes per builder. Measured on the machine clock, including agent thinking time:

| Builder | Minutes | Source that did the work |
|---|---|---|
| E1 Dee Vee | about 7 (incl. setup of the browser-render helper) | builder's own site via in-site menu ("Director's Desk"), plus one stale aggregator list |
| E2 Sendh | about 3 | register address -> group name -> Tofler director pages |
| E3 Biltech | about 2.5 | project site footer link -> group site -> Tofler MD listing |
| E4 R.K. Group | about 1.5 | own site + register rows that share RERA numbers with the site |
| E5 Balajee | about 1.5 | nothing reached an owner |
| E6 Dulani | about 2 | nothing reached an owner |

Register setup (list plus 6 detail pages) took about 5 minutes once, shared by all six. Whole test about 22 minutes. [ASSUMPTION] A person doing the same lookups by hand would need roughly 15 to 40 minutes per builder; no human timing was taken. Tokens were not metered per builder.

---

## 3. Hit-rate estimate (indicative, n = 6)

Definitions:
- VERIFIED: name and role confirmed by the business's own page or an official register, plus a second independent source.
- LIKELY: one good source, or two weak ones that agree, and the role is partly inferred.
- UNKNOWN: no usable evidence.
- "Business-published" means the business itself printed the contact on its own page or ad.

| Rung | Count | Share | 95% interval (Wilson) |
|---|---|---|---|
| Owner or decision-maker named with evidence (VERIFIED + LIKELY) | 4 of 6 | 67% | 30% to 90% |
| ...of which VERIFIED | 2 of 6 | 33% | 10% to 70% |
| Named AND a business-published company channel exists (landline, sales line, role inbox) | 4 of 6 | 67% | 30% to 90% |
| Named AND a business-published channel addressed to that person (named mailbox) | 1 of 6 | 17% | 3% to 56% |
| A business-published number labelled or wired for WhatsApp (enquiry desk, not the owner) | 1 of 6 | 17% | 3% to 56% |
| A verified direct WhatsApp number for the owner | 0 of 6 | 0% | 0% to 39% |

What "real owner identified with a business-published contact" means in practice: [OPINION] count the 1 of 6 (named person with a personal business mailbox) as the strict hit, and the 4 of 6 as the realistic "we know who to ask for and a business channel to ask on".

Comparison with Gujarat (campaign 1, round 2): an owner or decision-maker was named for 6 of 9 contacted leads (67%, interval 35% to 88%) [FACT, from the task brief]. The ratios look the same (67% vs 67%), but they must not be treated as equal evidence: the Gujarat leads were picked because they ran ads and had a website and email route, this sample is the newest RERA registrations, and the Gujarat count was "named", not "named plus published channel". Gujarat also found a business email for only 7 of 159 fresh GujRERA promoters (4%) [FACT, CAMPAIGN_LEARNINGS section 2]. Here 3 of 6 register emails were on a business domain, but that is a different measure and n = 6.

[OPINION] Plan on roughly half to two-thirds of shortlisted builders getting an owner name, about a third of those being VERIFIED, and a small minority having a person-specific published contact. Do not promise more.

---

## 4. What the register itself gives (the missing first step)

[FACT] List page columns (rera.cgstate.gov.in/Approved_project_List.aspx): Project, Registration No, Authorised Name, Promoter Name, type, district, tehsil, dates, website, certificate, a Details button.
[FACT] Detail page (opened by a postback; the server answers with a redirect to `Promoter_Reg_Only_View_Application_new.aspx?MyID=...`): authorised person, promoter name, promoter type (Individual, Company, Partnership Firm...), registered address, promoter mobile and email, project address, estimated construction cost and land cost, inventory.
[FACT] The postback needs the full 11 MB list page's form fields (about 2.5 MB per request) and the answer is 90 KB to 900 KB. Polite pace used: one project per about 13 seconds.

Facts about the top 20 (computed from the saved list, 20 rows only; the CSV keeps 20 of the 72):
- 15 of 20 promoters look like entities (Pvt Ltd, firm, LLP) and 5 look like individuals [heuristic on the name].
- 11 of 20 list a website on the register.
- In 17 of 20 the authorised name differs from the promoter name (spelling variants count), as expected when the promoter is an entity.
- 4 of 20 (Maha Ganpati, Dee Vee, Silver Developers, Harshit Singhania Buildcon) have an authorised person who also appears under other promoter names in the register (for example one person fronts four Singhania entities).

Filed project cost, from the six detail pages (Rs crore, "estimated cost of construction/development"; the promoter's own filing):

| Builder | Cost |
|---|---|
| Dee Vee (31 Marina) | 1,225.8 |
| Sendh Lake City Phase III | 88.8 |
| Shri Balajee (Rivera) | 49.0 |
| Biltech Estates (Surya Ananya Ph II) | 3.9 |
| Ravi Dulani (Samruddhi) | 0.9 |
| R.K. Greens-A | 0.2 |

[OPINION] Use this cost plus group size instead of "3 or fewer projects" to define small and medium. It is free, per project and machine-readable.

---

## 5. SAMPLE ENRICHED RECORDS (6) - safe to show Sridhar

All records were built from public pages on 20 Oct 2026. Phones show the last 4 digits only. Emails show the domain only. Confidence uses the labels VERIFIED / LIKELY / UNKNOWN defined in section 3. "RERA contact" means the person, phone and email filed on the Chhattisgarh RERA project page.

### E1. Dee Vee Projects Limited, Raipur (project: 31 Marina by Deevee)

| Field | Value |
|---|---|
| Register | Reg no PCGRERA010926002151, mixed development, Mandir Hasaud (Raipur), approved 1 Sep 2026. Filed cost about Rs 1,226 crore. Promoter type: Company. |
| Profile | Own site: construction and infrastructure group since 1989, 13 states, 3,000+ team, "Rs 1000+ crore turnover" (company's own claims). Realty is one of three verticals (flagship residential "Evaraa"). Not a small builder. |
| RERA contact | Authorised person: Manas K M Agrawal. Mobile ending 9000. Email on the company domain (dvplindia.in), a personal-style mailbox. |
| Role of the RERA contact | Authorised officer or operator, not shown as a director [INFERENCE: his name is not on either director list found]. |
| Real owner / decision-maker | Dinesh Kumar Patel, signing the "Director's Desk" message as "on behalf of all Promoter's & Whole-Time Director's"; the company says it began in 1989 as M/S Patel Enterprises founded by Shri Nanji Bhai Patel. |
| Confidence | VERIFIED (company's own page + a director listing that names Dinesh Kumar Patel and Nanji Bhai Patel). |
| Business-published contacts | Head-office landlines ending 2580 and 5431; role inbox at dvplindia.in (published on the site footer). Both are company lines. No direct number or WhatsApp for the promoters. |
| Route to the owner | Company switchboard or role inbox, asking for the promoter office or the realty division head. [OPINION] Likely a corporate procurement setup, so not a quick-decision lead. |
| Evidence | Register detail: https://rera.cgstate.gov.in/Promoter_Reg_Only_View_Application_new.aspx?MyID=MjY1Ng== ; own site (open the menu "Our Journey" then "Director's Desk"): https://dvplindia.in/ ; director listing (stale, last AGM shown 2016): https://www.companydetails.in/company/dee-vee-projects-limited |
| Notes | Aggregator director lists conflict with each other (one set from 2012 to 2019, another naming whole-time directors with different names), so only the company's own page is used for the owner label. Registered office is in Korba, head office in Raipur. |
| Checked | 20 Oct 2026. Time about 7 min. |

### E2. Sendh Integrated Project Private Limited, Raipur (Sendh Lake City, Phases I to III)

| Field | Value |
|---|---|
| Register | Three registrations (Phase I, II, III; PCGRERA250826002144 is Phase III), Group Housing, Mandir Hasaud. Filed cost of Phase III about Rs 88.8 crore. Company incorporated 24 Mar 2025, paid-up capital Rs 1 lakh (a project company). |
| Profile | Project site: 124-acre lifestyle township at Naya Raipur sectors 4 and 10, private villas, club, "JW Marriott Resort". Registered address is "PRA House" near Udyog Bhawan, Telibandha, Raipur, which search results also give as the address of PRA India Pvt Ltd, a road and highway company. Not small. |
| RERA contact | Authorised person: Rupesh Meghani. Mobile ending 1100. Email on the group domain praindia.in (a project-named mailbox; that domain's own web page is a parked page, mail is hosted on Google). |
| Role of the RERA contact | Officer or operator, not a director [INFERENCE: not on the director list]. |
| Real owner / decision-maker | Directors of the project company: Shrawan Agrawal and Ayush Agrawal. Ayush Agrawal is also a director of PRA India Pvt Ltd and several PRA-named highway companies. The group appears to be the PRA (road and highway) family. |
| Confidence | LIKELY (the registry-derived listing is one source family; role of each director in day-to-day sales not stated). |
| Business-published contacts | Project sales line on the site, ending 2000 (an enquiry line for invitation requests). No named person's contact. |
| Route to the owner | Sales line first; the group is big enough that the real buyer may be a project head. Owner direct contact: none published. |
| Evidence | Register detail: https://rera.cgstate.gov.in/Promoter_Reg_Only_View_Application_new.aspx?MyID=MjYyMg== ; project site: https://sendhlakecity.com/ ; directors (data shown as updated 7 Oct 2026): https://www.tofler.in/sendh-integrated-project-private-limited/company/U68100CT2025PTC017676 ; one director's company list: https://tofler.in/ayush-agrawal/director/03601777 |
| Notes | Meta Ad Library keyword "Sendh Lake City" returned only ads by the Nava Raipur development authority about the lake, nothing by the developer. |
| Checked | 20 Oct 2026. Time about 3 min. |

### E3. Biltech Estates, Bhilai (project: Surya Ananya Phase II)

| Field | Value |
|---|---|
| Register | Reg no PCGRERA170926002154, plotted development, Durg. Promoter type: Partnership Firm. Filed cost about Rs 3.9 crore. |
| Profile | Established Bhilai developer; group site lists Surya Ananya (Bhilai) and Prakriti Estate (Raipur) and its legal group company "Biltech Engineers Private Limited". Same address as the registry listing: 4th floor, Surya Treasure Island Mall, Junwani, Bhilai. |
| RERA contact | Authorised person: Manish Gupta. Mobile ending 2031. Email on the firm's own domain (biltechestates.com; the domain serves a default web page but has mail set up). |
| Role of the RERA contact | Owner-level: the register's authorised person matches the Managing Director of Biltech Engineers Pvt Ltd in the registry-derived listing. |
| Real owner / decision-maker | Manish Gupta, Managing Director. Other directors listed: Kuldip Kumar Gupta, Vijay Kumar Gupta, Anil Kumar, Rajnish Gupta, Shivani Gupta (whole-time). |
| Confidence | VERIFIED for the person and role at the group company (register + registry listing dated 3 Aug 2026). The firm's own partner list was not seen, so the link "Biltech Estates = same family" rests on shared address and name [INFERENCE]. |
| Business-published contacts | Project site: "Headquarters" phone ending 9775 and a role inbox at biltech.co.in. Group site: landline ending 0200, mobile ending 0830, role inbox "marketing" at biltech.co.in. Both sites carry a WhatsApp chat widget (the group site's button reads "Enquire Now") wired to the number ending 9775 [FACT from the page code]. These are sales and enquiry lines, not the MD's own line. |
| Route to the owner | WhatsApp or call the published enquiry line and ask for the Managing Director's office; the RERA mobile ending 2031 is probably his or his office's [INFERENCE]. |
| Evidence | Register detail: https://rera.cgstate.gov.in/Promoter_Reg_Only_View_Application_new.aspx?MyID=MjYwMA== ; project site: https://suryaananya.com/ ; group site: https://biltech.co.in/ ; directors (updated 3 Aug 2026): https://www.tofler.in/biltech-engineers-private-limited/company/U74210CT1984PTC002406 |
| Notes | The group site's About and Contact pages contain unrelated gambling-site text mixed into the headings (likely injected content); I did not use that text as evidence. |
| Checked | 20 Oct 2026. Time about 2.5 min. |

### E4. R.K. Group, Dongargarh (promoter names: Arun Kumaar Bhaiya, Pavan Bhaiya, Ganga Structure LLP)

| Field | Value |
|---|---|
| Register | R.K. Greens-A (Arun Kumaar Bhaiya, PCGRERA071026002164) and R.K. Greens-P (Pavan Bhaiya, PCGRERA011026002162), Dongargarh, approved Oct 2026, both individuals; filed cost of Greens-A about Rs 0.2 crore. Earlier R.K. Sharanam phases (2025) are registered to Ganga Structure LLP with authorised person Shreyas Bhaiya. |
| Profile | One family business under three promoter names. Own site says "R.K. Group ... among the most renowned builders of Dongargarh", 13+ years, office near the bus stand on Khairagarh Road. Site lists RERA numbers that match the LLP's registrations. |
| RERA contact | For Greens-A: authorised person Arun Kumar Bhaiya, mobile ending 1101, email on Gmail whose name resembles an accounting or company-secretary practice, not a person. The registered address of this individual promoter is in Nagpur. |
| Role of the RERA contact | Promoter himself, but the filed email looks like an adviser's mailbox [INFERENCE]. |
| Real owner / decision-maker | Shreyas Bhaiya (authorised person of the LLP and the name on the website's business mailbox), with Arun Kumaar and Pavan Bhaiya as co-promoters; same surname, so probably family [INFERENCE]. |
| Confidence | LIKELY. |
| Business-published contacts | Site footer: a mailbox on bhaiyas.com named after the same first name (named-person inbox) and a phone ending 6768 (office line). |
| Route to the owner | Email the named mailbox or call the office line. This is the only one of the six with a person-specific business-published contact. |
| Evidence | Register detail: https://rera.cgstate.gov.in/Promoter_Reg_Only_View_Application_new.aspx?MyID=MjY2OA== ; own site: https://www.bhaiyas.com/ and https://www.bhaiyas.com/project.html ; register list (rows for R.K. Sharanam, Greens-A, Greens-P): https://rera.cgstate.gov.in/Approved_project_List.aspx |
| Notes | Without group resolution this business would be counted as three leads. The LLP's partner list could not be found. |
| Checked | 20 Oct 2026. Time about 1.5 min. |

### E5. Shri Balajee Real Infrabuild Private Limited, Raipur (project: Rivera, Naya Raipur)

| Field | Value |
|---|---|
| Register | Reg no PCGRERA071026002163, group housing, approved 7 Oct 2026, 99 units, filed cost about Rs 49.0 crore. Promoter type: Company. |
| Profile | New company; no website; no Meta ads found for "Shri Rivera Raipur". Registered address is "c/o Sri Tirumala Realbuild", Capital Square Complex, Lalpur, Raipur. |
| RERA contact | Authorised person: Rishi Agrawal. Mobile ending 7000. Email on Gmail with a name unlike the authorised person's. |
| Role of the RERA contact | Unknown. |
| Real owner / decision-maker | Not found. Lead only: a Raipur LLP called Sri Tirumala Realbuild exists (reported by one aggregator that refused my automated fetch, so unverified); the c/o address suggests a link, which is not established. |
| Confidence | UNKNOWN. |
| Business-published contacts | None found. |
| Route to the owner | Human lane: a person checks the LLP and the company on the official registry, or phones the number filed with RERA to ask who handles the project's software and purchasing. |
| Evidence | Register detail: https://rera.cgstate.gov.in/Promoter_Reg_Only_View_Application_new.aspx?MyID=MjY3MA== |
| Notes | No registry listing for the company was found on the indexed aggregators; it may be too new or listed under a variant name. |
| Checked | 20 Oct 2026. Time about 1.5 min. |

### E6. Ravi Dulani, Rajnandgaon (project: Samruddhi)

| Field | Value |
|---|---|
| Register | Reg no PCGRERA210926002156, residential plotted development, Rajnandgaon, approved 21 Sep 2026, filed cost about Rs 0.9 crore. Promoter type: Individual. |
| Profile | Small individual promoter. No website; no Meta ads found for "Samruddhi Rajnandgaon"; no web trace in English or Hindi search. |
| RERA contact | Authorised person is the promoter himself. Mobile ending 1887. Email on Gmail in the name of a different builder firm. |
| Role of the RERA contact | The promoter, but the filed email belongs to another firm or person [INFERENCE]. |
| Real owner / decision-maker | The promoter is the individual on the register; nobody else was found. |
| Confidence | UNKNOWN (for any owner beyond the promoter's own name; the register gives only a number and email whose ownership is unclear). |
| Business-published contacts | None. |
| Route to the owner | Human lane only. |
| Evidence | Register detail: https://rera.cgstate.gov.in/Promoter_Reg_Only_View_Application_new.aspx?MyID=MjYzNw== |
| Notes | Typical of the small end of the register: the register is the only public source. |
| Checked | 20 Oct 2026. Time about 2 min. |

---

## 6. Recommended enrichment pipeline

A = automated, H = needs a human. Time figures are from this test, not guarantees.

| Step | What | A/H | Notes from the test |
|---|---|---|---|
| 0 | Shortlist from the register list (script exists) | A | Replace "3 or fewer projects" with filed project cost and group size (section 4) |
| 1 | Pull each shortlisted project's detail page | A | Authorised name, promoter type, address, cost, RERA phone/email. 1 project per about 13 s, so 72 builders take about 16 min [ASSUMPTION: extrapolated]. Read the site's terms first |
| 2 | Group resolution | A | Cluster by authorised name, email domain, address, brand token; count projects per group. Needed for E2, E4 and 4 of the top 20 |
| 3 | Website and contact discovery | A | Render JavaScript sites; follow the menu to About, Director's Desk, Contact; read footers, "Know your builder" links, WhatsApp widget settings. 4 of 6 had a site; 2 of those named people |
| 4 | Company and LLP directors | H or licensed API | Worked for E2 and E3 only. Automated scraping of aggregators is not allowed (section 7) |
| 5 | Evidence scoring | A proposes, H confirms | Rule-based label with a quote under 15 words and a URL per fact. Reopen every web-search summary at its source: two of my searches returned wrong or empty summaries for pages that exist |
| 6 | Role of the RERA contact | A | Compare authorised name with directors: owner / officer / consultant / unknown |
| 7 | Choose the contact route | A+H | Preference order: business-published WhatsApp enquiry number, named business mailbox, role inbox, office landline. Never a personal number from a third party |
| 8 | Optional human call to the published office line | H | Not tested. Ask who looks after indents and purchasing software |
| 9 | Verification gate (section 10) | H | Nothing is sent without it |

Expected yield for 72 shortlisted builders [ASSUMPTION from n = 6]: owner named 22 to 65 (30% to 90%), of which VERIFIED 7 to 50 (10% to 70%), person-specific business contact 2 to 40 (3% to 56%). Wide on purpose.

Effort inputs for the estimate [ASSUMPTION]: automated steps 1 to 3 about 2 to 4 minutes of agent time per builder (this test: 1.5 to 7); human registry lookup and review about 5 to 10 minutes per builder; no paid data source was used, and a licensed registry API was not priced.

What to put in front of a human first: the UNKNOWN and LIKELY records, and every VERIFIED record before its first message.

---

## 7. Sources: use, use manually, or avoid

| Source | Verdict | Why (evidence) |
|---|---|---|
| Chhattisgarh RERA register (list and detail pages) | Use, throttled | Official and public; no robots.txt (404); heavy postbacks. Terms not read |
| Builder's own website | Use | Business-published; highest quality. Render in a browser engine |
| Meta Ad Library keyword search | Use sparingly | Public, no login; 3 queries here gave nothing useful (noisy or empty) |
| Tofler | Manual single lookups only | Terms: "does not allow You to use crawlers, spiders or other scraping technology"; dataset is non-commercial (CC-BY-NC); an API is offered. I used 3 page views for this evaluation. Buy API or licence before production |
| Zauba Corp, thecompanycheck, filesure, planetexim, 99acres | Manual only | Returned HTTP 403 to automated fetches; I did not try to get around it. Zauba terms page also 403 |
| MCA portal, GST public search | Human step | Free official data, but I did not test them; they normally need a CAPTCHA, and we do not bypass CAPTCHAs [ASSUMPTION about the CAPTCHA] |
| LinkedIn | Do not automate | User Agreement 8.2 item 2 (scripts, robots) and item 13 (bots or other unauthorised automated methods). A person may look, nothing is harvested |
| Google Business / Maps | Manual or official paid API | Not tested here; scraping terms not checked |
| Facebook / Instagram pages | Manual view | Not tested; no login allowed in this task |
| CREDAI Chhattisgarh | Not available | One search found no public member directory (likely members-only) |
| Leaked lists, bought phone lists, caller-ID apps | Never | Third-party personal data; outside the legal-obligation or self-publication classes below |

---

## 8. Personal data (India DPDP Act 2023): risk summary, not legal advice

- Owner names, mobiles and mailboxes of identifiable people are personal data.
- [FACT] Section 3(c)(ii) says the Act does not apply to personal data made or caused to be made publicly available (A) by the person it relates to, or (B) by someone obliged by law to publish it (text from the unofficial copy at https://dpdpa.com/dpdpa2023/chapter-1/section3.html). A number printed on the builder's own site or ad, or an entry in the RERA register, plausibly falls inside it [INFERENCE]. A number found in a third-party listing, a social post by someone else or a bought list does not.
- [FACT, secondary sources] The DPDP Rules were notified in Nov 2025; most duties (notice, security, breach, rights) start 18 months later, around 13 to 14 May 2027, so they are not yet in force on 20 Oct 2026. Sources: https://www.mondaq.com/india/data-protection/1708164/digital-personal-data-protection-rules-2025-notified and https://www.storyboard18.com/amp/digital/breaking-govt-notifies-final-dpdp-rules-sets-staggered-rollout-with-key-obligations-for-data-fiduciaries-84201.htm . Confirm the exact date with counsel.
- [FACT] The bigger near-term constraint is WhatsApp's own rule: businesses may contact people only if the person shared their number and gave opt-in permission (WhatsApp Business Messaging Policy, section 1, https://whatsappbusiness.com/policy/). A cold template to a builder's published number is a policy risk regardless of DPDP; our own campaign delivered 2 of 7 cold templates.
- Calls and SMS fall under separate telecom commercial-communication rules; not checked here.
- [OPINION] Safe practice: store only what the business published, with source URL and date on every field; keep full numbers and emails in a restricted store and masked everywhere else; honour STOP on every channel; set a deletion date for unverified contact data; do not store family or home-address details (the register shows home addresses of individual promoters, which I did not copy into the records).

---

## 9. Record format kept per builder

| Field | Meaning |
|---|---|
| builder_id, group_id, group_members | Internal ids; promoter names that belong to one business |
| register_refs | Registration numbers and the detail-page URL |
| promoter_type, district, size_signal | Individual / Company / Firm / LLP; filed cost; group project count; own-site team size if stated |
| register_contact | authorised_name; phone_last4; email_domain; email_class (personal-style / role / consultant-style / unknown) |
| rera_contact_role | owner / officer / consultant / unknown, with the basis |
| owner_candidates[] | name; role; basis; evidence_url; quote (under 15 words); source_type (own site / registry-derived / news); as_of_date |
| owner_confidence | VERIFIED / LIKELY / UNKNOWN |
| published_contacts[] | channel; value_masked; class (enquiry line / office landline / role inbox / named-person inbox); published_by (business); page_url; observed_on; whatsapp_wired (yes/no/unknown); mx_ok (emails) |
| route_to_owner | direct / via company line / none |
| first_seen, last_verified, verified_by, next_check | Dates and the person who checked (internal id only) |
| status | new / verified / parked-human-lane / suppressed |
| suppression, stop_flag | Set if the person asked to stop |

Full values (numbers, mailboxes) live only in the restricted store, never in reports.

---

## 10. Verification gate before any message is sent

All must be true; a human ticks them.
1. Name and role have two independent sources, or the label is VERIFIED. LIKELY records need one more check; UNKNOWN is never messaged by name.
2. The evidence is not older than 30 days [OPINION: 30 days]. Directors and mobiles change.
3. The channel was published by the business itself (own site, ad, register). Class recorded. For email, MX checked. For WhatsApp, the number is wired or labelled for WhatsApp, or the first touch is not WhatsApp.
4. The opt-in position is recorded (WhatsApp policy section 1). If there is none, the first contact is not a cold WhatsApp template.
5. Suppression list and STOP list checked.
6. The wording claims nothing beyond the record: no "as the owner of X" unless VERIFIED; no figures from the builder's own marketing unless quoted and labelled.
7. A person has opened at least the top evidence URL for this record today.
8. The message carries an opt-out line and the sender identity.

---

## 11. Limits, and what to avoid telling Sridhar

- n = 6, chosen for variety, not at random, from the newest registrations. The rate is not a forecast.
- Owner names came largely from registry-derived aggregator pages, which can be stale (E1's lists disagree). The company's own page was preferred.
- Not tested: MCA portal, GST search, Google Business, Facebook/Instagram pages, a human call, and any paid registry API.
- Web-search summaries were unreliable at times (empty, or wrongly saying a page did not exist); every fact above was re-read at its source page except the Sri Tirumala Realbuild LLP lead (unverified).
- Do not tell Sridhar: that RERA alone finds owners, that we will supply owners' WhatsApp numbers, that Madhya Pradesh is automated, or any hit-rate as a promise.
- Safe to tell him: the register gives an authorised name and a filed contact that is often an officer or adviser; we reach for the owner by resolving the business group, reading the builder's own pages, and checking company records; where public evidence is thin the record says UNKNOWN and goes to a human; every record shows its sources and date; nothing is sent before a person has checked it.

---

## Appendix. Source log

Worked: register detail pages (6 of 6); own websites (E1, E2, E3, E4); Tofler single-page views (E2, E3); in-site menus for single-page apps (E1); WhatsApp widget settings in page code (E3).
Failed or unhelpful: Zauba (403), thecompanycheck (403), filesure (403), planetexim (403), 99acres (403), cleartax (410), Tofler search URL (404), direct deep links on E1's single-page site (404), E1's company-profile PDF (image only, no text), biltechestates.com (default server page; one https host did not connect), Meta Ad Library (nothing relevant), CREDAI (no directory), Hindi and English search for E6 (nothing).
Local files (scratch only, not in this folder): saved register list and the six detail pages; a JSON with full unmasked register values.
