# Daily leads 2026-11-06 (scheduled task daily-leads-2)

**Status:** ok. 13 qualified new leads (target 10-15, min 10). Campaign: detailing-studios.
**Source:** Google Maps list method (built-in browser), 21 area queries, about 210 cards read: Ahmedabad (Bopal [limited view, 1 card], Maninagar, Chandkheda, Naroda, South Bopal, Gota, Satellite), Surat (Adajan, Katargam, Vesu), Vadodara (Karelibaug, Alkapuri, Harni/Sama), Rajkot (Kalawad Rd, Mavdi), Navsari, Ankleshwar, Himmatnagar, Bardoli, Godhra, Surendranagar, Porbandar, Dahod, Amreli, Gondal.
**Research:** Workflow tool not used (Maps method needs the browser, which the workflow agents do not have); 4 WebSearch checks only (all weak, see below). **Apify:** not used, US$0 (logged in apify_budget.json).
**Files:** maps_notes.md (raw notes), qualified.json (the 13), entries.json (copy of `agent/state/campaigns/detailing-studios-gujarat.leads_maps_2026-11-06.entries.json`). params.json + seen.txt updated by maps_leads_to_entries.py, config next_index 4 -> 5. Nothing pushed, nothing sent.

## Qualified leads (name, city, grade, reviews, rating, phone last 4, slot)
1. AUTOZ HUB ceramic and PPF coating centre, Surat (Pal), B, 1235, 4.9, ...0002, a-instagram. Biggest review count. IndiaMART lists "Autoz Hub" (ceramic coating, Pal-Adajan); no second outlet found.
2. Veriton automotive, Ahmedabad (Chandkheda, Vrundavan Pearl TP44), B, 101, 4.9, ...2219, c. Card category "Car wash"; name says "automotive", could be a general garage. No web footprint. Check type first.
3. TLC CAR SPA, Vadodara (New VIP Rd), B, 125, 4.4, ...6639, c. "Car spa": may be wash-led.
4. CAR SPA GODHRA, Godhra (Vadodara Highway), B, 143, 4.7, ...5348, a-instagram. Generic name, may be wash-led.
5. JD Carzspa, Ahmedabad (Kathwada Rd), C, 72, 4.8, ...5335, c. Not the CarzSpa franchise as far as the card shows (no carzspa site link).
6. Motorus Detailing & Modification Studio - Gota, Ahmedabad, C, 84, 5.0, ...4707, c. "- Gota" in the name: may have another outlet. No web footprint.
7. Osean Auto Detail Workshop, Surat (VIP Rd, Vesu), C, 68, 5.0, ...7577, c. Category "Car detailing service". Cleanest fit of the C list.
8. Kiyansh AutoCare, Navsari, C, 79, 4.7, ...3166, c. Name lists ceramic/graphene/PPF, "NXTZEN Authorized Installer". Good fit.
9. Mr. Clean the car detailing studio, Himmatnagar, C, 73, 4.6, ...4384, c. Good fit, no web footprint.
10. M Y CAR'Z SPA, Ankleshwar, C, 78, 4.8, ...0408, c. Car spa: wash vs detailing unknown.
11. Auto - 1 Car Spa, Ankleshwar, C, 64, 4.8, ...3083, c. Car spa: wash vs detailing unknown.
12. Detailing Bros - Surendranagar, C, 42, 5.0, ...2452, c. City suffix in the name: other outlets possible; web search found nothing.
13. Chrome Car Spa, Ahmedabad (Jodhpur / Satellite), C, 41, 4.5, ...2347, c. Category "Auto restoration service".

## Dropped / held back
- Spare (not kept): Transformers Auto Detailing Vadodara (142, 4.8, website button opens Facebook: no template for a-facebook yet; good lead if a facebook slot is added), KM Autoz Spa Maninagar (244, website button = wa.me), Autoease Carcare Studio Surat (147, wa.me), Kesar Autohub Naroda (77, website = onetouchbizcard), Auto Herb Porbandar (137, maybe same brand as G.K. Auto Herb Vadodara), Sparkle and Shine Surat (236, IG, basement wash-led), Auto Sparkle Amreli (41, unclear type), GOGLAZE doorstep wash (183, not a studio).
- Own website (Detailing Dude, Autorevv, Akshar Car Spa, Detailing Devils, Coating Guru, Auto Touch, Ride & Shine etc.), chains (CarzSpa, Carz Hub, 3M, Exotic, V8, Creative Motors, Detailing Daddy, A TO Z), plain washes, under 40 reviews, no phone, already in seen.txt: skipped.

## Kya kamzor tha
- Ahmedabad, Surat, Vadodara, Rajkot are almost used up: most good cards were already in seen.txt. New supply came from small towns (Navsari, Ankleshwar, Himmatnagar, Godhra, Surendranagar). Supply will run out in 1-2 more runs; new idea needed (bike detailing, PPF-only, other states, or fresh-listing re-checks).
- 6 of 13 have "car spa" names (TLC, Car Spa Godhra, JD Carzspa, MY Car'z Spa, Auto-1, Chrome): wash vs real detailing is not proven from the card. Veriton may be a general garage. Check these before sending; drop if wash-only.
- Public web search found almost nothing (local studios are not indexed; Instagram/Justdial not searchable). Identity rests on the Maps card only. Chain status unknown for #6 and #12. Owner vs desk number and WhatsApp on the number not confirmed.
- Place panels not opened (cards only): newest review date and owner replies not checked. Re-check every listing on the send day.
- Bopal query returned the "limited view" with 1 card once; other queries worked.
