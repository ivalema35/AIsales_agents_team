# Daily leads 2026-11-05 (scheduled task daily-leads-3)

**Status:** ok. 12 qualified new leads (target 10-15, min 10). Campaign: detailing-studios.
**Source:** Google Maps list method (built-in browser), about 36 area queries (about 350 cards read): Ahmedabad (Prahlad Nagar, Ghatlodia/Ranip, Sarkhej/Ambli, Nikol, Navrangpura, Vastral/Odhav, Sola, Shilaj, Vejalpur, Thaltej, graphene/ceramic queries), Surat (Varachha, Udhna, Piplod, Rander, Sachin/Kamrej, Dindoli, PPF), Vadodara (Gotri, Manjalpur, Waghodia Rd, Akota, Bhayli, PPF), Rajkot x3, Gandhinagar x2, Bhavnagar, Jamnagar, Nadiad, Anand, Bharuch, Vapi/Valsad, Junagadh/Morbi, Bhuj/Gandhidham.
**Apify:** not used, US$0. Workflow tool not available; research by 3 lead-researcher agents (WebSearch/WebFetch only, 27 candidates checked). Files: candidates.json (20 first-round cards), qualified.json (the 12 kept). Entries file: `agent/state/campaigns/detailing-studios-gujarat.leads_maps_2026-11-05.entries.json` (params.json and seen.txt updated, config next_index +1). Nothing pushed.

## Qualified leads (name, city, grade, reviews, rating, phone last 4, slot)
1. Sunshine Car Spa, Ahmedabad (Ghatlodia), B, 204, 4.9, ...5635, c. Only a directory entry (LocalEye: detailing + ceramic/graphene). No site/Instagram found.
2. Sparkling Car Studio, Ahmedabad (Sola), C, 58, 4.8, ...5093, c. Instagram @sparklingcarstudio (~61 followers): ceramic, wrap, wash. Maps address is inside a Mahindra showroom: may be a showroom side business.
3. AutoDox Carz, Surat (Vesu/Piplod, Blue Ribbon Bldg), C, 76, 4.9, ...8098, c. Best-verified: PPF/wrap/detailing studio, MotoShield authorized detailer, single outlet, Instagram @autodox_carz (~580 followers), no own site. Maps says Piplod, MotoShield says Vesu: check area.
4. Mr.Detailing Car Care Centre, Surat (Dindoli, Madhuram circle), C, 59, 5.0, ...3029, c. No web footprint; generic name, outlets unchecked.
5. Radhe Krishna Car Detailing, Vadodara (Ajwa Rd), B, 143, 5.0, ...0367, c. No web footprint, nothing against.
6. Csm Detailing Studio, Vadodara (Airport Circle), C, 43, 4.8, ...4395, c. Maps category "Auto restoration service". No web footprint.
7. TOP 7 Detailing, Vadodara (Bhayli), B, 158, 5.0, ...4522, c. No web footprint.
8. Detailuxe, Vadodara (Bhayli), C, 41, 5.0, ...1460, a-instagram. Website button opens Instagram; handle not read.
9. Brightspots Car Studio, Rajkot (Bolbala Main Rd), C, 71, 5.0, ...7142, c. Maps category "Car detailing service" (twice). No web footprint.
10. RideinStyl Ceramic Coating & PPF Studio, Vapi (NH48), B, 392, 4.9, ...8806, c. Strongest review count. No web footprint; outside the core geography (South Gujarat).
11. Premium Auto Care & Car Detailing Studio, Gandhidham (Lilashah Cir), C, 66, 4.9, ...0475, c. City from Maps coordinates. Generic name; outside core geography.
12. 9TO9 Car Detailing Studio & Spa, Bhuj (RTO School Rd), C, 101, 4.3, ...0019, c. City from Maps coordinates. "9TO9" may be a multi-outlet name; rating just above cut (grade C).

## Dropped / held back
- Researcher DROP: Sunshine Cars (Prahlad Nagar: workshop with own site, 2 outlets), B2 Carz (repair/wash, 2 outlets), V8 Car Detailing Studio (5 outlets), Autobell (own site, 4+ outlets), Autogard Motors (own site), Autoworrld (multibrand workshop), The Car & Bike Surgeon Gotri (insurance garage).
- Spare / not kept (unsure type): Silent Car Care Surat (wash + coating + accessories mix, 114 rev, 4.9), CarNest Detailing & Diagnostic Center (hybrid workshop), Premium Car Wash Vadodara (wash-led, keyword-stuffed name), Trinay Car Care, CARTIST (detailing + accessories shop, IG), Forza Detailing Hub & Bodyshop (bodyshop), Elite Detailing & Car Washing Vapi (wash-led), o3 Car Spa Vapi (likely branch of an Anand brand), Ocean Car Spa Jamnagar (2 branches).
- Plain car washes (many in Bhavnagar, Bharuch, Surat, Vadodara), under 40 reviews, no phone, has own website, chains (CarzSpa, Carz Hub, Creative Motors, Detailing Daddy etc.), already seen: skipped.
- Mehsana/Kadi/Visnagar/Patan/Anand/Nadiad: nothing new (done on 4 Nov).

## Kya kamzor tha
- Ahmedabad and Surat are mostly used up by earlier runs; new leads came from Vadodara, Vapi, Kutch and Rajkot. Fresh supply will shrink further.
- The web check was weak: public search found almost nothing for most of these (Instagram/Facebook/Justdial not searchable, Justdial 403). For 9 of 12 leads identity rests on the Maps card only. Chain status "unknown" for #4, #11, #12 especially. Owner vs front desk unknown; WhatsApp on the number not confirmed.
- Maps place panels do not show text via get_page_text; cards only. Owner replies to reviews and newest review date not checked. Re-check each listing on the send day.
- 3 of the 12 are outside the core geography (Vapi, Gandhidham, Bhuj); drop them first if the owner wants Mehsana-belt/Ahmedabad only.
