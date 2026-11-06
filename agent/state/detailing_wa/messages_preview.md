# Detailing WhatsApp template v1 - messages preview (29 Oct 2026)

**Status: DRAFT for the owner's read. Nothing was sent, created, submitted or deployed.** Phone numbers are not in this file.

Files: spec `agent/state/outreach/detailing_template_v1_spec.json` | per-lead values `agent/state/detailing_wa/params.json` | reply texts `agent/state/detailing_wa/reply_texts.json`.

## 0. The three decisions in plain words

**Buttons.** 3 buttons, all quick replies: 'हाँ, बताइए' (yes), 'अभी नहीं' (not now), 'मैसेज बंद करें (STOP)' (stop messages). NO link button (no page exists yet, and a link button next to quick replies stops the template from opening on WhatsApp Web), NO call button (it would publish a company number), and the word 'demo' is on no button and in no text (it would start the real-estate demo flow). Why the STOP button: the real danger of this campaign is the WhatsApp account, not these 9 leads. An annoyed owner with a one-tap STOP does not press Block or Report, and the English letters STOP are the only opt-out the CRM reads by itself. Its effect on yes-taps is unproven (not measurable with 9 sends). Your call: for only 2 buttons, delete the third entry in the spec before the approval code is asked; nothing else changes (the footer still says STOP).

**Language.** ONE template, in Hindi (Devanagari). All three reviewers ranked it first (approval odds about 83 percent against 75 for Gujarati and 60 for Roman-script Hinglish: judgement, unverified), the video voice is Hindi, and every studio owner can read it. Gujarati is the warmest for the 5 Mehsana/Gandhinagar studios, but it would be our first Gujarati template, nobody has proofread the Gujarati, and it has only about 20 characters of headroom. Roman Hinglish declared as English is the likeliest to be rejected (vendors report language-mismatch rejections). A second language is NOT worth submitting now: with 9 leads no language test means anything, and each extra template costs one more OK code. If you want Gujarati later, it takes one OK code and no sends, plus your proofreading (starting point: agent/state/detailing_wa/draft_gu_spec.json, trimmed by about 20 characters). An English fallback is ready in messages_preview.md in case Meta rejects the Hindi. Typed replies follow the lead's language: Hindi by default, Gujarati or Roman variants are in the reply kit.

**Reply to haan / demo.** YES (tap on 'हाँ, बताइए', or typed haan / ok / demo): ONE instant fixed reply (fixed text, nothing is generated; it calls itself an automatic (AI) message to be honest, says a person will write in this chat, and promises no time, price, free, link or phone) plus a hand-off card; then a person asks one question (kit item yes_typed), every reply with your OK code, within 23h45m of the lead's last message. NOT NOW: silence, logged, no second template, number not suppressed. STOP (button or any language): suppress first, then one confirmation. Price, call, questions, references, voice notes: hand-off, no automatic text; the person uses the reply kit. The instant reply is OFF until you send DETAILING TEST or ON from your own WhatsApp, and it needs new CRM code (a prototype with its own tests exists in agent/state/detailing_wa/proto_reply, not re-run here; deploy only on your 'deploy it'). Until then a tap lands as plain inbound text, nobody is alerted while OWNER_QUIET exists, and the attended session must poll `crm.py inbound` and reply by hand. Before any lead: prove on your own number that a button tap opens the 24 h window (tap, then reply free-form at once; error 131047 = it does not).

## 1. The template Meta will review (frozen text)

| Field | Value |
|---|---|
| Name | `iv_detailing_video_hi_v1` (versioned; no v1 existed before) |
| Language / category | `hi` (Devanagari Hindi) / MARKETING |
| Header | VIDEO sample = `assets/SAMPLE_detailing_hi_v1.mp4` (7,189,241 bytes, sha256 starts `1333ef7a7a12cb82`, 720x1280, about 67 s). The video at send time is a public https link. |
| Variables | `{{1}}` = studio short name, `{{2}}` = one literally-true observation (5-sentence dictionary in params.json) |
| Footer | `मैसेज बंद करने के लिए STOP लिखें` (32 chars) |
| Buttons | 3 quick replies: `हाँ, बताइए` (10 chars), `अभी नहीं` (8), `मैसेज बंद करें (STOP)` (21); limit 25 |
| Examples (fictional) | `{{1}}` = Sunrise Car Studio; `{{2}}` = आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा |

Body with placeholders (433 characters):

```text
नमस्ते {{1}} टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: {{2}}।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।
```

## 2. The 9 messages exactly as a lead sees them (suggested send order)

