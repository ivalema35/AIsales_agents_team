# -*- coding: utf-8 -*-
"""28 Oct 2026: clinic campaign ke brief ko demand-research verdict ke hisaab se sudharta hai (agent/docs/CLINIC_DEMAND_RESEARCH_2026-10-28.md).
Verdict INCONCLUSIVE tha: sirf ek sasta test approve hai, build nahi. Isliye daily run ko wahi clinics dhundne hain jo test ke cohorts me aate hain:
doctor-named, 1-3 branches, WhatsApp-opening Meta ad 30+ din se chal raha, Ahmedabad / Surat / Rajkot / Gandhinagar. Offer 'lean desk' hai (recall aur reviews hataye),
pain ko fact ki tarah nahi likhna (unproven). Sirf clinic-web campaign badalta hai, baaki config waisa hi rehta hai. Dobara chalane par wahi result (idempotent)."""
import io
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / "config.json"
cfg = json.loads(PATH.read_text(encoding="utf-8"))

NEW = {
    "offer": ("A lean WhatsApp patient desk: an automatic reply to every enquiry (also when the clinic is closed or busy), the patient picks an appointment slot, "
              "ONE reminder 24 hours before with confirm or reschedule, and one simple list for the clinic. Recall and review requests only later, as paid add-ons. "
              "The first-touch angle is a question (who answers the clinic's WhatsApp number when the clinic is closed?), never a claim about lost patients."),
    "need": ("Doctor-owned clinics (dentist, skin / cosmetic / hair, physio) that already pay Meta for click-to-WhatsApp ads, so they pay for enquiries. "
             "UNPROVEN and still to be tested: that they fail to answer some of those enquiries (after hours, busy chairs) or lose patients to no-shows. "
             "Never write it as a fact about the clinic."),
    "geo": "Ahmedabad, Surat, Rajkot, Gandhinagar (on 28 Oct 2026 Mehsana had 0 independent clinics with WhatsApp ads; Vadodara is thin)",
    "notes": ("Research verdict 28 Oct 2026 (agent/docs/CLINIC_DEMAND_RESEARCH_2026-10-28.md): INCONCLUSIVE, only a cheap test is approved, nothing is built yet. "
              "BEST LEADS = doctor-named clinics with 1-3 branches whose WhatsApp-opening Meta ad has been running 30+ days (Ad Library through the Apify actor "
              "curious_coder/facebook-ads-library-scraper; record the ad's start date), doing high-value work (hair, skin / cosmetic, implants, ortho, physio packages). "
              "Skip chains (3+ branches or 2+ cities), agency-run pages, hospital or booking desks. Also useful: clinics with public reviews about unanswered calls or long "
              "waits (never mention the reviews anywhere). A WEBSITE is NOT the pitch (owner: patients in India do not choose a clinic from its website). Never email. "
              "owner_direct_contact: a doctor-direct number cannot be proven from public data, so 'probably' is enough when the ad, the Maps listing or the Facebook page names "
              "the doctor and the number is a mobile (not a landline, desk or auto-greeting); say 'unknown' otherwise. The first reply confirms it. "
              "Record for every lead: ad start date, specialty, number of branches, who the number belongs to as far as the sources show."),
}

for campaign in cfg["campaigns"]:
    if campaign["key"] == "clinic-web":
        campaign.update(NEW)
        print("clinic-web updated:", ", ".join(NEW))
        break
else:
    raise SystemExit("clinic-web campaign not found")

with io.open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
print("next_index stays", cfg["next_index"], "| campaigns:", [c["key"] for c in cfg["campaigns"]])
