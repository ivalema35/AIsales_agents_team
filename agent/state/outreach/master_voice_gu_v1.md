# Gujarati voice script v1.1 (for ElevenLabs) - reviewed by a Gujarati-language check on 2026-10-19. DRAFT for the owner. Nothing is recorded, rendered or sent.

Same 5 scenes as the English video, with the wording fixes the owner list asked for: "can" instead of "gets", reminders only when the buyer says yes, "usually on your own number",
"anyone from your team can join the chat". No price, no promise, no AI / bot / CRM word, and NOT "your ad" (we do not know who runs the ads). Plain words: સવાલ, લિસ્ટ, ફરજિયાત, ટેપ કરો.
The company is spoken "આઈ વી ઇન્ફોટેક" (letters, like the English take). The button text "યસ, સેન્ડ ધ ડેમો" stays English-sounding on purpose (the WhatsApp button and the page say "Yes, send the demo").

## How to make it (one clip per scene; I join them)
1. ElevenLabs -> a calm natural Gujarati voice. Use **Eleven v3** and check that Gujarati is in its language picker. In v3 use the "Natural" (or "Robust") stability setting, NOT "Creative" (Creative improvises; this script must be read exactly).
2. FIRST make a 10 second sample of scene 1 and scene 5 (they hold the two risky pronunciations) and let one Gujarati speaker listen.
   If "આઈ વી" is read as one word, write "આઈ-વી ઇન્ફોટેક". If "સેન્ડ ધ ડેમો" sounds wrong, write the button in Latin letters inside the Gujarati sentence: Yes, send the demo.
3. Then generate each scene as its own clip: `gu_1.mp3` ... `gu_5.mp3` (paste each paragraph below as one clip, no break tags). Put them in `agent/state/outreach/assets/gu/`.
4. Tell me "gujarati clips ready": I join them with 1.0 s of silence, build the timeline and render the Gujarati video (captions below as big on-screen lines per scene, not word-by-word: the speech-to-text step is English only).
5. Commercial use needs an ElevenLabs plan with the commercial licence (open item), and the page must say the voice-over is AI generated. Use it as an extra video link (own noindex page or link), not as a language toggle on the English page.

## Scene 1  (about 10 s)
**Voice:** નમસ્તે, અમે આઈ વી ઇન્ફોટેક, મહેસાણાથી છીએ. રાતે પણ, વોટ્સએપ પરની દરેક ઇન્ક્વાયરીને લગભગ એક મિનિટમાં ઓટોમેટિક જવાબ મળી શકે છે.
Roman (check): Namaste, ame I V Infotech, Mehsana thi chhiye. Raate pan, WhatsApp parni darek inquiry ne lagbhag ek minute ma automatic javab mali shake chhe.
**Caption:** એ જ ઇન્ક્વાયરી. જવાબ લગભગ એક મિનિટમાં.

## Scene 2  (about 6 s)
**Voice:** તે વોટ્સએપ જાહેરાતો સાથે કામ કરે છે, સામાન્ય રીતે તમારા પોતાના નંબર પર.
Roman: Te WhatsApp jaheraato sathe kaam kare chhe, samanya rite tamara potana number par.
**Caption:** વોટ્સએપ જાહેરાતો સાથે, તમારા નંબર પર.

## Scene 3  (about 8 s)
**Voice:** તે બ્રોશર મોકલે છે અને ત્રણ ટૂંકા સવાલ પૂછે છે. પછી સાઇટ વિઝિટનો સમય પસંદ કરવા દે છે.
Roman: Te brochure mokle chhe ane tran tunka saval puchhe chhe. Pachhi site visit no samay pasand karva de chhe.
**Caption:** બ્રોશર. ત્રણ સવાલ. સાઇટ વિઝિટનો સમય.

## Scene 4  (about 17 s)
**Voice:** તમારી ટીમને દરેક ઇન્ક્વાયરી એક જ લિસ્ટમાં દેખાય છે. જેમને વધુ રસ હોય તેવા ગ્રાહકો સૌથી ઉપર હોય છે. ગ્રાહક ચેટમાં હા પાડે, તો પહેલા, ત્રીજા અને સાતમા દિવસે રિમાઇન્ડર મોકલી શકાય છે. તમારી ટીમમાંથી કોઈ પણ ગમે ત્યારે ચેટમાં જોડાઈ શકે છે.
Roman: Tamari team ne darek inquiry ek j list ma dekhay chhe. Jemne vadhu ras hoy teva grahako sauthi upar hoy chhe. Grahak chat ma ha pade, to pahela, trija ane satma divse reminder mokli shakay chhe. Tamari team mathi koi pan game tyare chat ma jodai shake chhe.
**Caption:** એક લિસ્ટ. તમારી ટીમ ગમે ત્યારે જોડાય.
(Shorter version if wanted: drop the second sentence "જેમને વધુ રસ હોય ...".)

## Scene 5  (about 8 s)
**Voice:** તમારા પ્રોજેક્ટ માટે ડેમો જોવો હોય, તો "યસ, સેન્ડ ધ ડેમો" બટન ટેપ કરો. ડેમો મફત છે, અને પછી કંઈ કરવું ફરજિયાત નથી.
Roman: Tamara project mate demo jovo hoy, to "Yes, send the demo" button tap karo. Demo mafat chhe, ane pachhi kai karvu farajiyat nathi.
**Caption:** તમારા પ્રોજેક્ટ માટે ડેમો. કોઈ ફરજ નથી.

About 118 words, about 45-50 seconds (the English video is 37.7 s; the pipeline follows the audio length).
Notes: "મફત" (free) stays only while the owner keeps the demo free (leads.json `demo_free`). The Gujarati wording is softer than the English v2 narration ("can", no "your ads"): the English video is still voiced from v2 (it says "gets" and "your ads"), fix that in the next English take too.
Ask ONE Gujarati speaker to listen to the 10 s samples before the full set is made ("રાતે" vs "રાત્રે", "ગ્રાહક", "નમસ્તે" are the words that need a native ear).