Each block = what appears in the chat: the video on top, the text, the grey footer line, then the three buttons. The line under each block is what must be passed to `send-template`.

### 1. Krishna Auto Coating (Mehsana) - slot c - confidence high

Status: **sendable after the send-day re-check**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Krishna Auto Coating टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Krishna Auto Coating" --body-param "आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा" --lead "Krishna Auto Coating" --lang hi` | body 495 chars

### 2. Walker's Detailing Studio (Ahmedabad) - slot a-signin - confidence high

Status: **sendable after the send-day re-check**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Walker's Detailing Studio टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: आपकी Google लिस्टिंग का वेबसाइट बटन लॉगिन के बिना साइन-इन पेज पर ले जाता है।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Walker's Detailing Studio" --body-param "आपकी Google लिस्टिंग का वेबसाइट बटन लॉगिन के बिना साइन-इन पेज पर ले जाता है" --lead "Walker's Detailing Studio" --lang hi` | body 523 chars

### 3. RRR Detailing (Gandhinagar) - slot a-instagram - confidence high

Status: **sendable after the send-day re-check**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते RRR Detailing टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: आपकी Google लिस्टिंग का वेबसाइट बटन Instagram प्रोफ़ाइल पर खुलता है।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "RRR Detailing" --body-param "आपकी Google लिस्टिंग का वेबसाइट बटन Instagram प्रोफ़ाइल पर खुलता है" --lead "RRR Detailing" --lang hi` | body 503 chars

### 4. Dwarkesh Car Detailing (Ahmedabad) - slot c - confidence high

Status: **sendable after the send-day re-check**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Dwarkesh Car Detailing टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Dwarkesh Car Detailing" --body-param "आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा" --lead "Dwarkesh Car Detailing" --lang hi` | body 497 chars

### 5. Detailing Xpert (Gandhinagar) - slot b - confidence medium

Status: **sendable only after a HUMAN phone check**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Detailing Xpert टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: Google पर आपके सबसे नए 3 रिव्यू के जवाब अभी नहीं दिख रहे।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Detailing Xpert" --body-param "Google पर आपके सबसे नए 3 रिव्यू के जवाब अभी नहीं दिख रहे" --lead "Detailing Xpert" --lang hi` | body 494 chars

### 6. Carx Care (Gandhinagar) - slot b - confidence medium

Status: **sendable only after a HUMAN phone check**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Carx Care टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: Google पर आपके सबसे नए 3 रिव्यू के जवाब अभी नहीं दिख रहे।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Carx Care" --body-param "Google पर आपके सबसे नए 3 रिव्यू के जवाब अभी नहीं दिख रहे" --lead "Carx Care" --lang hi` | body 488 chars

### 7. DNX Car Detailing (Ahmedabad) - slot d - confidence high

Status: **sendable, but send late (thin gap)**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते DNX Car Detailing टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: आपकी वेबसाइट का Book Now कॉन्टैक्ट सेक्शन तक ले जाता है, बुकिंग फ़ॉर्म तक नहीं।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "DNX Car Detailing" --body-param "आपकी वेबसाइट का Book Now कॉन्टैक्ट सेक्शन तक ले जाता है, बुकिंग फ़ॉर्म तक नहीं" --lead "DNX Car Detailing" --lang hi` | body 518 chars

### 8. Motors Inn (Ahmedabad) - slot b - confidence medium

Status: **HOLD if any of the newest 3 reviews now has a reply; otherwise send last**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Motors Inn टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: Google पर आपके सबसे नए 3 रिव्यू के जवाब अभी नहीं दिख रहे।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Motors Inn" --body-param "Google पर आपके सबसे नए 3 रिव्यू के जवाब अभी नहीं दिख रहे" --lead "Motors Inn" --lang hi` | body 489 chars

### 9. Arihant Car Detailing (Mehsana) - slot c - confidence low

Status: **HOLD (do not send unless the dormancy test passes)**

```text
[VIDEO: the reel, plays muted with captions]

नमस्ते Arihant Car Detailing टीम, हम IV Infotech, मेहसाणा से हैं।

ऑनलाइन आपका स्टूडियो देखते हुए हमें एक छोटी-सी बात नज़र आई: आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा।

हम एक सिंपल पेज बनाते हैं: पैकेज, पहले-बाद की फ़ोटो और WhatsApp पर बुकिंग का बटन। साथ में Google प्रोफ़ाइल की देखभाल करते हैं, और सेटअप हम ही करते हैं। ऊपर का वीडियो (करीब एक मिनट, कैप्शन के साथ, AI आवाज़ में) यही दिखाता है।

जानना चाहें तो नीचे "हाँ, बताइए" दबा दीजिए; हमारी टीम का कोई व्यक्ति इसी चैट में बताएगा।

मैसेज बंद करने के लिए STOP लिखें
[ हाँ, बताइए ]
[ अभी नहीं ]
[ मैसेज बंद करें (STOP) ]
```

