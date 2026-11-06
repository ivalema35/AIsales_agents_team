# -*- coding: utf-8 -*-
"""PROTOTYPE mutation check (scratch copy only): puts one deliberate bug at a time into the prototype module / the patched inbound.py, runs the detailing tests, restores the file.
Every mutant must make the tests FAIL. Modelled on backend/tests/mutate_demo.py."""
import os
import subprocess
import sys
from pathlib import Path

B = Path(sys.argv[1])
PY = sys.argv[2]
MOD = B / "services" / "detailing_responder.py"
INB = B / "api" / "inbound.py"
OWN = B / "services" / "owner_channel.py"
FILES = {"MOD": MOD, "INB": INB, "OWN": OWN}
BACKUP = {k: v.read_text(encoding="utf-8") for k, v in FILES.items()}

MUTANTS = [
    ("tap path: claim guard removed", "INB", "        if detailing_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted):\n            return", "        if False:\n            return"),
    ("typed path: claim guard removed", "INB", "    if detailing_responder.maybe_handle_lead_message(db, msg, sender, kind, body, trusted):\n        return", "    if False:\n        return"),
    ("claim returns False when the handler is done", "MOD", "        _handle_lead(db, msg, kind, origin, cfg, phone)\n", "        _handle_lead(db, msg, kind, origin, cfg, phone)\n        claimed = False\n"),
    ("webhook-retry marker removed", "MOD", "    if not _mark(db, \"det:\" + str(wamid)):\n        return                                            # webhook retry", "    if False:\n        return"),
    ("per-template-send marker removed", "MOD", "            if not _mark(db, (\"detsend:\" if cls == \"yes\" else \"detmedia:\") + bucket):", "            if False:"),
    ("STOP ALL ignored", "MOD", "    if agent_service.is_paused(db):\n        return False, \"STOP ALL (paused)\"", "    if False:\n        return False, \"STOP ALL (paused)\""),
    ("mode OFF ignored", "MOD", "    if mode == \"off\":\n        return False, \"automatic reply is OFF\"", "    if False:\n        return False, \"automatic reply is OFF\""),
    ("test mode ignores the number list", "MOD", "    if mode == \"test\" and phone not in demo_responder._test_numbers():", "    if False:"),
    ("STOP does not suppress", "MOD", "        demo_responder._suppress(db, phone)               # always, whatever the mode", "        pass"),
    ("STOP confirmation sent every time", "MOD", "and _mark(db, \"detstop:\" + phone):", "and True:"),
    ("hard-stop check removed", "MOD", "    if typed and demo_responder._is_hard_stop(typed):\n        return \"stop\"", "    if False:\n        return \"stop\""),
    ("suppressed numbers are answered", "MOD", "    if suppressed:\n        _event(db, \"detailing_blocked\"", "    if False:\n        _event(db, \"detailing_blocked\""),
    ("old messages are answered", "MOD", "    return agent_service.utc_now() - sent <= timedelta(hours=WINDOW_HOURS)", "    return True"),
    ("old templates are answered", "MOD", "        return agent_service.utc_now() - agent_service.parse_iso(origin[\"ts\"]) <= timedelta(days=AUTO_REPLY_DAYS)", "        return True"),
    ("a person's reply is ignored", "MOD", "        elif cls == \"yes\" and _human_replied_since(db, origin, phone):", "        elif False:"),
    ("caps ignored", "MOD", "    return day < MAX_AUTO_PER_DAY and mine < MAX_AUTO_PER_PHONE_PER_DAY", "    return True"),
    ("typed yes: any word instead of every word", "MOD", "all(w in vocab for w in words)", "any(w in vocab for w in words)"),
    ("typed yes: question marks allowed", "MOD", " and \"?\" not in typed and", " and"),
    ("unknown label counts as yes", "MOD", "        return \"other\"\n    if _is_yes_text", "        return \"yes\"\n    if _is_yes_text"),
    ("claim by number ignores an open demo", "MOD", "    if demo_responder._active_session(db, phone) is not None:\n        return None", "    if False:\n        return None"),
    ("a campaign-1 context is claimed", "MOD", "            if not _is_detailing_name(origin[\"template\"], cfg):\n                return None", "            if False:\n                return None"),
    ("hand-off skipped", "MOD", "    if not test_send:\n        _handoff(db, origin, phone, reason, brief, \"high\" if cls == \"yes\" else \"normal\")", "    if False:\n        _handoff(db, origin, phone, reason, brief, \"high\" if cls == \"yes\" else \"normal\")"),
    ("config validity ignored", "MOD", "        elif not use_texts or not text:" if False else "        if not use_texts or not text:", "        if not text:"),
    ("owner test run hands off", "MOD", "    if not test_send:\n        _handoff(", "    if True:\n        _handoff("),
    ("owner alert while paused", "MOD", " or agent_service.is_paused(db) or _alerts_today(db)", " or _alerts_today(db)"),
    ("owner command: ON without whole-message rule", "OWN", "(on|off|test|status)\\s*[.!]*\\s*$\", re.IGNORECASE)\n_DETAILING_RUN_RE", "(on|off|test|status)\", re.IGNORECASE)\n_DETAILING_RUN_RE"),
    ("owner tap row not marked processed", "MOD", "    _mark_owner_row_processed(db, wamid)                  # the agent must not answer this tap as if it were chat", "    pass"),
]
survivors = []
try:
    for name, which, old, new in MUTANTS:
        path = FILES[which]
        text = BACKUP[which]
        if text.count(old) != 1:
            print("!! anchor not found exactly once:", name, text.count(old))
            survivors.append(name + " (anchor)")
            continue
        path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        r = subprocess.run([PY, "-X", "utf8", "-m", "pytest", "tests/test_detailing_responder.py", "-q", "-x", "-p", "no:cacheprovider"], cwd=str(B), capture_output=True, text=True,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
        caught = r.returncode != 0
        print("%-52s %s" % (name, "CAUGHT" if caught else "*** SURVIVED ***"))
        if not caught:
            survivors.append(name)
        path.write_text(text, encoding="utf-8", newline="\n")
finally:
    for k, path in FILES.items():
        path.write_text(BACKUP[k], encoding="utf-8", newline="\n")
print("survivors:", survivors or "none")
