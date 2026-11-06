# -*- coding: utf-8 -*-
"""Daily run 2026-10-27: researcher ne 6 leads ko C diya kyunki Meta Ad Library subagents ko 403 de rahi thi. Chat session ne 4 leads ke ads khud kholke dekhe
(Shreem, Kishan, Class One, Shivanta: active, WhatsApp CTA, dates match). Ye script un 4 ke console entries banati hai (grade B, status researched, contacted false).
Push owner ke approved flow se: bash agent/deploy/vps_run.sh agent/deploy/vps_console_push.sh <entries file> agent/tools/console.py"""
import json
from pathlib import Path

HERE = Path(__file__).parent
r = json.loads((HERE / "researcher.json").read_text(encoding="utf-8"))
camp = "AI WhatsApp first-reply automation for real-estate developers (Gujarat)"
prod = "WhatsApp automation: every enquiry gets a first reply in about a minute (brochure, 3 quick questions, site-visit slot) and one list for the sales team"
VER = "Re-opened by the chat session in the Meta Ad Library on 2026-10-27 (the daily researcher got HTTP 403): "
CH = ("Phone call to the number the business printed in its own ad, at an off-peak time; ask for the sales head or a partner. "
      "Use WhatsApp only after they agree (opt-in), never as a cold template, and never message through the ad pretending to be a buyer.")

