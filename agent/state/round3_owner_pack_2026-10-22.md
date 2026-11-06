# Round 3 pack: 4 leads (Shyamal, Vistara/Anahata, BLJ/Silver Square, Shree Namasya) - 22 Oct 2026

## 1. Kya taiyaar hai (kuch live nahi hua, kuch bheja nahi)
| Cheez | Status |
|---|---|
| 4 videos (Hale voice, 40-43 s, ~4.4 MB) | Ready: `agent/state/video_v2/<key>/renders/<key>_final.mp4` (Shyamal: `shyamal/renders/shyamal_v2_hale.mp4`) |
| 4 lead-specific pages (naya UI, mobile-first) | Build ho gaye, site checks pass, package ready (38 MB, 13 pages). **Deploy nahi hua** |
| Demo bot config (13 projects, "automatic assistant" wording) | Ready, backend tests 84 pass. **Deploy nahi hua** |
| Emails | 3 drafts ready (Shyamal, Vistara, Namasya). **BLJ ka email nahi mila**, uske liye sirf WhatsApp. Dry-run proposal sab pass |
| WhatsApp msgs | 4 texts neeche (copy-paste) |

## 2. Order (sahi sequence)
1. Tum bolo **"deploy it"** -> main pages + demo config live karta hoon (pehle dry run, phir live, phir check). Iske bina email ka banner link nahi chalega aur WhatsApp ka page link 404 dega.
2. Deploy ke baad main 3 emails ka OK code banata hoon (`propose.py email ... --no-notify`), exact message yahin chat me dikhata hoon. Tum apne WhatsApp se **OK <code>** bhejoge to hi email jayega (har email ka alag code).
3. WhatsApp: neeche 2 raaste.
4. Main har lead ke console entry me `page_url` daal deta hoon taaki page khulna / video play / demo tap tracking me dikhe.

## 3. WhatsApp: buttons wala (demo, page, reply) kaise
**Sach:** apne personal WhatsApp se buttons nahi lag sakte. Buttons sirf API template me aate hain (video header + "See details" page button + "Yes, send the demo" / "No, thanks" quick replies). Dono raaste:

**Raasta A - API template (buttons ke saath, template jaisa):**
- Abhi ka approved `iv_en_realestate_demo_v1` ka text kehta hai "your ads... some buyers may move on to the next developer". Ye hamare naye honesty rule se mel nahi khata (ad ka source batana, dar nahi dikhana). Isliye **naya template `iv_en_realestate_demo_v2`** chahiye. Mera suggested text:
  `Hello! We saw {{2}} ads on Meta that have a Send WhatsApp message button, so IV Infotech made a short video and a page for you. Tap "See details" to open the page, or "Yes, send the demo" to get a short sample chat on WhatsApp from our own number. Reply STOP to opt out.`
  Buttons: See details (URL `/campaign/{{1}}`), Yes, send the demo, No, thanks. Header: video.
- Template banane ke liye tumhara OK + Meta approval (kuch ghante) chahiye.
- **Risk:** pichle cold marketing templates 0/3 deliver hue (Meta 131049). Naye numbers par bhi aisa ho sakta hai. Shyamal, BLJ, Namasya ke numbers "WhatsApp labelled" nahi hain (ho sakta hai WhatsApp par hon hi nahi).

**Raasta B - tumhara personal WhatsApp (jaldi, deliver hone ka chance zyada, par buttons nahi):**
- Video file attach karo + neeche ka text paste karo. Isme 2 links hain: **Page** (tracked) aur **demo link** (tap karte hi hamare number par "Yes, send the demo for ..." message pehle se likha khulta hai, phir hamara automatic bot jawab deta hai). "Reply" = wo seedha tumhe reply karenge, tum khud dekh lo.
- Tracking: page khulna/video play/button tap console me aayega (deploy ke baad), demo tap CRM me session banata hai. Read/reply tumhare phone par.
- Sirf 4 chats hain, isliye ban ka risk kam, par ek ek karke bhejo.

### Raasta B ke texts (copy-paste)

