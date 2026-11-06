# Re-test result (26 Oct 2026): manufacturer + clinic

**Short me:** fixes se kaafi sudhar hua, par poora nahi. Sabse bada sabak: **scraper ki leads "claims" hain, sachchai researcher + skeptic nikalta hai.**

## Kya sudhra
- Manufacturer: naya need-specific source mila (SME IPO filings, PDFs padhe). Dates 17 me se 17 source se aayi. Spot-check me 4 me se 3 poori tarah sahi (pehle 3 me se 0).
- Clinic: jin leads ki sirf scrape date thi (38 me se 18), unpe ab sahi label laga.
- Nakli chain/fake leads 4 me se 4 reject.

## Kya abhi bhi kamzor
- Judge ke tier labels 8 me se 4 baar zyada bade the. "Usable" count abhi bhi thoda generous (manufacturer 14 vs ~10, clinic 27 vs ~8).
- Cross-source match: koi company do sources me nahi mili.
- Rating-agency source se sirf 1 lead; Morbi se 0; skin/eye/physio clinics search hi nahi hue.
- Manufacturer: 0 ready. Teeno IPO companies skeptic ne C kar di (growth dikhta hai, back-office dard ka saboot nahi).

## Sabse zaroori finding
Clinic ki 3 "ready" leads me scraper ka headline teeno me aanshik galat tha, aur researcher ne pakad liya:
- **S M Wellness:** "sirf Instagram" galat; website hai, par andar ke pages 404 aur appointment button parked domain pe jaata hai.
- **Sure Align:** "domain kabhi bana hi nahi" galat; Jan 2026 tak chalti site thi, ab "Coming soon".
- **Dabhi's Dental:** ad ki dates reproduce nahi hui (asli start 12 Aug); par domain sach me dead hai aur WhatsApp ads active hain.

Matlab in leads ka pitch "website banao" nahi, "aapki site toot gayi hai" wala hai (checkable hook), aur problem hum call karein tab tak theek bhi ho sakti hai.

## Ready leads (review ke liye, kuch push nahi kiya)
- Test 1: Vacanza (Surat), Shafalya (Ahmedabad), Bhavyaa Dental (Ahmedabad)
- Re-test: Dabhi's Dental, Sure Align Orthodontix, S M Wellness (file: `agent/state/retest_2026-10-26_clinic-website.entries.json`)

## Rule jo ab yaad rakhna hai
Scraper ke baad researcher hamesha chalao, top 5-8 leads pe, tabhi lead use karo.

Detail: `agent/docs/LEAD_AGENTS.md` section 4b.