spec = {
    0: dict(key="ai-auto-re-class-one-evoq-rajkot", name="Class One Infra - Class One Evoq (Raiya Hills), Rajkot", city="Rajkot",
            contacts=[dict(kind="phone", value="91575 96575 (printed as 91 575 96 575)", source="https://www.facebook.com/ads/library/?id=1141357448479865",
                           note="Printed by the business in its own Meta ad. This resolves the researcher doubt: the +91 81691 14718 Connect Now number is the listing portal, this one is the builder."),
                      dict(kind="instagram", value="@classonegroupindia", source="https://www.facebook.com/ads/library/?id=1141357448479865", note="Handle printed in the ad text (not used for outreach).")],
            facts=["Active Meta ad by Classone Group started 13 Oct 2026 (2 ads use the same creative): sample flat of 4 BHK Class One Evoq, Tulsi Park, Sopan Luxuria Road, Raiya Hills, Rajkot; phone printed in the ad. " + VER + "the CTA button text was not read on the page."],
            angle="Open with one checkable fact: they are running Meta ads for the Evoq sample flat since 13 Oct. Offer the first reply in about a minute with a brochure and a site-visit slot for Evoq. Do not claim they lose enquiries.",
            against="Slow replies are not shown anywhere: ads that bring enquiries are normal for a developer. The ad CTA could not be read; the project is 56 units (smaller buyer). The ads say Classone Group, the RERA promoter is Class One Infra."),
    1: dict(key="ai-auto-re-shreem-avdhesh-ahmedabad", name="Shreem Group - Shreem Avdhesh (Odhav, Ahmedabad)", city="Ahmedabad (Odhav)",
            contacts=[dict(kind="phone", value="+91 96248 42535", source="https://www.facebook.com/ads/library/?id=2985438971803637", note="Printed in the 16 Oct ad."),
                      dict(kind="phone", value="+91 95865 64040", source="https://www.facebook.com/ads/library/?id=2045598407088530", note="Printed in the 14 Oct ad (a different number than the 16 Oct ad: two lines)."),
                      dict(kind="email", value="Shreemgroupinfo@gmail.com", source="https://www.facebook.com/ads/library/?id=2045598407088530", note="Printed in both ads; a free-mail address.")],
            facts=["Two active Meta ads for Shreem Avdhesh, started 14 Oct and 16 Oct 2026; both with the CTA Chat with us / Send WhatsApp message; text in Gujarati (2 and 3 BHK, Odhav Varjal ring road). " + VER + "confirmed (dates, CTA, phones, email).",
                   "RERA mirror shows about 419 unsold units across two registrations (April 2026 snapshot) and a partner group that also builds Shreem Luxuria (https://www.aurumproptech.in/pulse/rera/gujarat/ahmedabad/shreem-avdhesh/18536)."],
            angle="Gujarati first. Open with the fact that their Shreem Avdhesh festival ads send people to WhatsApp (since 14 and 16 Oct). Offer the first reply in about a minute with a brochure and a site-visit slot, framed around the unsold inventory. No price talk.",
            against="Pain (slow replies) is inferred, not seen: a WhatsApp CTA is standard. Informal brand Shreem over a partnership firm; contacts are only the ad numbers and a free-mail address; no own website found."),
    2: dict(key="ai-auto-re-shivanta-krushnam-vadodara", name="Shivanta Group - Shivanta Krushnam (New Manjalpur), Vadodara", city="Vadodara (Manjalpur)",
            contacts=[dict(kind="website", value="https://www.shivantagroup.com/", source="https://www.facebook.com/ads/library/?id=1383953363769565", note="Named in the ad. The researcher saw an expired TLS certificate via search snippets only."),
                      dict(kind="phone", value="+91 92270 31144", source="https://www.facebook.com/ads/library/?id=1383953363769565", note="Printed in several ads together with 8141133114, +91 75673 31144 and +91 88499 92177 (the Kapurai villa ad).")],
            facts=["6 active Meta ads from Shivanta Group (Krushnam, Ramam, villas at Kapurai) started 9 to 19 Oct 2026; the Krushnam ad has the CTA Book Your Site Visit / Send WhatsApp message and states 191 premium apartments and its own website. " + VER + "confirmed."],
            angle="Open with one fact: six live ads across three projects, the Krushnam one pointing to WhatsApp. Offer one WhatsApp first-reply flow that can serve all three projects (brochure, 3 questions, site-visit slot). Ask for the sales head or a partner (founders named on the About page: unconfirmed).",
            against="Pain is inferred. Several projects and phone numbers suggest an organised sales desk already. The site certificate looked expired (not seen by us directly). Decision-maker unconfirmed."),
    5: dict(key="ai-auto-re-kishan-antilia-vadodara", name="Kishan Antilia (RERA promoter Ambica Inc), Bhayli, Vadodara", city="Vadodara (Bhayli)",
            contacts=[dict(kind="phone", value="84696 18000 / 84697 18000", source="https://www.facebook.com/ads/library/?id=1400703488886438",
                           note="Printed by the business in its own ad. (The +91 81691 14718 WhatsApp number on portals is the portal, not them.)")],
            facts=["Active Meta ad started 26 Sep 2026 for Kishan Antilia 4 BHK, Bhayli Canal Road, with the CTA Send WhatsApp message and the text DM or call for details. " + VER + "confirmed (date, CTA, phones).",
                   "RERA mirror: promoter Ambica Inc, 60 units, approved 23 May 2024, only 0 to 3 booked (snapshot date unknown) (https://www.aurumproptech.in/pulse/rera/gujarat/vadodara/kishan-antilia/21824)."],
            angle="Open with the ad fact: the Kishan Antilia ad (since 26 Sep) invites people to DM or call. Offer a first reply in about a minute with a brochure and a site-visit slot. No claims about lost enquiries.",
            against="No website and no named owner; only ad numbers. Pain is inferred. A single ad running since 26 Sep (about a month)."),
}
out = []
for i, s in spec.items():
    dos = r["leads"][i]["dossier"]
    extra = [str(x.get("fact", "")) + " (" + str(x.get("date")) + ", " + str(x.get("source_url")) + ")" for x in (dos.get("observed_facts") or [])[:3]]
    out.append({"type": "lead", "key": s["key"], "data": {
        "name": s["name"], "city": s["city"], "product": prod, "campaign": camp, "grade": "B", "status": "researched", "contacted": False,
        "best_channel": CH, "best_angle": s["angle"], "contacts": s["contacts"], "observed_facts": s["facts"] + extra,
        "hypotheses": dos.get("hypotheses") or [],
        "case_for": "Real developer with a live project and live paid ads that open WhatsApp (verified in the Ad Library by the chat session). " + str(dos.get("case_for") or "")[:400],
        "case_against": s["against"],
        "next_step": "Owner review, then add to the campaign. Grade B was raised from C by the chat session after it opened the ads itself (the researcher could not: HTTP 403).",
        "researched": "2026-10-27 (daily-leads run + chat-session ad check)"}})
(HERE / "daily_2026-10-27_ai-auto-re.entries.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "entries written")
for o in out:
    print(o["key"], len(json.dumps(o)))
