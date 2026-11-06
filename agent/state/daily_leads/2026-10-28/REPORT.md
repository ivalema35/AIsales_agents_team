# Daily leads 2026-10-28

**Status:** ok (with 2 fixes, see "Kya kamzor tha")
**Campaign:** clinic-web (Website + Google profile + WhatsApp enquiry for local clinics, Gujarat)
**Sources chune gaye (planner ne 8+ me se):** (1) Google Maps broad scrape for 3 cities (Apify, saste per-result price par: website field dekhne ke liye), (2) Google Maps "withoutWebsite" filter, sirf Mehsana (seedha need dikhata hai: website hai hi nahi). Baaki (Justdial, Practo, Meta Ad Library, medical council, association lists, job posts) reject: need nahi dikhate ya numbers portal ke hain.
**Candidates:** 18 (verified 1, signal_only 13, unverified 4, fit_only 0). Researcher ne top 6 check kiye.
**Result:** 4 grade B, 1 C, 1 reject. **READY: 3** (M.K., Goradwala, Uma). Apify kharcha (est): about US$0.23 scraper + ~US$0.01 researcher.

## READY leads (grade B, saare Mehsana)

### 1. M.K. Hi Tech Dental Clinic, Mehsana (Dr. Anand Patel / Dr. Asmita Patel, Facebook snippet ke hisaab se)
- **Kyun:** Google Maps par listed website http://mkdental.clinic.net.in/ DNS par resolve nahi hoti (dead link, 2026-10-28 ko check). 73 reviews sab 5-star. Maps: https://www.google.com/maps/place/?q=place_id:ChIJw-QETi5DXDkRs233-yS--eU
- **Contact:** +91 95585 56006 (Maps listing; Facebook snippet me bhi same). Likely WhatsApp, confirm nahi. FB page: https://www.facebook.com/mkhitechdentalclinic/
- **Need:** observed (dead website). **Pay signal:** weak.
- **Skeptic ka aitraaz:** identity ek Maps scrape + Facebook title par tika; doctor ke naam aur "13 saal" snippets se aaye (Justdial/Medindia 403). 73 reviews bina site ke aa rahe hain, to urgency kam ho sakti hai.
- **Angle:** "Google par Website dabane se error aata hai" (fact, chhota) + website fix + WhatsApp appointment button. **Channel:** WhatsApp / call, number upar; Dr. Anand ya Dr. Asmita ko poochho.

### 2. Goradwala Smile Centre - An Advance Dental Clinic (Dr Saurabh Patel), Mehsana
- **Kyun:** Website sirf free Wix page: https://sharpedge99.wixsite.com/website-1 (1 page, 4 services, booking/WhatsApp nahi, footer 2022). 157 reviews 5.0 finder ka claim, researcher verify nahi kar paya (Lybrate: rating 4.3, fee Rs 300).
- **Contact:** 9925099230, clinic ke apne Wix page par (likely WhatsApp). Doosre numbers directory ke hain, unhe use mat karo.
- **Need:** observed (feature gap, lost business proof nahi). **Pay signal:** weak.
- **Skeptic:** Wix page + Lybrate + Facebook pehle se hain, Rs 300 consultation par free Wix plan chuna, matlab budget kam ho sakta hai.
- **Angle:** unke apne 2022 Wix page ka before/after, free preview with WhatsApp appointment button. **Channel:** WhatsApp short human message.

### 3. Uma Dental Clinic & Implant Center, Mehsana (Dr. Brijesh Patel owner, KiViHealth profile)
- **Kyun:** Maps par website field khali (finder ka claim, Maps page researcher ne khola nahi); directories (Latrexa, dentalimplantprice.in) par bhi koi website nahi. 220 reviews 5.0 (unverified).
- **Contact:** +91 89800 12380 (Dr. Brijesh ka KiVi profile https://kivihealth.com/iam/brijesh.patel.3236 aur Latrexa). Ek aur number 99250 29462 sirf Mappls par, use mat karo.
- **Need:** observed (no website in directories). **Pay signal:** weak (implant practice, 2 locations: Mehsana + Dhinoj, inferred).
- **Skeptic:** 220-review claim koi verify nahi kar paya; KiVi online booking page pehle se hai.
- **Angle:** WhatsApp voice note, doctor ke naam se: "implant dentist Mehsana" search par apna kuch nahi dikhta, chairside ho tab WhatsApp enquiry koi nahi uthata. Email nahi.

## Not ready
- **Skin Sure Clinic (Dr. Sneha Patel), Mehsana** , grade B, par researcher number padh nahi paya (Maps render nahi hua); finder ke hisaab se mobile +91 93286 74079 Maps par. Chat session Maps khol ke number confirm kar le to ready ho sakti hai. Skeptic: Facebook/Instagram pehle se, Rs 400 fee, weak pay.
- **Orthopedic Physiotherapy Clinic (Dr Rahul Prajapati)** , reject: do independent sources nahi mile (sirf ek directory post, Maps nahi khula).
- **Ambika Skin, Hair & Laser Clinic** , grade C: need sirf inferred (Maps empty field recheck nahi hua), do alag phone numbers, hours conflict.

## Baaki 12 candidates (researcher ko nahi diye)
Uma-type signal_only: Mehta Physiotherapy, Keshavam Eye Clinic (Gandhinagar), Geeta Dental (Gandhinagar), Dr Dhruv's Yashdeep Skin (Gandhinagar), Shubham Dental, Jay Physiotherapy, Mayur Dental, Dr. Amee's Skin Clinic. Unverified: Nilkanth Hi Tech Dental Hospital, Ambika Eye Hospital, Prism Eye Clinic, EVA Skin Hair and Laser. Details scraper.json me. Ye kal ke liye bachi hui pool hai (seen.txt me nahi daali).

## Kya kamzor tha
- Saari signal dates scrape-date (2026-10-28) hain, source ki date nahi. Maps "website khali hai" snapshot hai, kab se, pata nahi.
- Maps pages researcher ke liye render nahi hue (JS shell); Justdial/Medindia 403. Review counts, doctor ke naam, 13 saal sab snippets par. Chat session ko 2-3 leads ke Maps listing khud kholke phone number aur website field confirm karna chahiye.
- Teeno ready leads par pay signal weak hai; sab chhote single-clinic, kam budget ka risk.
- Sab leads Mehsana ke hain, Ahmedabad ka koi nahi aaya (broad scrape se bhi nahi). Eye/physio: 1 physio reject, eye researcher tak nahi pahunchi.
- Technical: workflow scripts me agent types `scout` aur `qualifier` is session me nahi mile, isliye `general-purpose` se chalaya (scripts repo me waise hi hain). Workflow tool scriptPath nahi le raha tha, to scripts inline di.
