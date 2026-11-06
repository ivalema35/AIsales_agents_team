# Meta Ad Library test, 21 Oct 2026 (Apify curious_coder/facebook-ads-library-scraper, custom connector)

Local file (git-ignored). Phones below are the numbers PRINTED IN THE ADS (business-published), not verified owner numbers. Nothing was contacted.

## Runs and cost
- Run 1 (named builders, 9 URLs, exact-phrase, active, IN): run 1dYGhgK7FE1BE4ix9, dataset SmVc5bp2ouOGEpqi4, 6 ads returned, ~US$0.01.
- Run 2 (discovery: "<city> 3 BHK site visit" for Ahmedabad, Surat, Vadodara, Rajkot, 25 per city, active, IN, most recent): run 7RC1y1w2ZLJoi9iHQ, dataset P3WR3suDei2WkpAPy, 92 ads, ~US$0.07-0.09 (92 x $0.00075 + start). Check exact amount in the Apify console.
- Both under the spend caps ($0.25 / $0.10). Total about US$0.10.

## Run 1: the 9 names from the first test
- No active ads found: Aadi Makers, Tirupati Construction, Kailash Corporation, Sahaj Buildcon, Raghuvir Buildcon (only an Instagram-profile ad from "Raghuvir Developers & Builders", May 2026, not WhatsApp), Hrishikesh Ventures, Bhumika Buildcon, Auracle Makarba.
- Satyamev: 3 pages running ads. "Satyamev Group" (page 448787565559347): video ads started 23 Jul and 3 Aug 2026 (Royal 4 and Royal 5), CTA "Get quote" (Meta lead form, NOT WhatsApp), copy says "Enquire today and schedule your Site Visit". "Satyamev Developers" (page 776409658887896, possibly a sister entity): Vista Two video ad started 10 Sep 2026, CTA Get quote. The third match was a Housing.com ad that only mentions Gandhinagar (ignore).
- So Satyamev = STACKED signal: hiring ads (~18 Oct) + paid lead-gen ads. Pain still not observed; channel is lead forms and phone, not WhatsApp.

## Run 2: advertisers with a click-to-WhatsApp button (CTA = WHATSAPP_MESSAGE), active, newest ad first
| Page (as on Facebook) | City / project (from ad copy) | Latest ad start | Phone printed in ad | Type |
|---|---|---|---|---|
| BGSR | Rajkot, Atlantis Hills (Raiyadhar Road) | 20 Oct | 99792 36000 | developer |
| shree_siddhivinayak_reality_56 | Rajkot, Vincy Tower | 20 Oct | 96875 16666 / 99259 13232 | developer |
| Siddhivinayak Developers | Surat, Elite Homes row houses (Laskana-Kholvad) | 17 Oct | 999 88 58000 / 95589 77078 | developer |
| Vaidehi Developers | Surat, Vaidehi Hills (Karadva) | 17 Oct | 70435 54431 | developer |
| Mahant Nakshatra | Surat, Masma-Orma Road | 15 Oct | 75740 41310 | developer |
| Shyam Rivanta | Surat, Mota Varachha | 14 Oct | 98798 25100 | developer; CHECK vs contacted "Rivanta Heritage" before anything |
| BLJ INFRA LLP | Rajkot, Silver Square (150 ft Ring Road) | 12 Oct | none printed | developer |
| Param Developer | Surat, Param Elina (Adajan) | 10 Oct | none printed | developer |
| Shree Namasya | Vadodara, Atladra-Padra Road | 8 Oct | 70696 06777 | developer |
| VR Group | Vadodara, New Karelibaug (APMC) | 19 Sep | 75748 82881 | developer (a "VR Ahmedabad" was also a hiring near-miss: check if related) |
| Lions Real Estate Surat | Surat, Kailash Homes (Masma-Orma Road) | 27 Sep | 99989 05682 | broker / sales agency |
| Mahanta Group | Surat, Madhuvan Farm Villa (Velook) | 12 Sep | 93276 95584 | developer |
| Sunfin Realty | Vadodara, Gotri-Sevasi | 15 Sep | 70461 16777 | developer/broker |
| Reseed Infra Group | Vadodara, Shubh Imperia (Makarpura) | 3 Sep | 81608 53083 | developer |
| 1 Clik Property | Surat (Vesu) | 11 Aug | 99788 00128 | broker |
| Shree Shyam Developers | Surat, Olpad (Masma-Orma Road) | 2 Aug | 99793 02000 / 85112 47779 | developer |
| Peak Living | Surat, Althan | 12 Jun | none | developer |
| TPG - The Palm Group | Ahmedabad, Nava Vadaj | 19 May | none ("book on WhatsApp") | developer |
| Reva80 | Ahmedabad, Nikol | 29 May | 74350 06001 | developer |
Strongest (ad started within the last 14 days, 7-21 Oct): BGSR, Shree Siddhivinayak Realities, Siddhivinayak Developers, Vaidehi Developers, Mahant Nakshatra, Shyam Rivanta (dedupe check), BLJ Infra, Param Developer, Shree Namasya.

## Other Gujarat advertisers seen (lead-form / call CTAs, NOT WhatsApp): context only
Nyalkaran Group, Kesar Group, Sharnam Sanidhya, Prapti Group, Tanaaz, Saanvi Nirman, Satya Sankalp, Sammoda Grandeur, Explore Ahmedabad, Rameshwar Developers, The Privilon, Pragati Arcelia, Mahadev Sky, Hari Shyam, Kasturi Infraventures, The Divine Group Rajkot, Shree Ambica Elegance, Royal Regius, Keshavaa Group, Shriram Realties, Kohinoor Group, Pacifica Companies, Mount Group, Ukaz Group, Shiv Aradhana Bunglows, Piramyd Group, Trinity Heights, Mangla Group, Narayan Realty, Purusarth Group. Portals/vendors to ignore: 99acres, Housing.com, Adani Realty (national).

## What this proves / does not prove
- The ads angle WORKS and is cheap: 92 ads cost under 10 cents and gave 19 Gujarat advertisers using click-to-WhatsApp, 9 of them with a fresh ad in the last 14 days. It proves they pay for WhatsApp enquiries (stronger than a hiring ad).
- It does NOT show pain (late or missed replies), the real owner, a WhatsApp-capable number, or whether they already have an auto-reply. That is step 2 (enrich): owner via GujRERA authorised person / website / Instagram / LinkedIn, and whether the number is WhatsApp (we can only see this by opening the click-to-WhatsApp link or wa.me, read-only; do NOT message).
- All of this is "likely need", not "asked for it". Expect low reply rates; compare with campaign 1 = 0 of 9.
- Quality risk: broker/agency pages (Lions Real Estate, 1 Clik Property) are resellers; small local developers often run ads through an agency, so the ad phone may be a telecaller.
