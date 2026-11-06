# -*- coding: utf-8 -*-
"""PROTOTYPE of agent/deploy/crm_detailing_patch.py. Server par chalta hai (vps_crm_detailing.sh se): CRM ki 2 maujooda files me DETAILING reply path ke hooks jodta hai.
Exact-string anchors: agar server ki file local se alag nikli to ANCHOR MISMATCH aata hai AUR KUCH BADALTA NAHI (script pehle ek temp copy par yahi chalati hai).
Idempotent: dobara chalane par jo pehle se laga hai use chhod deta hai.   usage: CRM_DIR=/path/to/backend python3 crm_detailing_patch.py   (Python 3.9 compatible)"""
import os
import sys
from pathlib import Path

B = Path(os.environ.get("CRM_DIR", "/home/sales.ivinfotech.com/aisales/backend"))


def _write(path, text):
    """Python 3.9 on the server: Path.write_text has no newline= argument."""
    with open(str(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def edit(rel, pairs, marker):
    p = B / rel
    s = p.read_text(encoding="utf-8")
    if marker in s:
        print("already patched:", rel)
        return
    for a, b in pairs:
        if s.count(a) != 1:
            sys.exit("ANCHOR MISMATCH in %s (found %d times): %s" % (rel, s.count(a), a[:90]))
        s = s.replace(a, b)
    _write(p, s)
    print("patched:", rel)


# ---- api/inbound.py: import + owner hook + the two lead hooks (a claimed message never reaches the demo or the AI agent)
edit("api/inbound.py", [
    ("from services import demo_responder, owner_channel, sales_agent, wa_tracking",
     "from services import demo_responder, detailing_responder, owner_channel, sales_agent, wa_tracking"),
    ("                            sales_agent.after_owner_message(db, msg, outcome)       # AGENT ON/OFF/TEST/STATUS/RUN; never raises\n",
     "                            sales_agent.after_owner_message(db, msg, outcome)       # AGENT ON/OFF/TEST/STATUS/RUN; never raises\n"
     "                            detailing_responder.after_owner_message(db, msg, outcome)   # DETAILING ON/OFF/TEST/STATUS/RUN + the owner's own tap on a detailing template; never raises\n"),
    ("        demo_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)\n"
     "        sales_agent.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)       # free-text answers (queues only; never raises)\n"
     "        return\n",
     "        if detailing_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted):\n"
     "            return                                    # a detailing-studio lead: the real-estate demo and the AI agent never see this message\n"
     "        demo_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)\n"
     "        sales_agent.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)       # free-text answers (queues only; never raises)\n"
     "        return\n"),
    ("                   keep_unknown_sender=trusted)\n"
     "    demo_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)\n"
     "    sales_agent.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)           # free-text answers (queues only; never raises)\n",
     "                   keep_unknown_sender=trusted)\n"
     "    if detailing_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted):\n"
     "        return                                        # a detailing-studio lead: the real-estate demo and the AI agent never see this message\n"
     "    demo_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)\n"
     "    sales_agent.maybe_handle_lead_message(db, msg, sender, kind, body, trusted)           # free-text answers (queues only; never raises)\n"),
], "detailing_responder")

# ---- services/owner_channel.py: DETAILING commands (ON is the dangerous direction, so every switch must be the WHOLE message)
edit("services/owner_channel.py", [
    ('_AGENT_RUN_RE = re.compile(r"^\\s*agent\\s+run\\s+.{1,300}$", re.IGNORECASE | re.DOTALL)',
     '_AGENT_RUN_RE = re.compile(r"^\\s*agent\\s+run\\s+.{1,300}$", re.IGNORECASE | re.DOTALL)\n'
     '# The detailing-studio reply path (services/detailing_responder.py): DETAILING ON / OFF / TEST / STATUS, and DETAILING RUN [template] (the owner previews the reply on his own phone).\n'
     '_DETAILING_MODE_RE = re.compile(r"^\\s*detailing\\s+(on|off|test|status)\\s*[.!]*\\s*$", re.IGNORECASE)\n'
     '_DETAILING_RUN_RE = re.compile(r"^\\s*detailing\\s+run(\\s+.{1,60}?)?\\s*[.!]*\\s*$", re.IGNORECASE)'),
    ('    if _AGENT_RUN_RE.match(message):\n        return "agent-run"\n',
     '    if _AGENT_RUN_RE.match(message):\n        return "agent-run"\n\n'
     '    match = _DETAILING_MODE_RE.match(message)\n    if match:\n        word = match.group(1).lower()\n'
     '        if word != "status":                                # status never changes the mode\n'
     '            agent_service.set_flag(db, "detailing_mode", word, "owner:" + wamid)\n        return "detailing-" + word\n\n'
     '    if _DETAILING_RUN_RE.match(message):\n        return "detailing-run"\n'),
], "_DETAILING_MODE_RE")
print("done")
