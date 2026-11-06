# -*- coding: utf-8 -*-
"""Follow-up template (iv_en_followup_v1) ke liye owner-approval proposals banata hai: Great Spaces Aaroham aur Swagat Cilantra.
Number campaign_send.py ki wahi logic se aata hai (business-published WhatsApp/phone, boss ka personal number block). Kuch bheja nahi jaata: sirf OK code maangta hai."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "agent" / "tools"))
import campaign_send as cs  # noqa: E402

KEYS = sys.argv[1:] or ["greatspaces", "swagat"]
leads = cs.load_leads()
entries = cs.load_entries()
for key in KEYS:
    lead = leads[key]
    entry = cs.entry_for(lead, entries)
    number, how = cs.pick_number(entry, lead.get("wa_last4")) if entry else (None, "no entry")
    print("== %s -> %s (%s)" % (key, cs.mask(number) if number else "NO NUMBER", how))
    if not number:
        continue
    project = lead.get("wa_project") or lead["project"]
    cmd = [sys.executable, str(REPO / "agent" / "tools" / "propose.py"), "wa-template", "--to", number, "--template", "iv_en_followup_v1", "--lang", "en",
           "--body-param", "%s team" % lead["brand"], "--body-param", project, "--lead", lead["brand"],
           "--reason", "follow-up: they read our earlier WhatsApp message and did not reply", "--no-notify"]
    subprocess.call(cmd, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
