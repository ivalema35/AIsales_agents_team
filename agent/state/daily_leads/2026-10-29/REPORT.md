# Daily leads 2026-10-29

**Status:** ok (1 fix, see "Kya kamzor tha")
**Campaign:** clinic-web (WhatsApp patient desk for doctor-owned clinics, Gujarat: Ahmedabad, Surat, Rajkot, Gandhinagar)
**Sources chune gaye:** Round 1: (1) Meta Ad Library via Apify (WhatsApp-opening ads, ad start date dikhta hai = paid enquiries ka seedha signal), (2) Google Maps recent reviews via Apify (unanswered calls). Yield kam tha (4 usable of 8), isliye re-plan: (3) Meta Ad Library v2 (30+ din purane WhatsApp ads, alag keywords) aur (4) Google sponsored clinics (0 mile).
**Candidates:** 15 (verified 0, signal_only 11, fit_only 1, unverified 3). Researcher ne top 6 check kiye.
**Result:** 1 grade B, 2 C, 3 reject. **READY: 1** (Shivam Skin Hair & Laser Clinic, Surat). Apify kharcha (est): about US$0.25 scraper + ~US$0.01 researcher.

## READY lead (grade B)

### 1. Shivam Skin Hair & Laser Clinic, Nana Varachha, Surat
- **Kyun:** Meta Ad Library page (id 101194626197782) par 6 active ads, sabme "Send WhatsApp message" button. Start dates 2026-08-06 (2 ads), 08-08, 08-13, 09-16, 09-18; sabse purana ~84 din. Researcher ne Ad Library direct nahi khol paya (403), ek chhote Apify run (~US$0.005) se dobara padha. URL: https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&view_all_page_id=101194626197782
- **Branch / specialty:** skin + hair + laser (acne, Hydrafacial, PRP). Branch: probably 1 (Nana Varachha). Ek ad me "Mota Varachha" likha hai, wahan doosri branch ka koi proof nahi (ek alag homeopathic clinic hai, ussey mix mat karna).
- **Contacts (clinic-published):** clinic appointments +91 95373 88962 (site https://www.shivamclinik.com/ + ads; yeh desk ho sakta hai). Doctors ke naam se digital card (https://digital-card.in/shivam/): Dr. Dipak Mandaviya +91 95373 88973, Dr. Bhavita Mandaviya +91 90232 99691. Sab likely WhatsApp, confirm nahi.
- **Owner/decider:** probably (inference: dono Mandaviya doctors, same surname; koi page "owner" nahi likhta).
- **Need:** INFERRED (6 paid WhatsApp ads + site par online booking nahi). Koi missed enquiry observed nahi. **Pay signal:** strong (researcher ke hisaab se), par thin hai: Facebook page 88 likes, template site.
- **Skeptic ka aitraaz:** need sirf inferred; doctors ke numbers third-party digital card se aaye, site ya Maps se nahi; ads shayad bahar ka marketer chalata hai (boosted reels jaisa); Justdial/Maps khule nahi.
- **Angle:** sawaal, claim nahi: "Dr. Dipak, aapke acne ads WhatsApp kholte hain. Raat 10 baje ya jab dono doctor patients ke saath hon, us number par kaun jawab deta hai?" Free sample reply + slot picker offer. **Channel:** WhatsApp (insaan se) Dr. Dipak ke mobile par, OPD ke bahar (9:30-13:00 aur 17:00-21:00 ke alawa). Pehle desk number 95373 88962 mat use karo. Email nahi.

## Non-ready leads

- **Re Life Clinic (Dr. Rikin M. Shah), Gota, Ahmedabad:** grade C. Specialty diabetes/obesity (skin/dental nahi), doctor shayad Marengo CIMS Hospital me bhi baithta hai, 3 alag phone numbers, Ad Library 403 (ad kisi ne dekha nahi). Need inferred, pay weak.
- **Dr. Dhamelia's Skin Laser & Hair Clinic, Ahmedabad:** reject. Ad evidence kisi ne khol ke nahi dekha (403); sirf ek Facebook page title confirm hua, 2nd independent source nahi mila (unverifiable).
- **RQC Hair Transplant & Skin Clinic (Dr. Vivek Galani), Surat:** reject. Apni site par Surat main + Ahmedabad (Naroda) branch = 2 cities (chain rule), doctor-direct number nahi.
- **ADIVA Center for Skin and Hair (Dr. Harshit Ranpara), Rajkot:** B se skeptic ne C kiya. Sirf ek 1-star Google review (phone hold, "fully booked"), koi Meta ad nahi dikha, WhatsApp complaint nahi, phone/capacity complaint hai. Owner-direct unproven. (Review ka zikr clinic se kabhi nahi karna.)
- **Narayan Skin Clinic (Dr. Ketan Kacha), Rajkot:** reject (unverifiable). Ad page khula nahi; sirf ek aggregator (Drlogy) ek Rs 100 homeopathic GP dikhata hai, skin services nahi. Hath se Ad Library dekhne par C ban sakta hai.

Baaki scraper candidates jo researcher tak nahi gaye (top 6 ke baad): Ajaram Skin Hair & Laser (Surat), Naman Breast Clinic (Surat), Maninagar Dental Hospital and Implant Center, Satguru Skin Hair Laser & Family Clinic (Surat), The Skin Lab (Surat, ad 2026-10-23), Rejuvene Skin Clinic (Rajkot, fit_only), Vinayak Dental, Siddhi Skin Clinic, Nilkanth Skin Clinic (unverified). Ye seen.txt me nahi daale gaye, kal ya baad me dobara aa sakte hain. Poori list: `scraper.json`.

## Kya kamzor tha

1. **Meta Ad Library 403:** koi bhi agent page seedha nahi khol paya. Sirf ek ready lead (Shivam) me researcher ne Apify se dobara padha. Baaki 5 me ad ka saboot nahi dohraya ja saka, isliye 2 reject, 2 C. Ad-based leads ko owner ko hath se ek baar Ad Library me dekhna chahiye.
2. **Need har jagah inferred hai:** ad dikhta hai, par "enquiry unanswered hoti hai" kahin observed nahi. Shivam ke liye bhi sirf sawaal wala angle sahi hai, claim nahi.
3. **Owner-direct contact unproven:** doctor ke numbers digital card se aaye (clinic ki apni site ya Maps se nahi). Pehle message ka jawab hi confirm karega ki number kiska hai.
4. **Technical fix:** `scout` aur `qualifier` agent types is session me nahi mile (woh AISales repo ke `.claude/agents` me hain, session working directory alag thi). Dono workflows me `general-purpose` agent type use kiya, baaki script waisi hi. Agar chaho to daily-leads-2 task ko AISales_agent_team folder se chalao taaki asli agent types mile.
5. Workflow scriptPath bhi nahi chala (repo bahar ki), isliye scripts inline chalaye.
6. Judge ne 11 "signal_only" gine par koi "verified" nahi; judge tier abhi bhi generous.
