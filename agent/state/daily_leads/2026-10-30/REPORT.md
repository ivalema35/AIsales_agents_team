# Daily leads 2026-10-30

**Status:** ok, lekin 0 ready (kamzor din)
**Campaign:** detailing-studios (car / bike detailing studios, Gujarat)
**Apify:** is mahine ka budget khatam (spent ~US$18 vs cap 4.5), isliye Apify bilkul use nahi hua. Kharcha: US$0. Sirf WebSearch / WebFetch.
**Sources chune gaye:** Round 1: (1) Garware Hi-Tech Films "Locate Us" application-studio pages, (2) town-wise web search for studios ki apni sites. Yield kam tha (2 usable of target 8), isliye re-plan: (3) carchhe.com roster, (4) studio-footprint audit (website/social presence check). Google Maps aur Meta Ad Library free tools se khulte nahi (Maps sirf title deta hai, Justdial 403), isliye review-reply aur website-button wale signals check nahi ho paye.
**Candidates:** 13 (verified 1, signal_only 1, fit_only 11, unverified 0). Runbook ke hisaab se sirf verified/signal_only (2) researcher ko diye.
**Researcher:** 2 check kiye, dono reject. **READY: 0.**

## READY leads
Koi nahi.

## Non-ready leads
- **Kesari Custom - The Car Detailing Studio, Tragad, Ahmedabad:** reject (unverifiable). Studio ki apni site sirf free Grexa template hai (kesari-custom.grexa.site) jo Google listing se auto-bani hai, yani dusra independent source nahi. Google Maps listing khuli nahi, to phone ya owner-replies confirm nahi. Observed: site par sirf "Enquire" buttons, booking form / WhatsApp link nahi (https://kesari-custom.grexa.site/contact). Phone +91 92745 82116 sirf us site par. Pay signal weak. Agar kisi ko normal browser me Maps listing dikhe to C/B ho sakti hai.
- **Quartz Detailing Studio, Vesu, Surat:** reject (unverifiable). quartzdetailingstudio.in resolve nahi karta (DNS NXDOMAIN, 30 Oct), par business ab bhi chal raha hai ye koi source nahi dikhata; Instagram snippet Chikhli batata hai, Surat Vesu se conflict; phone numbers dead site ke search snippet se aaye. Business band ya shift ho sakta hai.
- **Baaki 11 fit_only (researcher ko nahi gaye):** Coating Buddies (Odhav), Incredible Car Detailing (Shilaj/Bopal), The Gunman Car (Mehsana), MotorX Car Care (Makarba), Shreeji Car Spa (Satellite), Vampires Detailing (Sola), AutoGlow (Chandkheda), Swish Auto Care (Vadodara), MP Car Spa Gota (shayad 2-outlet brand), Shakti Car Care (Mehsana Palodar), Janvi Car Wash and Detailing Studio (Kadi). Ye sirf carchhe.com ke rows hain (rating + mobile, no website field): koi signal verify nahi hua. Agar owner Apify budget ya normal browser de to inhe Maps par check karna sabse achha agla kadam hai.

## Kya kamzor tha
- Free tools se campaign ka asli signal (Google website button, newest-3-review replies) dekha hi nahi ja sakta, isliye 11 of 13 candidates "fit_only" rahe. Ye aaj ki sabse badi kamzori hai.
- Technical: `lead-scraper.js` / `lead-researcher.js` me agentType `scout` / `qualifier` is session me nahi mile (pehli baar collectors fail hue). Maine session-copy me `general-purpose` kar ke chalaya, repo ki script nahi badli. Scheduled task ko Workflow tool ke liye script inline deni padi (file working directory ke bahar hai).
- Judge ke tier phir se thode generous ho sakte hain; dono usable leads researcher ne reject kar diye.
- Mahine ki Apify cap khatam hone se detailing campaign ki asli kamzori (Maps data) 1 Nov (naya mahina) tak solve nahi hogi.
