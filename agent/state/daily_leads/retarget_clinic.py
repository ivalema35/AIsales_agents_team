# -*- coding: utf-8 -*-
"""28 Oct 2026, owner: 'India me koi website dekh kar clinic nahi jata' -> clinic campaign ka product website nahi, WhatsApp patient desk.
Sirf config.json ke clinic-web campaign ke fields badalta hai (baaki campaigns, settings, next_index waise ke waise)."""
import json
from pathlib import Path

p = Path(__file__).parent / "config.json"
c = json.loads(p.read_text(encoding="utf-8"))
for camp in c["campaigns"]:
    if camp["key"] == "clinic-web":
        camp["name"] = "WhatsApp patient desk for doctor-owned clinics (Gujarat)"
        camp["offer"] = ("WhatsApp patient desk: a first reply to each enquiry in about a minute with a booking slot to choose, reminders before the appointment to cut no-shows, "
                         "a 6-month recall message and a review request, with one list for the clinic")
        camp["need"] = ("Doctor-owned clinics (dentist, skin / cosmetic, hair, physio) that already pay for Meta click-to-WhatsApp ads or get their enquiries on WhatsApp and phone, "
                        "and lose patients to slow replies, no-shows and no recall")
        camp["buyer"] = "The doctor-owner of an independent clinic (not a receptionist, not a chain)"
        camp["notes"] = ("A WEBSITE is NOT the pitch (owner: in India patients do not choose a clinic from its website; Dabhi's has 148 five-star reviews and patients without a site). "
                         "Best signal = an active Meta ad with a WhatsApp button (a paid enquiry channel) plus the clinic's own Google Maps listing; also fine: heavy call/WhatsApp-only booking. "
                         "Only leads with a business-published phone/WhatsApp number that plausibly reaches the doctor-owner; skip numbers that are an auto-greeting, a booking desk of a chain or an agency. "
                         "Never email. Prefer dental implants, skin / laser / hair, physio.")
        camp["exclude_types"] = "hospital chains, multi-speciality hospitals, doctors listed only on a platform with no clinic of their own, ayurved polyclinics"
p.write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
print("clinic-web retargeted; next_index =", c["next_index"])
