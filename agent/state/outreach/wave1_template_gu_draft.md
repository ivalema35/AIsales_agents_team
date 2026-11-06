# Wave 1 - WhatsApp template (Gujarati) - DRAFT for the owner to proofread. Nothing is submitted or sent.

Submit later with:  python agent/tools/wa.py create --spec <spec.json> --live --approval CODE   (needs the sample video file and an OK code)

- name: `iv_gu_realestate_demo_v1`   language: `gu`   category: MARKETING
- header: VIDEO (sample = the master video; at send time each lead gets its own video link as the header parameter)
- variables: {{1}} = how we address them (for example "રોહિતભાઈ" or "Pride Group ના સાહેબ"), {{2}} = project name (for example "Pride Aura")

## Body (max 1024 characters)
```
નમસ્તે {{1}} 🙏

હું ઇન્ફોટેક (Ivinfotech), મહેસાણાથી વાત કરું છું. તમારા {{2}} ની જાહેરાત જોઈ.

રાતે કે ધમાલના સમયે આવેલી enquiry નો જવાબ મોડો મળે, તો ઘણી વાર ગ્રાહક બીજે જતો રહે છે.

તમારા {{2}} માટે અમે એક નાનો વિડિયો બનાવ્યો છે. એમાં સરળ ભાષામાં બતાવ્યું છે કે WhatsApp પર દરેક enquiry ને 1 મિનિટમાં જવાબ કેવી રીતે મળે, તમારી ટીમનો સમય કેવી રીતે બચે અને site visit વધવામાં કેવી રીતે મદદ મળે.

વિડિયો જુઓ અને રસ હોય તો નીચે "હા, Demo મોકલો" દબાવો.
```

## Footer
`બંધ કરવા STOP લખો`   (the English word STOP stays on purpose: the opt-out detection looks for it)

## Buttons
1. URL button, label `વિગતવાર જુઓ`, link `https://www.ivinfotech.com/campaign/{{1}}` (the suffix = the lead's page slug)
2. Quick reply `હા, Demo મોકલો`
3. Quick reply `ના, આભાર`

## Notes for the proofreader
- Please fix any word that sounds unnatural to a Gujarat businessman; keep it short and respectful.
- No price, no claim that THEIR replies are slow (it is a general sentence), no "booked/registered" wording (RERA).
- Marketing templates need the recipient's opt-in under Meta's policy: see the safeguards in agent/memory.md section W.


---
# ADDED 2026-10-16: the lead's OWN marketing language decides the template (Meta checks that the text matches the template language)
Wave 1 = 4 English leads (Pride, Brij, NB Developer, Elenza) + 1 Gujarati lead (Rivanta). So the ENGLISH template is needed first; the Gujarati one above is for Rivanta (and later Trinetra, Somnath).

## English template - name `iv_en_realestate_demo_v1`, language `en`, MARKETING, header VIDEO
Variables: {{1}} = how we address them (for example "Mr. Prajapati" or "Pride Group team"), {{2}} = project name (for example "NB Legacy Tower").
```
Namaste {{1}},

We are IV Infotech, Mehsana. We saw your ads for {{2}}.

When an enquiry arrives at night or in a busy hour and the reply comes late, many buyers move on to the next developer.

We made a short video for {{2}}. In simple words it shows how every WhatsApp enquiry can get a reply within a minute, how your team saves time, and how site visits can grow.

Watch the video, and if it looks useful, tap "Yes, send the demo" below.
```
Footer: `Reply STOP to opt out`
Buttons: URL `See details` -> https://www.ivinfotech.com/campaign/{{1}} (suffix = the lead's page slug); quick replies `Yes, send the demo` and `No, thanks`.
For the premium brands (NB Legacy Tower from Rs 4.50 Cr, Brij) keep the tone calm and respectful, no emojis.
