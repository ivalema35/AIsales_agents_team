# -*- coding: utf-8 -*-
"""29 Oct 2026: detailing_verified_leads_2026-10-28.json (decider + independent lead verifier ka output) se console ke entries banata hai:
  detailing-studios-gujarat.campaign.entries.json  (1 campaign entry)
  detailing-studios-gujarat.leads.entries.json     (10 verified leads; Exotic Car Detailing multi-outlet brand hai, isliye nahi)
Push: bash agent/deploy/vps_run.sh agent/deploy/vps_console_push.sh agent/tools/console.py agent/state/campaigns/detailing-studios-gujarat.campaign.entries.json agent/state/campaigns/detailing-studios-gujarat.leads.entries.json
Sirf wahi likhta hai jo verifier ne dekha; kuch invent nahi hota."""
import io
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "detailing_verified_leads_2026-10-28.json").read_text(encoding="utf-8"))
CAMPAIGN_KEY = "detailing-studios-gujarat-2026-10"
CAMPAIGN_NAME = "Car / bike detailing studios: booking + proof page and Google profile upkeep (Gujarat)"

# naam -> (grade, language, safe slot jo literally sach hai, priority note). Order = message bhejne ka order (jinka spend dikha pehle).
PLAN = {
    "Krishna Auto Coating": ("B", "GU", "c: the Google listing has no website button", "Live Meta ad seen (Call now, started 28 Oct); same brand as Krishna Xtreme: message ONE number once."),
    "Detailing Xpert - Gandhinagar": ("B", "GU", "b: the newest Google reviews have no owner reply (4 unanswered)", "Two live click-to-WhatsApp ads seen (26-28 Oct); do not mention the ads."),
    "The Walker's Detailing Studio": ("B", "en", "a: the website button on the Google listing opens a Google sign-in page", "Meta ad seen; do not mention it or the prices in it."),
    "DNX Car Detailing Studio": ("B", "en", "d: the site has a Book Now button but no booking form", "Meta ad seen (page private in the Ad Library)."),
    "Motors Inn - Car Detailing Studio": ("B", "en", "b: the newest Google reviews have no owner reply (5 unanswered)", "Meta ad seen."),
    "Krishna Xtreme Car Detailing Studio, Mehsana": ("B", "GU", "a: the Linktree website link returns 404; b: newest reviews unanswered", "Same brand as Krishna Auto Coating: ONE message to ONE number."),
    "Dwarkesh Car Detailing Studio": ("C", "en", "c: the Google listing has no website button", "No active ad found (exact-name search)."),
    "RRR Detailing": ("C", "GU", "a: the website button opens an Instagram profile, not a website", "No active ad found; owner answers most reviews, so do not use slot b."),
    "Carx Care The Detailing Studio and Service Station (Raysan)": ("C", "GU", "b: the newest Google reviews have no owner reply (5 unanswered)", "No active ad found; possible multi-outlet brand (not confirmed)."),
    "Arihant Car Detailing Studio": ("C", "GU", "c: the Google listing has no website button", "LOWEST priority: only 1 review in the last 12 months, trading unconfirmed."),
}


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return ("detailing-" + s)[:60].rstrip("-")


checks = {c["name"]: c for c in SRC["checks"]}
leads_src = {x["name"]: x for x in SRC["leads"]}
entries = []
for name, (grade, lang, slot, note) in PLAN.items():
    chk, lead = checks[name], leads_src[name]
    phone = (lead.get("published_phone") or "").replace("(published on Maps)", "").strip(" ()")
    phone = re.sub(r"\s*\(.*$", "", phone).strip()
    entries.append({
        "type": "lead",
        "key": slug(name),
        "tags": ["detailing", "round-1"],
        "data": {
            "name": name,
            "city": lead.get("city") or "",
            "product": "Booking + proof page, Google profile clean-up and monthly upkeep, WhatsApp booking set-up",
            "campaign": CAMPAIGN_NAME,
            "campaign_key": CAMPAIGN_KEY,
            "grade": grade,
            "status": "researched",
            "contacted": False,
            "researched": "2026-10-28 (Gujarat scan + independent re-check by a second agent on 28 Oct 2026)",
            "language": lang,
            "language_note": "Gujarati for Mehsana and Gandhinagar, English for Ahmedabad; Hindi if the owner replies in Hindi.",
            "best_channel": "The owner's own WhatsApp, 1:1, to the number the studio publishes on its Google Maps listing. One message per brand, 10-12 new chats a day at most, no links in message 1.",
            "best_angle": "Open with ONE thing literally true on THEIR Google or site page (slot " + slot + "), then ask whether most bookings come through WhatsApp or phone (a one-word reply is enough). Never mention their ads, offers or prices; no price, free, instant, every or guarantee; no owner first name unless the studio's own page shows it. " + note,
            "contacts": [{"kind": "phone", "value": phone, "source": lead.get("url") or chk.get("url"), "note": "Published on the studio's own Google Maps listing (checked 28 Oct 2026); not tested for WhatsApp."}],
            "observed_facts": [chk["what_i_saw"]],
            "hypotheses": ["The pain is inferred, not seen: we see a missing or broken website link, silent reviews and ads that go to WhatsApp or a call, not lost bookings. These studios win customers without a site (see the review counts)."],
            "case_against": "Evidence is one scan of top-ranked studios; the Rs 5k a month fee holds only if the weekly work is visible; free tools exist (Google profile, Linktree, WhatsApp Business).",
            "verification": chk["verdict"],
        },
    })

