# Daily leads 2026-11-04

**Status:** ok, lekin 0 ready (kamzor din, pichhle din jaisa)
**Campaign:** detailing-studios (car / bike detailing studios, Gujarat)
**Apify:** is mahine (Nov) ka spent 0.0 / cap 4.5, par Apify tools subagents me mile hi nahi. Asli kharcha: US$0. Sirf WebSearch / WebFetch / DNS check.
**Tarika (note):** is session me `Workflow` tool nahi tha, isliye lead-scraper aur lead-researcher ka kaam Agent tool se (1 scraper agent, 6 investigator agents, 2 skeptic agents) chalaya. Repo ki scripts nahi badli. Skeptic sirf un 2 leads par chala jinka pehla grade B tha; C/reject ko skeptic upar nahi utha sakta.

## Sources aur candidates
Round 1 (re-plan nahi hua, 6 usable >= 5 threshold): (1) Garware Application Studio + Llumar partner locator (real studios, phone, kuch me website blank), (2) city-wise web/Instagram/Facebook search + live site aur DNS check. Reject kiye gaye: Google Maps (nahi padh sakte), Justdial / Wheree (403), Instagram (login wall), Meta Ad Library (interactive), carchhe.com (fit_only).
Candidates: 10 (verified 2, signal_only 4, fit_only 3, unverified 1). Researcher ko 6 usable gaye. **READY: 0.** Grades: C = 5, reject = 1.

## READY leads
Koi nahi.

## Non-ready leads
- **Auto Clinic (Llumar partner), Bellagio/Iscon, Ahmedabad:** pehle B, skeptic ne C kiya. Real single studio (Llumar locator + directory + Instagram), phone 9909956565 do jagah published, pay signal strong. Par website-button / reviews / owner-reply (Maps) kuch dekha nahi gaya; "no website" sirf negative finding hai; 4.6 rating shayad padosi CarzSpa Ambli ki hai; number kiska hai unknown. Maps par check ho jaye to slot c ke saath B ban sakta hai.
- **Detailing Culture, Bodakdev, Ahmedabad:** pehle B, skeptic ne C kiya. Real, single-outlet Garware studio, apni site detailingculture.in par booking form hai; photo/video galleries par "no projects added yet" (4 Nov ko dekha). Par Instagram par Mar-Oct 2026 ke posts hain, site naya hai, koi slot a/b/c/d nahi, owner-reach unproven (studio ka wa.me 91063 26281; Garware wala doosra number use na karo).
- **MK29 Detailing, Chharodi, Ahmedabad:** C. Live site + hotline 84870 11029, par Maps data nahi, enquiry form hai (slot d lagu nahi), owner unnamed, Instagram 107 followers.
- **Dignity Cares (Garware studio), Ghodasar, Ahmedabad:** C. Real, par "no website" sirf do directories se; dignitycare.in parked hai, ownership confirm nahi; phone Garware register ka hai.
- **Detailing Spot, Nizampura, Vadodara:** C. Magicpin 4.7 (63 ratings), phone sirf aggregators par; Maps / Wheree 403; Vadodara second-wave geography.
- **Arbuda Car (Gandhinagar):** reject. Accessories / customisation shop (excluded type), sirf apni netlify site (ek hi source), Book Now ki jagah enquiry form + WhatsApp button hai.
- **fit_only / unverified (researcher ko nahi gaye):** Morning Shine (Gota), Spotless Car Spa (Kudasan), O3 Car Spa (Anand), Coaterz (Anand).
- Scraper ne drop kiye: Autotouch (4 outlets), Autoism, Autobell, Creative Motors, Motorus, Mquik, Dharti Auto Accessories, Garware distributors (S M Trade, Futkar, Global Auto Traders), Detailing Xpert (franchise + seen).

## Kya kamzor tha
- Sabse badi kamzori wahi: Google Maps (website button, newest 3 reviews, owner replies, Maps phone) free tools se nahi dikhta, isliye campaign ke asli signals kisi lead par verify nahi hue. Sab "need" inferred hai. Visnagar, Palanpur, Patan, Nadiad me koi studio nahi mila; Kadi me sirf unverified Justdial snippets.
- Apify tools scraper / researcher subagents me available nahi the, to ~US$0.08 ka capped Maps check nahi chal paya. Agla kadam: Auto Clinic, Detailing Culture aur 4 aur names ka ek chhota Maps check (Apify ya normal browser se), tab Auto Clinic B-ready ho sakta hai.
- Workflow tool is session me missing tha (Agent-tool fallback), skeptic sirf 2 leads par chala.
- Auto Clinic ka finder-claim "4.6 rating" reproduce nahi hua; Detailing Culture ke dono phone ka owner-link unproven.
- Raw dossiers aur challenges: `work/leadN.dossier.json`, `work/leadN.challenge.json`.
