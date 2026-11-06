# Daily leads report - 2026-10-27

**Status: done (with 2 fixes), 0 READY leads today.**
**Campaign:** `ai-auto-re` (index 0) - AI WhatsApp first-reply automation for real-estate developers (Gujarat)

## Run summary
- Sources chosen by the planner (2): **Meta Ad Library via Apify** (ads with WhatsApp CTA, strongest signal of paid enquiries going to WhatsApp) and **Google Maps slow-reply reviews via Apify** (gave 0 usable results). Rejected: GujRERA register (JS portal, unreadable with our tools), 99acres/MagicBricks (contacts hidden, no need signal), job posts, search ads, news lists.
- Candidates: 12 found (all from Meta ads) -> judge tiers: verified 0, signal_only 9, fit_only 0, unverified 3. Judge dropped 0 (note: judge did not drop anything, which is a bit generous).
- Researched: top 6 signal_only (Classone, Shreem, Shivanta, Shree Siddhivinayak, Sunfin, Kishan Antilia). Not researched: Quick Build Con (Rajkot), Radhekrishna Group (Vadodara), Vatsalya Hilltop (Vadodara) = signal_only; Reseed Infra, Sunrise Group, Anthems Corporation = unverified. They are in `scraper.json` but NOT in seen.txt, so tomorrow's/next runs can pick them up.
- Result: **A 0, B 0, C 6, ready 0.** Skeptic lowered Shivanta (B->C) and Sunfin (B->C).
- Apify spend (est): about US$0.14 (scraper). Researcher used no Apify run that finished.
- Tokens: about 1.6M subagent tokens in total.

## Problems in this run (important)
1. **Agent types `scout` and `qualifier` do not exist in this session** (they are custom agents of the AISales repo). First scraper run failed all collectors. I changed `agentType` to `general-purpose` in the inline script copy and resumed (planner result was cached). Same change for the researcher. The files in `agent/workflows/` are NOT changed. If the daily task should use the original agent types, the task needs to run with the AISales repo as its working directory.
2. `scriptPath` was refused for files outside the working directory, so both scripts were passed inline (unchanged except the agentType).
3. **Meta Ad Library returned HTTP 403 for every researcher and skeptic** (and Apify web-fetch on the JS page did not finish). So none of the 6 ad signals could be re-opened by a second pair of eyes. The collector saw the ads in Apify data only (tier signal_only). This is why every lead stayed at C: the need is only "inferred" until a human opens the ad in a normal browser.

## Non-ready leads (all grade C, no console entry written)
Evidence URL for all six = the Meta Ad Library link from the collector (unverified by researcher/skeptic, 403).

1. **Class One Infra - Class One Evoq, Rajkot (Raiya Hills)** - C/C. Real: partnership firm incorporated 14 Aug 2023, RERA approved 18 Jul 2025, 56 units at Rs 80-85 lakh (RERA mirror https://www.aurumproptech.in/pulse/rera/gujarat/rajkot/class-one-evoq/26534, listing https://houssed.com/rajkot/class-one-infra/class-one-evoq-161259). Finder's name "Classone Group" appears nowhere. Pay signal strong (inferred). Objection: ad unopened; the only phone (+91 81691 14718) is a portal "Connect Now" link, probably the portal's, not the builder's. Angle: instant brochure + 3 questions + site-visit slot for Evoq.
2. **Shreem Avdhesh (Shree Avdhesh Developers), Ahmedabad (Odhav/Varjal)** - C/C. Real RERA project with about 395 unsold units; no developer website. Contacts found: shreemavdhesh@gmail.com, +91 9824331641, ad phone +91 96248 42535 (all from listing/RERA pages, not from the business site). Objection: ad unverified, B needs a strong reach signal. Channel: call the ad number after a human opens the ad.
3. **Shivanta Group - Shivanta Krushnam, Vadodara** - C (investigator B, skeptic C). Own site https://shivantagroup.com/ (expired TLS certificate, seen via search snippets only); phones +91 92270 31144, 8141133114; decision-maker candidate "Hardik Shah" (unconfirmed). Objection: the project "Shivanta Krushnam" and the 191-unit figure appear in no source we could reach.
4. **Shree Siddhivinayak Realities - Vincy Tower, Rajkot** - C/C, pay signal weak. RERA-listed small partnership; signatory number +91 9879149190. Objection: only evidence of need is the unopened ad. Advice from dossier: do not pitch on the ad; open with a public fact (RERA + portal "Ask for Price" forms).
5. **Sunfin Realty Pvt Ltd (Baroda Realty), Vadodara** - C (investigator B, skeptic C). Real broker, site https://www.barodarealty.com/, office lines 70461 19777 / 75673 11777, Rs 1 lakh paid-up capital (small). Objection: the ad's phone (70461 16777) matches nothing on their site (their number is 70461 19777), and no Sunfin project in Gotri/Sevasi/Manjalpur found.
6. **Kishan Antilia (Ambica Inc), Bhayli, Vadodara** - C/C. Real RERA developer, no website, no named owner. Phones 84696 18000 / 84697 18000 from the ad. Objection: only the unopened ad. Note: its "whatsapp" contact +91 81691 14718 is the same portal number as Class One, so it is the listing portal's number, not theirs.

## Kya kamzor tha
- **Zero ready leads.** Root cause: Meta Ad Library cannot be opened by our subagents (403), so the main signal is never second-checked, and the researcher is strict by design. A human (or the chat session with the browser) opening the ad links would likely lift 2-3 of these (Shreem, Shivanta, Kishan, Class One) to B.
- Google Maps reviews source produced 0 results; the whole yield came from one source (no cross-matching).
- The judge dropped nothing and used "signal_only" for all; some details are shaky: "Classone Group" name, "191 units", "395 unsold units", the ad phone of Sunfin.
- Several phone numbers listed as contacts come from listing portals, not from the business itself. Treat as unconfirmed.
- No lead was pushed to the console; `entries.json` is empty (`[]`).

## Bookkeeping done
- `seen.txt`: +6 researched businesses (now 58 lines). `config.json`: `next_index` 0 -> 1 (next campaign: `clinic-web`).
- Files: `scraper.json`, `researcher.json`, `entries.json` (empty), `REPORT.md`.
