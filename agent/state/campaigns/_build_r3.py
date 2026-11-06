# -*- coding: utf-8 -*-
"""Round 3 (21 Oct 2026): workflow result -> raw leads + overrides for make_lead_entries.py.
Yeh sirf local file banati hai (agent/state/campaigns/), console me kuch push nahi karti.
Skeptic ke fact-check fixes yahan lagaye gaye hain (decision maker, hunger lines, must_not_claim)."""
import html
import json
from pathlib import Path

BASE = Path("C:/Users/Administrator/Desktop/AISales_agent_team/agent/state")
SRC = BASE / "intent_test_2026-10-21" / "round3_enrich_output.json"
OUT_RAW = BASE / "campaigns" / "_research_raw_r3.json"
OUT_OVR = BASE / "campaigns" / "r3_overrides.json"
EXTRA = BASE / "campaigns" / "_r3_extra_fields.json"

d = json.loads(SRC.read_text(encoding="utf-8"))
res = d["result"]
en = {e["key"]: e["lead"] for e in res["enriched"]}
dec = {x["key"]: x for x in res["decide"]["decisions"]}


def clean(x):
    """HTML entities (&amp;) saaf karo, har string me."""
    if isinstance(x, str):
        return html.unescape(x)
    if isinstance(x, list):
        return [clean(i) for i in x]
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    return x


def drop_lines(lines, needles):
    return [l for l in lines if not any(n.lower() in l.lower() for n in needles)]


leads = {}
extra = {}
overrides = []

# ---------------- Shyamal ----------------
l = clean(en["shyamal"])
l["decision_maker"] = ("Chirag Ramniklal Tilva and Amitkumar Ramniklal Tilva, both shown as Founder & Director on the About page of shyamalgroup.co.in "
                       "and both listed among the partners of the promoter firm Shree Ganesh Infra Homes on a third-party GujRERA mirror (aurumproptech.in). "
                       "Which of them decides on sales tools is not published.")
l["observed_facts"] = [("21 Oct 2026, Meta Ad Library (own browser tab): 3 active versions of one Diwali creative for Shyamal Park Lane, all started 16 Oct 2026; "
                        "one version has a Send WhatsApp message button, two use a Get quote form; the copy lists three call numbers.")] + \
    drop_lines(l["observed_facts"], ["did not confirm a click-to-whatsapp", "no click-to-whatsapp"])
reasons = l["hunger_reasons"]
reasons[2] = ("+1 funnel gap: the site has no WhatsApp link, chat widget, Meta pixel or CRM trace; the ads feed three routes (a WhatsApp button on one version, "
              "a Get quote form on two, and calls); whether any auto-reply exists behind them is untested.")
l["hunger_reasons"] = reasons
gaps = l["gaps"]
gaps[0] = "Only 1 of the 3 Diwali ad versions has a Send WhatsApp message button (Ad Library, 21 Oct 2026); the other two use a Get quote form."
l["gaps"] = gaps
l["best_angle"] = ("Your Diwali ad for Shyamal Park Lane in Bhayli has a Send WhatsApp message button on one of its three versions. We would like to show you what an "
                   "automatic WhatsApp first reply (brochure, three quick questions, a site-visit slot, hand-over to your team) could look like for that ad.")
l["best_channel"] = "Email first to the business-published address shyamalpark501@gmail.com, sent by a named person at IV Infotech after the owner's OK. No cold WhatsApp template, no website form."
leads["shyamal"] = l
extra["shyamal"] = {
    "must_not_claim": ("Do not say we saw slow or missed replies. Say only that one of the three Diwali ad versions has a Send WhatsApp message button; do not say all their ads are WhatsApp ads "
                       "(the other two use a Get quote form). Do not say they lack a CRM or an auto-reply (untested). Do not state 990 units, 24 buildings or 99.64% as verified "
                       "(third-party mirror with conflicting sources). Refer to the two directors only as 'shown on your About page'."),
    "will_buy_view": l["will_buy_view"],
    "decision_maker_confidence": l["decision_maker_confidence"],
    "whatsapp_path": l["whatsapp_path"],
}
o = dec["shyamal"]
overrides.append({"match": "Shyamal Group", "name": o["display_name"], "slug": o["slug"], "summary": o["summary"], "why_hungry": o["why_hungry"],
                  "next_step": o["next_step"], "language": o.get("language", "en"), "tags": o.get("tags", [])})