`--body-param "Arihant Car Detailing" --body-param "आपकी Google लिस्टिंग में वेबसाइट का बटन नहीं दिख रहा" --lead "Arihant Car Detailing" --lang hi` | body 496 chars

## 3. Counts and checks

| # | Studio | Slot | {{1}} chars | {{2}} chars | Rendered body chars | Footer | Buttons |
|---|---|---|---|---|---|---|---|
| 1 | Krishna Auto Coating | c | 20 | 52 | 495 | 32 | 10 / 8 / 21 |
| 2 | Walker's Detailing Studio | a-signin | 25 | 75 | 523 | 32 | 10 / 8 / 21 |
| 3 | RRR Detailing | a-instagram | 13 | 67 | 503 | 32 | 10 / 8 / 21 |
| 4 | Dwarkesh Car Detailing | c | 22 | 52 | 497 | 32 | 10 / 8 / 21 |
| 5 | Detailing Xpert | b | 15 | 56 | 494 | 32 | 10 / 8 / 21 |
| 6 | Carx Care | b | 9 | 56 | 488 | 32 | 10 / 8 / 21 |
| 7 | DNX Car Detailing | d | 17 | 78 | 518 | 32 | 10 / 8 / 21 |
| 8 | Motors Inn | b | 10 | 56 | 489 | 32 | 10 / 8 / 21 |
| 9 | Arihant Car Detailing | c | 21 | 52 | 496 | 32 | 10 / 8 / 21 |

- Rendered body: **488 to 523 characters** (Python len = UTF-16 units here, no emoji). Meta's official limit is 1024. Some vendors report a 550-character ceiling for MARKETING bodies (unverified, and one vendor table says 512); every message is under 550, 7 of 9 are under 512.
- Fixed words: 82. Words between `{{1}}` and `{{2}}`: 18. Two variables only, never adjacent, body starts with a fixed greeting and ends with fixed words, so 'too many variables for the length' and 'dangling parameter' cannot fire.
- Emoji: 0. Script: about 92 percent of the fixed letters are Devanagari; Latin only for IV Infotech, Google, WhatsApp, AI, STOP and the studio name (proper nouns), so the declared language `hi` matches the text.
- `python agent/tools/wa.py create --spec agent/state/outreach/detailing_template_v1_spec.json` (dry run): spec valid.
- Lint over every lead-facing string (template, 3 labels, footer, 9 renderings, auto reply, pause reply, media reply, STOP confirmations, 11 kit items in Hindi, Roman and Gujarati): no price/free/instant/every/gets/guarantee/'your ads' in English, Hindi, Gujarati or Roman forms; no demo/sample/rate/charges wording; no time, working-hours or call-back promise; no link, phone number or emoji; all NFC. Positive controls proved the lint fires.
- The repo's own `sales_agent.check_reply` (rules copied from the source, backend not imported) accepts the automatic texts and every kit text.
- Labels vs the CRM's regexes: `हाँ, बताइए` and `अभी नहीं` are neither a demo trigger nor a STOP; `मैसेज बंद करें (STOP)` is caught as STOP (`hard_classifiers.is_optout` and the hard-stop regex).

## 4. Holds and re-checks before ANY send (details per studio in params.json)

- **Arihant Car Detailing: HOLD.** Send only if a free dormancy test passes (recent review/photo/post). Otherwise skip.
- **Motors Inn: HOLD if any of its newest 3 Google reviews now has an owner reply** (no fallback sentence). Weakest lead: send last.
- **Detailing Xpert, Carx Care, Motors Inn** (reviews sentence): a human must check on a phone that the newest 3 reviews still have no owner reply. Logged-out Maps cannot sort by Newest, so this could NOT be verified on 29 Oct.
- **Walker's:** the curl check must still print 302 to accounts.google.com. **DNX:** the served HTML must still have no form. **RRR:** look at the Instagram handle. **Krishna:** only the Auto Coating listing's own number.
- Every sentence was true when checked on 28-29 Oct; listing facts expire in about 3 days, so re-check on the send day and write the result in the approval reason.

## 5. Test plan before any lead (owner's own number, logged apart from Gate 1)