**shyamal (Shyamal Park Lane)**
```
Hello Shyamal Park Lane team, this is IV Infotech from Mehsana. We saw a Diwali ad for Shyamal Park Lane with a Send WhatsApp message button on Meta's public Ad Library, so we made a 40-second video and a short page for Shyamal Park Lane. It shows how a WhatsApp enquiry can get an automatic first reply in about a minute.

Page: https://www.ivinfotech.com/campaign/shyamal-park-lane-k4m8vz
To see the demo on WhatsApp, tap: https://wa.me/15559597730?text=Yes%2C%20send%20the%20demo%20for%20Shyamal%20Park%20Lane

Reply STOP and we will not message again.
```

**vistara (Anahata Florenza)**
```
Hello Vistara team, this is IV Infotech from Mehsana. We saw ads for Anahata Florenza with a Send WhatsApp message button on Meta's public Ad Library, so we made a 40-second video and a short page for Anahata Florenza. It shows how a WhatsApp enquiry can get an automatic first reply in about a minute.

Page: https://www.ivinfotech.com/campaign/vistara-anahata-p7q2xc
To see the demo on WhatsApp, tap: https://wa.me/15559597730?text=Yes%2C%20send%20the%20demo%20for%20Anahata%20Florenza

Reply STOP and we will not message again.
```

**blj (Silver Square)**
```
Hello BLJ Infra team, this is IV Infotech from Mehsana. We saw ads for Silver Square with a Send WhatsApp message button on Meta's public Ad Library, so we made a 40-second video and a short page for Silver Square. It shows how a WhatsApp enquiry can get an automatic first reply in about a minute.

Page: https://www.ivinfotech.com/campaign/blj-silver-square-t9d3wn
To see the demo on WhatsApp, tap: https://wa.me/15559597730?text=Yes%2C%20send%20the%20demo%20for%20Silver%20Square

Reply STOP and we will not message again.
```

**namasya (Shree Namasya)**
```
Hello Shree Namasya team, this is IV Infotech from Mehsana. We saw ads for Shree Namasya with a Send WhatsApp message button on Meta's public Ad Library, so we made a 40-second video and a short page for Shree Namasya. It shows how a WhatsApp enquiry can get an automatic first reply in about a minute.

Page: https://www.ivinfotech.com/campaign/shree-namasya-r5h6jb
To see the demo on WhatsApp, tap: https://wa.me/15559597730?text=Yes%2C%20send%20the%20demo%20for%20Shree%20Namasya

Reply STOP and we will not message again.
```

## 4. Note: boss ka number
Site ke footer me boss ka personal number (9924426361) chhapa hota hai. Naye v2 pages me wo nahi hai, par **pehle se live 9 campaign pages me hai**. Decision chahiye: unko v2 me rebuild karein ya footer se hatayein? (Main bina poochhe nahi karunga.)

## 5. Token aur kharcha (andaza, exact meter nahi)
| Kaam | Tokens (approx) | Alag kharcha |
|---|---|---|
| Main chat (research, pages, emails, Nexus360, packaging) | ~320k | - |
| Video subagent (3 videos) | ~200k | kie.ai 8 credits |
| Page QA workflow | ~420k | - |
| Shyamal video (earlier, main chat me) | included above | kie.ai ~40 credits |
| Apify (ads + pages scrape) | - | ~US$0.46 |
| ElevenLabs | - | tumhare account se |
| **Total** | **~0.95M tokens** | ~US$0.5 + ~48 kie credits |

Per lead (4 leads): ~240k tokens for video + page + email, research alag (pehle ~1.6M per qualified lead enrichment). Sabse mehenga hissa QA workflow tha (~44%), agli baar ek ya do pages par hi QA chalayenge, saare par nahi.

## 6. Tumse chahiye
1. "deploy it" (pages + demo config)?
2. WhatsApp: Raasta A (naya template v2 banau) ya Raasta B (tum khud bhejo) ya dono?
3. Boss-number footer wale 9 pages ka decision.
4. Videos sunke bata do: Vistara/Namasya me koi galat uchcharan to nahi ("Sri Namasya").