# ---------------- Vistara ----------------
l = clean(en["vistara"])
l["decision_maker"] = ("No verified owner. The name Viral Soni appears in the employee preview of the LinkedIn company page (no title seen) and a similarly named designated partner "
                       "exists in aggregator listings for a related LLP; the job poster (an HR manager) is not the decision-maker. Address the Vistara team, name nobody.")
l["decision_maker_confidence"] = "UNKNOWN"
l["observed_facts"] = [("21 Oct 2026, Meta Ad Library (own browser tab): 9 active ads on the Kalrav Farms page (7 started 10 to 16 Oct) and 8 active ads on the Anahata Florenza page "
                        "(17 in total); two Anahata Florenza ads running since 18 Jun 2026 have a Send WhatsApp message button.")] + \
    drop_lines(l["observed_facts"], ["one active meta ad", "one active ad", "only one active"])
l["hunger_reasons"] = [
    "+2 spend now: 17 active ads on 21 Oct 2026 (8 for Anahata Florenza, oldest from 18 Jun; 9 for Kalrav Farms, 7 started 10 to 16 Oct).",
    "+2 urgency: a Real Estate Sales Executive job posted about 17 Oct 2026 (LinkedIn) and new launches (Anahata Florenza, Kalrav Farms 2).",
    "+1 funnel gap: the site has a call/WhatsApp number, forms and a chatbot that only takes name and phone and promises a callback; no instant WhatsApp reply seen (untested).",
    "+2 can pay: 36 villas from about Rs 2.5 crore, several portfolio items, LinkedIn size band 51-200, paid ads plus a sales hire.",
    "+1 reachable: a published call/WhatsApp number and domain emails on the company's own site, each with a source.",
    "-1 resistance: an in-house chatbot already captures leads and an outside web developer could extend it; listings also sit on Square Yards.",
]
l["hunger_score"] = 7
l["hunger_tier"] = "hungry"
l["best_angle"] = ("Your Anahata Florenza ads have a Send WhatsApp message button and have been running since June. An automatic first reply could send the brochure, ask villa "
                   "budget and visit time, offer a site-visit slot and hand the chat to your team.")
l["best_channel"] = "Email first to a business-published domain address (marketing@ or info@vistararealty.com), team-addressed, sent after the owner's OK. No ad number, no enquiry form."
leads["vistara"] = l
extra["vistara"] = {
    "must_not_claim": ("Do not say Vistara is Vadodara-headquartered (the site says Gandhinagar, LinkedIn says Ahmedabad; Vadodara is the Anahata Florenza project site and the sales hire). "
                       "Say the Anahata Florenza ads have a Send WhatsApp message button; do not say slow or missed replies, and do not say they lack a CRM (they have a website chatbot that promises a callback). "
                       "Do not name an owner. Do not attribute the Bangalore pre-leased office ads, the Pune resale-flat ad by 'vistararealty2024' or the UAE company at vistara-group.com to this builder. "
                       "Never repeat the guaranteed-return wording seen in some Kalrav Farms ads."),
    "will_buy_view": l["will_buy_view"],
    "decision_maker_confidence": "UNKNOWN",
    "whatsapp_path": l["whatsapp_path"],
}
o = dec["vistara"]
overrides.append({"match": "Vistara Group", "name": o["display_name"], "slug": o["slug"], "summary": o["summary"], "why_hungry": o["why_hungry"],
                  "next_step": o["next_step"], "language": o.get("language", "en"), "tags": o.get("tags", [])})

# ---------------- BLJ (owner ne rakhne ko kaha; warm, score 5) ----------------
l = clean(en["blj"])
l["decision_maker"] = ("No single owner: BLJ Infra LLP has 11 listed partners. Samirkumar Ratilal Hansalia is Partner 1 on the Aurum RERA mirror (the best person to ask for; "
                       "list order is not proof that he decides on sales tools). Do not call anyone the owner.")
