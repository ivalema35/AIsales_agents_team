# -*- coding: utf-8 -*-
"""29 Oct 2026 (owner ka kehna): clinics campaign hatao, detailing studios ka naya campaign banao. Daily lead task ab sirf detailing campaign chalata hai.
Purane campaigns (ai-auto-re, clinic-web, inst-mgmt, mfg-erp) delete nahi hote: `paused_campaigns` me rakhe jaate hain (runbook sirf `campaigns` padhta hai); wapas laana ho to unhe `campaigns` me daal do.
seen.txt me verified studios jodta hai taaki agents unhe dobara na layen. Dobara chalane par wahi result."""
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))

DETAILING = {
    "key": "detailing-studios",
    "name": "Car / bike detailing studios: booking + proof page and Google profile upkeep (Gujarat)",
    "offer": ("A one-page booking and proof page (packages by car size, before and after photos, Google reviews, a WhatsApp Book button), a Google profile clean-up with monthly upkeep, "
              "and a weekly list of enquiries that are not booked yet. About Rs 15-25k setup and about Rs 5k a month; the owner decides the price and it is never written in a message."),
    "need": ("Owner-run detailing, coating and PPF studios win customers on Google, Instagram and WhatsApp. The gap must be something we can SEE from outside, literally true today: "
             "no working own website; the website button on the Google listing opens a sign-in page, a Linktree or an Instagram profile; the newest 3 Google reviews have no owner reply; "
             "a Book Now button with no booking form. Some studios already pay for Meta ads that lead to WhatsApp or a call (a spend signal). Lost bookings are NOT observed: never claim a loss."),
    "buyer": "The studio owner (decides alone), reachable on the mobile number the studio itself publishes on its Google Maps listing",
    "geo": "Mehsana, Kadi, Visnagar, Patan, Palanpur, Gandhinagar and Ahmedabad first; then Surat, Rajkot, Vadodara, Anand, Nadiad",
    "exclude_types": "franchises and multi-outlet brands (for example CarzSpa, 3M Car Care, Exotic Car Detailing Studio), car dealerships and showrooms, hotels, plain car-wash points with no detailing, accessory shops, studios already verified",
    "notes": ("Pack and rules: agent/docs/FIRST_CLIENT_PACK_DETAILING_2026-10-28.md. Record for every lead: the phone published on Maps, the website status (none / Instagram only / Linktree / own site alive / dead or parked / sign-in wall), "
              "the newest review date and how many of the newest 3 reviews the owner answered, ad status (exact-name Ad Library search only if cheap), brand or franchise flag, and the one safe first-message slot "
              "(a website button opens a broken, sign-in, Linktree or Instagram page; b newest 3 reviews unanswered; c no website button; d Book Now without a form). "
              "A website is NOT the pitch; sell the booking and proof page plus profile upkeep. One message per brand. "
              "APIFY BUDGET: the owner allows about US$4-5 a month in total; follow step 2b of the runbook (ledger agent/state/apify_budget.json), use free tools first, never pull Maps reviews unless needed. "
              "Already verified, do NOT repeat: Krishna Auto Coating, Krishna Xtreme, Detailing Xpert, The Walker's Detailing Studio, DNX Car Detailing Studio, Motors Inn, Dwarkesh Car Detailing Studio, RRR Detailing, "
              "Carx Care (Raysan), Arihant Car Detailing Studio; held back as a multi-outlet brand: Exotic Car Detailing Studio; franchise: CarzSpa Mehsana."),
}

paused = cfg.get("paused_campaigns", [])
paused_keys = {c["key"] for c in paused}
for c in cfg["campaigns"]:
    if c["key"] != DETAILING["key"] and c["key"] not in paused_keys:
        paused.append(c)
cfg["paused_campaigns"] = paused
cfg["campaigns"] = [DETAILING]
cfg["next_index"] = 0
cfg["_about"] = ("Daily lead task ka config. Har din campaigns[next_index % len] chalta hai, phir next_index +1. 29 Oct 2026 se sirf detailing-studios chalta hai; "
                 "baaki purane campaigns `paused_campaigns` me hain (delete nahi hue). Owner is file ko badal sakta hai.")
(HERE / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

seen = (HERE / "seen.txt").read_text(encoding="utf-8").splitlines() if (HERE / "seen.txt").exists() else []
names = ["Krishna Auto Coating", "Krishna Xtreme Car Detailing Studio", "Detailing Xpert", "The Walker's Detailing Studio", "DNX Car Detailing Studio", "Motors Inn Car Detailing Studio",
         "Dwarkesh Car Detailing Studio", "RRR Detailing", "Carx Care The Detailing Studio (Raysan)", "Arihant Car Detailing Studio", "Exotic Car Detailing Studio", "CarzSpa Mehsana"]
add = [n for n in names if n not in seen]
if add:
    with io.open(HERE / "seen.txt", "a", encoding="utf-8", newline="\n") as f:
        f.write(("" if not seen or seen[-1] == "" else "\n") + "\n".join(add) + "\n")
print("campaigns now:", [c["key"] for c in cfg["campaigns"]], "| paused:", [c["key"] for c in cfg["paused_campaigns"]], "| next_index", cfg["next_index"], "| seen +", len(add))
