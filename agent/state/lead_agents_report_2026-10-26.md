# Dono agents ka test result (26 Oct 2026)

**Sawal:** kya lead-scraper aur lead-researcher need ke hisaab se kaam kar rahe hain?
**Jawab:** Haan, kaam karte hain. Par abhi "pehla version" hai, kuch kamiyan mili aur unko theek kar diya.

## Test kaise hua
4 alag need diye (real-estate WhatsApp automation, coaching-institute software, manufacturer ERP, clinic website). Har need pe scraper ne khud sources chune, researcher ne top 2 leads check kiye. Saath me 2 nakli lead daali (ek badi national chain, ek bani-banayi "Zorbal" company) taaki dekh sakein pakadta hai ya nahi.

## Jo pass hua
| Check | Result |
|---|---|
| Alag need = alag sources? | Haan. Real estate: Meta ads + GujRERA register + job posts. Coaching: Meta ads + Maps + directory. Manufacturer: Naukri + Indeed + TradeIndia. Clinic: Maps (no website) + Meta ads + Justdial |
| Independent judge ka score | 4/5, chaaron me "default route nahi" |
| Purani 25 leads dobara aayi? | Nahi, 0 |
| Chain / nakli lead | 8 me se 8 reject (Godrej, ALLEN, L&T, Apollo, aur Zorbal wale: website hi exist nahi karti thi) |
| Skeptic ka kaam | 3 leads ka grade giraya (Gyanjyot B se C, Edugreed aur Amica reject) |
| Real-estate spot-check | 3 me se 3 poori tarah sahi (ad dates, WhatsApp link) |
| Kharcha | Apify ~ US$0.76 total (chaaron need milake) |

## Leads jo tumhare review ke liye ready hain (kuch push nahi kiya)
1. **Vacanza Developers (Surat)**: B grade. 6 live Meta ads, zyadatar WhatsApp button wale. Need sirf *anumaan* hai (WhatsApp ad normal hai, slow reply ka saboot nahi).
2. **Shafalya Infra LLP (Ahmedabad)**: B grade. Naya project Vellure, GujRERA approval 19 Oct. Sales email aur phone published. Need yahan bhi anumaan; unka funnel pehle se kaafi bana hua hai.
3. **Bhavyaa Hi-Tech Dental Clinic (Shilaj, Ahmedabad)**: B grade. Maps pe website nahi, ek 2 din purana ad. Paisa dene ka saboot kamzor.

Coaching aur manufacturer me koi lead "ready" nahi nikli (best wali C grade thi). Files: `agent/state/eval_2026-10-26_realestate-whatsapp.entries.json` aur `eval_2026-10-26_clinic-website.entries.json`.

## Kamiyan jo mili (sach)
1. Judge "kitni leads usable hain" ka number badha-chadha ke bata raha tha (manufacturer 13 bola, asli ~9; clinic 21 bola, asli verified 2-4).
2. Do alag sources me ek hi company mile (sabse mazboot saboot) yeh check chala hi nahi.
3. Maps/directory/job leads me "signal kab shuru hua" aksar verify nahi ho paya (scrape ki date ko signal ki date samajh liya).
4. Clinic wale collectors ka WebSearch quota beech me khatam ho gaya.
5. Manufacturer ke teeno sources wohi common India scrapers the; "planner hire kar raha hai" signal kamzor hai.
6. Har need pe sirf 0-2 leads ready nikli. Yeh agent "bahut saari" nahi, "kam par pakki" leads deta hai.

## Jo maine theek kiya (abhi dobara run nahi kiya)
- Collector ab batata hai ki date kis type ki hai aur evidence khud kholke dekha ya nahi.
- Judge ab har lead ko tier deta hai (verified / signal_only / fit_only / unverified), sirf pehle do ko "usable" ginta hai, aur sources ke beech cross-match karta hai.
- Planner ko samjhana padega agar teeno source wahi purane Apify scrapers hain.
- Researcher ke output me ab "need sirf anumaan hai" ka flag aata hai.

## Agla kadam (tumhari marzi)
- Upar ki 3 leads dekh lo, jo theek lage unhe campaign me add karne ko bolo (main console me push kar dunga).
- Ya naye changes ke saath ek chhota re-test chalaun (manufacturer + clinic) dekhne ke liye ki honest count aur dates behtar hue ya nahi.

Detail: `agent/docs/LEAD_AGENTS.md` (section 4). Memory me bhi likh diya hai.