l["hunger_score"] = 5
l["hunger_tier"] = "warm"
l["hunger_reasons"] = [
    "+2 spend now: 3 live Silver Square ads, all started 12 Oct 2026 (9 days), two with a Send WhatsApp message button (Ad Library, 21 Oct 2026).",
    "+0 urgency: the call to action is generic ('Book Your 3 BHK Visit Today') with no deadline, offer or scarcity.",
    "+1 funnel gap: no website; enquiries go only to WhatsApp or a printed call number; no chat widget or form seen (absence of a site, not proof of no CRM).",
    "+2 can pay: a 171-unit RERA project (141 flats and 30 shops per the Aurum mirror) and an 11-partner LLP.",
    "+1 reachable: a sales number printed in BLJ's own ad (Ad Library, 21 Oct 2026).",
    "-1 resistance: no identified sales decision-maker among 11 partners; a produced video suggests an agency or media person may run the ads.",
]
l["observed_facts"] = [("21 Oct 2026, Meta Ad Library (own browser tab): 3 live ads, all started 12 Oct 2026: a Gujarati sample-flat video (two versions, one with a Send WhatsApp message button, "
                        "one with an Instagram-profile button) and one English ad with a Send WhatsApp message button.")] + \
    drop_lines(l["observed_facts"], ["three ads", "3 ads"])[:6]
l["language"] = "gu"
leads["blj"] = l
extra["blj"] = {
    "must_not_claim": ("Do not say anyone is the owner, founder or MD (11-partner LLP); that 77788 11154 is the number behind the ad's WhatsApp button; that enquiries go unanswered, "
                       "or that they lack a CRM or sales team; that an agency runs their ads; that Rs 60-70 lakh is BLJ's price, or that Silver Square has few bookings (the RERA mirror is stale); "
                       "that BLJ built Silver Avenue, 48 Avenue, 36 Avenue or Zen Garden (other promoters); never say we saw their Instagram."),
    "will_buy_view": l["will_buy_view"],
    "decision_maker_confidence": "LIKELY (as the person to ask for; not proven decision-maker)",
    "whatsapp_path": l["whatsapp_path"],
    "kept_at_owner_request": "Warm (5), below the hungry threshold; kept because the owner asked to keep the two leads found on 21 Oct 2026.",
}
overrides.append({"match": "BLJ Infra", "name": "BLJ Infra LLP - Silver Square", "slug": "blj-infra-silver-square",
                  "summary": ("Rajkot LLP with 11 listed partners selling Silver Square (141 flats and 30 shops on a third-party RERA mirror). Three live ads started 12 Oct 2026, "
                              "two with a Send WhatsApp message button; the need for an automatic first reply is inferred from that, not observed as slow replies."),
                  "why_hungry": ["21 Oct 2026: Meta Ad Library shows 3 live Silver Square ads, all started 12 Oct 2026, two with a Send WhatsApp message button.",
                                 "21 Oct 2026: BLJ has no website; enquiries go to WhatsApp or the call number printed in its own Gujarati ad.",
                                 "21 Oct 2026: 141 flats and 30 shops on the Aurum RERA mirror (third-party), so there is real inventory to sell."],
                  "next_step": ("Warm lead kept at the owner's request (score 5, below the hungry threshold). One short human-sent plain message to the sales number printed in its own ad, "
                                "asking to be passed to the partner who handles sales. Nothing is sent without the owner's OK; the unmasked promoter contact on the official GujRERA page is still to be checked."),
                  "language": "gu", "tags": ["rajkot", "click-to-whatsapp", "kept-at-owner-request", "warm"]})

# ---------------- Shree Namasya (owner ne rakhne ko kaha; warm, score 5) ----------------
l = clean(en["namasya"])
l["decision_maker"] = ("Abhijit Rajendra Bhagwat is listed as a partner of the promoter firm Shree Namasya Enterprise (RERA mirror) and as a director of its corporate partner "
                       "Sunfin Realty Pvt Ltd (company-register aggregator); nothing shows that he decides on sales tools.")