campaign = [{
    "type": "campaign",
    "key": CAMPAIGN_KEY,
    "tags": ["round-1", "detailing"],
    "data": {
        "name": CAMPAIGN_NAME,
        "product": "Websites and custom software",
        "status": "active",
        "start": "2026-10-29",
        "end": "2026-11-27",
        "unit": "USD",
        "budget_cap": 4.5,
        "budget_used": 0,
        "budget_note": "Owner's Apify budget: about US$4-5 a month in total (ledger agent/state/apify_budget.json). No paid sends: the owner messages 1:1 from his own WhatsApp.",
        "daily_send_cap": 12,
        "target_leads": 46,
        "leads": len(entries),
        "sent": 0,
        "delivered": 0,
        "failed": 0,
        "replies": 0,
        "page_opens": 0,
        "segment": "Owner-run car and bike detailing, coating and PPF studios in Gujarat (Mehsana, Gandhinagar, Ahmedabad first) with a visible gap on their own Google or site page; some already pay for Meta ads that lead to WhatsApp or a call.",
        "offer": "Booking and proof page (packages by car size, before/after, reviews, WhatsApp Book button), Google profile clean-up and monthly upkeep, WhatsApp Business set-up, source-tagged links, a weekly not-yet-booked enquiry list. About Rs 15-25k setup and about Rs 5k a month (the owner decides; never quoted in messages). Smallest paid step: Rs 5,000 Google + WhatsApp booking tune-up in 3 working days, 50% advance.",
        "evidence_methods": [
            "Google Maps scan of 120 Gujarat businesses on 28 Oct 2026: 9 of 11 independent detailing studios had no working own website",
            "Meta Ad Library exact-name checks: 3 of 8 conclusive checks showed an active ad",
            "Independent re-check of 11 named studios on 28 Oct 2026 (10 usable, Exotic Car Detailing held back as a multi-outlet brand)",
        ],
        "rules": "The owner messages 1:1 from his own WhatsApp; nothing is automated. First message = one literally true observation from THEIR own Google or site page + a one-word question; never mention their ads, offers or prices; no price, free, instant, every or guarantee; one message per brand; day-3 follow-up only if the sample already exists; day-7 soft close; STOP is final; 10-12 new chats a day at most from one number; stop and review at 2 blocks. A website is NOT the pitch: sell the booking + proof page and profile upkeep.",
        "validation_plan": "PRE-REGISTERED 28 Oct 2026. Gate 1 Thu 5 Nov 18:00, n = 46 sends (Thu 29 Oct 10, Fri 30 12, Sat 31 12, Mon 2 Nov 12; delivered >= 36): PASS R >= 8 and Q >= 4; KEEP GOING R >= 4 and Q >= 2; PIVOT R <= 3 or Q <= 1 (batch 2 = wedding vendors); KILL R = 0. Gate 2 Fri 27 Nov, n about 96: PASS >= 1 advance of Rs 5,000 or more; KEEP 0 advance but >= 3 calls or demos; PIVOT <= 2 calls and R >= 5; KILL <= 2 calls and R <= 4. No cold sends 6-15 Nov (Diwali about 8 Nov). R = any human reply, Q = owner says the gap matters or asks what / how much, C = call or demo.",
        "waves": [
            {"wave": 1, "group": "Spend seen", "leads": 6, "rule": "studios with a live Meta ad or a broken website link; one message each, first 3 on Thu 29 Oct"},
            {"wave": 2, "group": "Visible gap", "leads": 4, "rule": "no working site or unanswered reviews, no ad seen"},
        ],
        "pack": "agent/docs/FIRST_CLIENT_PACK_DETAILING_2026-10-28.md",
    },
}]

(HERE / "detailing-studios-gujarat.leads.entries.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
(HERE / "detailing-studios-gujarat.campaign.entries.json").write_text(json.dumps(campaign, ensure_ascii=False, indent=1), encoding="utf-8")
print("campaign 1 + leads", len(entries))
for e in entries:
    print(" -", e["data"]["grade"], e["key"], "|", e["data"]["contacts"][0]["value"])