1. Create + approve the template, then one owner-test send with the longest case (Walker's, 523 chars) labelled `Owner test`.
2. Play the video on a real Android phone and an iPhone (High profile with B-frames may not play on Android WhatsApp: unproven).
3. Tap `हाँ, बताइए`, save the webhook JSON (type, text, payload, context.id), then send a free-form reply at once: error 131047 would mean the tap does NOT open the 24 h window (then no instant reply is possible).
4. On the same message tap `अभी नहीं` and `मैसेज बंद करें (STOP)` (a quick reply stays tappable) and type STOP once; read the status webhooks and the inbox. Afterwards check that his own number did not land on the suppression list.
5. His own tap goes to owner_inbox, so this proves the tap path, not the lead reply flow.
6. Only then lead 1, one at a time: wait about 60 s, read delivered/failed. 131049 or no receipt after 10 min = a strike; 131026 = number not on WhatsApp (log separately, says nothing about the template). 3 strikes in a row = cold templates OFF. Never retry the same number the same day. Day 1: at most 3 sends. Not 6-15 Nov.

## 6. English fallback (use ONLY if Meta rejects the Hindi template)

Name `iv_detailing_video_en_v1`, language `en`, MARKETING, same VIDEO header, footer `Reply STOP to opt out` (already approved twice on this account), buttons `Yes, tell me`, `Not now`, `Stop messages`, every send with `--lang en`. A new name needs a new OK code (a rejected template cannot be edited with wa.py).

```text
Namaste {{1}} team, we are IV Infotech, Mehsana.

While looking at your studio online we noticed one small thing: {{2}}.

We make a simple page (packages, before-after photos, a WhatsApp booking button), look after your Google profile, and do the setup ourselves. The video above (about a minute, captions, AI voice) shows this.

To know more, tap "Yes, tell me" below; a person from our team will explain here in this chat.
```

`{{2}}` in English: c = "the website button is not showing on your Google listing"; b = "replies to your newest 3 Google reviews are not showing yet"; a-signin = "your Google listing's website button opens a sign-in page if you are not logged in"; a-instagram = "your Google listing's website button opens your Instagram profile"; d = "the Book Now on your website goes to a contact section, not to a booking form".

Rendered length 482 to 521 characters. The dry run of this fallback spec is also valid.

## 7. Decisions still needed from the owner

1. Read and freeze the Hindi: body, footer, the 3 button labels, the 2 examples and the 5 observation sentences. Name, text and video bytes are all inside the approval code, so one changed character later = a new template name + a new OK code (Meta allows 1 edit per 24 h). The Gujarati and Roman reply texts are optional reading.
2. Third button: keep 'मैसेज बंद करें (STOP)' (recommended) or go back to 2 buttons?
3. Video: the original has 1,473 B-frames (H.264 High profile); Meta says Android WhatsApp may not play that (unproven). A WhatsApp-safe copy already exists: agent/video/reel_cartoon/renders/detailing_hi_v1_720_wa.mp4 (Main profile, 0 B-frames, moov first, 5.65 MB, same 67 s and audio; I checked the frame types, not the picture quality). Recommended: use it as the Meta sample AND the send file. To switch: copy it to agent/state/outreach/assets/SAMPLE_detailing_hi_v1_wa.mp4 and change header.file in the spec to that path BEFORE the approval code is asked (the video bytes are inside the code; the original stays untouched). Then play the exact file on a real Android phone. A send also needs a public https link: hosting it needs your 'deploy it' (creating the template does not).
4. What does the person send after a 'haan'? The video promises only an explanation. Is a sample page made, and is it free? Until you decide, the reply kit promises neither (sales_kb bans a 'free sample').
5. Reply path: approve deploying the automatic yes-reply module (prototype ready, OFF until you send DETAILING TEST / ON from your own WhatsApp, deploy only on your 'deploy it'), or answer by hand for these 9 (one OK code per reply, within 23h45m, and someone must poll `crm.py inbound`)? Either way first prove on your own number that a button tap opens the 24 h window.
6. Language per lead: Hindi for all 9 (recommended), or also a Gujarati template for the 5 Mehsana/Gandhinagar studios (Krishna Auto Coating, Detailing Xpert, RRR, Carx Care, Arihant)? It needs your Gujarati proofreading and one more OK code; not in v1.
7. Send order and day-1 size: default Krishna Auto Coating, Walker's, RRR, Dwarkesh, Detailing Xpert, Carx Care, DNX, Motors Inn, Arihant last or never, at most 3 on day 1; or 'WhatsApp evidence first': Krishna, Walker's, Detailing Xpert, DNX (Krishna's listing has a WhatsApp booking link; the other three run click-to-WhatsApp ads).
8. Studios you already message from your own number in Gate 1: skip them for the template, or send it as a deliberate follow-up? (one message per brand; the template route is logged as its own channel).
9. Holds: Arihant (skip unless the dormancy test passes), Motors Inn (hold if any of its newest 3 reviews now has a reply), DNX (thin gap: send late or skip). Optional softer fallback sentence for the three review-reply studios, 'Google पर आपके कुछ नए रिव्यू के जवाब अभी नहीं दिख रहे' (it stays true after one or two replies): it is a NEW sentence and needs your OK.
10. The pause: Gate 1 ends Thu 5 Nov and there are no cold sends 6-15 Nov, but marketing messages can be delivered up to 30 days late and a tap can arrive later. Switch DETAILING OFF before 6 Nov, or use the greeting-only reply text in reply_texts.json.
11. Tracking: wa.py logs the 2nd body variable as the CRM 'project', so the ledger will hold the observation sentence and the console will not attach these sends to the studio. Accept it and log each send by hand, or approve a small wa.py / engagement_sync change (needs 'deploy it').
12. Fill in the WhatsApp Business profile (name IV Infotech, city, About, website): a studio owner will tap the sender name before anything else. Also OK a read-only status script so the 3-strikes breaker can see Meta's error code (131049 vs 131026): no tool shows it today.

## 8. Residual risks

1. Delivery and policy (the biggest): this is a cold MARKETING template to Maps numbers that never opted in. Approval is not delivery: campaign 1 delivered 2 of 7 (131049 / 131026) and no wording changes that. Blocks or reports lower the quality of the only WhatsApp account (template paused 3 h, then 6 h, then disabled), which also hurts the real-estate templates. Mitigations: one lead at a time, 60 s wait and a status read, 3 strikes = cold templates OFF, no same-day retry, STOP honoured at once, a log separate from Gate 1.
2. First Hindi template on this WhatsApp account and BSP: Meta approval and the BSP's handling of Devanagari are unverified (my odds: about 83 percent first time, a judgement). If rejected: a new name (the English fallback or _v2) + a new OK code + the review wait (earlier templates took 3 minutes to under an hour).
3. Length: rendered bodies are 488-523 characters (Meta's official limit is 1024). Some vendors report 550 for MARKETING bodies and one table says 512: unresolved. If 512 were real, DNX (518) and Walker's (523) would fail at send time and burn an OK code.
4. Video: the original (High profile, B-frames) may not play on Android WhatsApp (unproven); the Main-profile copy exists but is not wired into the spec yet; a 5.7 to 7.2 MB sample is bigger than anything this BSP upload path has handled (2 MB proven).
5. A button tap is assumed to open the 24 h window (Meta does not document it). The owner's own tap goes to owner_inbox, so his test proves the tap path, not the lead reply flow.
6. Nothing answers a tap in production today, and nobody is alerted while OWNER_QUIET exists. The body promises that a person writes in this chat: that promise must be kept (OK code per reply, within 23h45m), otherwise the window closes and only another cold template is left.
7. Observation truth: every sentence goes stale in about 3 days; the three review-reply sentences cannot be checked logged-out; Walker's link may look fine to its own logged-in owner; Arihant may be dormant; DNX's gap is thin. A false observation is worse than none.
8. Logging blind spot: the second variable is the observation, not a project, so the console shows nothing for these sends (log them by hand).
9. STOP handling: the CRM auto-suppresses only English STOP words. The STOP button and the English word are caught; a typed Hindi or Gujarati stop needs a manual `suppress.py add`. The prototype responder's bare 'बंद' match would also suppress 'office बंद है' and must be tightened before it is deployed. A STOP sent to the owner's personal WhatsApp is invisible to every tool.
10. A burnt OK code is the likeliest operational failure, because the code is spent before Meta checks the parameters: a forgotten `--lang hi` (default en gives error 132001), a newline, tab, 5 spaces or double quote in a value, the wrong number of values, an unreachable video link, a paused template.
11. Timing: today is Thu 29 Oct, Gate 1 closes Thu 5 Nov, no cold sends 6-15 Nov. Still to do in that time: proofread, (video copy), create, review, host the video, owner test, then the sends. Nothing in code enforces the 6-15 Nov pause.
12. The Gujarati and Roman reply texts are not checked by a native speaker; the third button's effect on yes-taps is unproven; a lead who types the exact English phrase 'send the demo' would still start the real-estate demo while DEMO is ON and the detailing responder is not deployed (our texts never use the word).