l["hunger_score"] = 5
l["hunger_tier"] = "warm"
l["hunger_reasons"] = [
    "+3 spend now: 6 live ads on the Shree Namasya page (started 28 Sep, 8 Oct, 17 Oct) plus 1 on the partner Sunfin Realty page; 4 of the 6 have a Send WhatsApp message button (Ad Library, 21 Oct 2026).",
    "+1 urgency: the site says Newly Launched and the 28 Sep ad has a festive price with a ready sample house; later ads drop the offer.",
    "+0 funnel gap: the ads already open WhatsApp and a partner brokerage answers calls; the site has click-to-call and forms only, no chat widget or CRM trace, but whether an auto-reply exists is untested.",
    "+2 can pay: about 82 flats at Rs 55-60 lakh (roughly Rs 45-49 crore list value of unsold flats; inventory, not cash), live ads and an agency-built site.",
    "+1 reachable: info@shreenamasya.com (mail hosted by Google) and +91 70696 06777 are published on the business's own contact page.",
    "-2 resistance: the partner brokerage Sunfin Realty sells the project through its own call-answering lines and runs its own WhatsApp-button ad.",
]
l["language"] = ""
l["language_note"] = "Mixed: four ads mix Gujarati script with English, two are Roman-script Hindi-English, the website is English. Plain English for a first email."
leads["namasya"] = l
extra["namasya"] = {
    "must_not_claim": clean(l["must_not_claim"]),
    "will_buy_view": l["will_buy_view"],
    "decision_maker_confidence": "LIKELY (partner; not proven to decide on tools)",
    "whatsapp_path": l["whatsapp_path"],
    "kept_at_owner_request": "Warm (5), below the hungry threshold; kept because the owner asked to keep the two leads found on 21 Oct 2026.",
}
overrides.append({"match": "Shree Namasya", "name": "Shree Namasya - Shree Namasya Residency", "slug": "shree-namasya-vadodara",
                  "summary": ("Vadodara developer (promoter firm Shree Namasya Enterprise, 97 units on a third-party RERA mirror) at Atladra-Padra Road. Six live ads on its own page, "
                              "four with a Send WhatsApp message button; a partner brokerage (Sunfin Realty) also sells it by phone. The need is inferred, not observed."),
                  "why_hungry": ["21 Oct 2026: Meta Ad Library shows 6 live ads on the Shree Namasya page (28 Sep, 8 Oct, 17 Oct); four have a Send WhatsApp message button.",
                                 "21 Oct 2026: shreenamasya.com has only click-to-call and forms, no chat widget or CRM trace; whether an auto-reply exists was not tested.",
                                 "21 Oct 2026: the partner brokerage Sunfin Realty answers calls on its own lines, so a 'we handle it ourselves' reply is likely."],
                  "next_step": ("Warm lead kept at the owner's request (score 5). One short email to info@shreenamasya.com addressed to the Shree Namasya team, not a named person; "
                                "nothing is sent without the owner's OK. The broker angle (Sunfin Realty) is a possible second route."),
                  "language": "", "tags": ["vadodara", "click-to-whatsapp", "kept-at-owner-request", "warm", "broker-partner"]})

# ---------------- raw file ----------------
order = ["shyamal", "vistara", "blj", "namasya"]
raw_leads = []
for k in order:
    x = leads[k]
    x["hunger_tier"] = x["hunger_tier"].lower()
    s = sum(int(r.split(" ", 1)[0].replace("+", "")) for r in x["hunger_reasons"])
    assert s == x["hunger_score"], (k, s, x["hunger_score"])
    raw_leads.append(x)
OUT_RAW.write_text(json.dumps({"leads": raw_leads}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
OUT_OVR.write_text(json.dumps(overrides, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
EXTRA.write_text(json.dumps({"keys": {"re-gj-" + o["slug"]: extra[k] for k, o in zip(order, overrides)}}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("written", OUT_RAW.name, OUT_OVR.name, EXTRA.name, [(k, leads[k]["hunger_score"], leads[k]["hunger_tier"]) for k in order])
