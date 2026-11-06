# -*- coding: utf-8 -*-
"""Final lint of the detailing template (spec + params): banned words in Latin / Devanagari / Gujarati forms, Meta variable rules, lengths, 'demo' phrases.
Run:  PYTHONIOENCODING=utf-8 python agent/state/detailing_wa/_lint_final.py   (read-only, no network)"""
import json, re
from pathlib import Path

H = Path(__file__).resolve().parent
spec = json.loads((H.parent / "outreach" / "detailing_template_v1_spec.json").read_text(encoding="utf-8"))
params = json.loads((H / "params.json").read_text(encoding="utf-8"))
leads = params["leads"]
BANNED = [r"\bfree\b", r"\binstant\b", r"\bevery\b", r"\bgets?\b", r"guarantee", r"\bprice\b", r"your ads", r"\brs\.?\s*\d", "₹", r"\bdemo\b", r"send the demo",
          "मुफ़्त", "मुफ्त", "फ्री", "फ़्री", "तुरंत", "गारंटी", "हर ", "सभी ", "कीमत", "रेट", "क़ीमत", "विज्ञापन", "એડ", "મફત", "તરત", "ગેરંટી", "દરેક", "કિંમત",
          r"\bmuft\b", r"\bturant\b", r"\bgarantee\b", r"\bsabhi\b", r"\bkimat\b"]
problems = []
body = spec["body"]
vars_ = [int(x) for x in re.findall(r"\{\{(\d+)\}\}", body)]
if sorted(set(vars_)) != list(range(1, max(vars_) + 1)):
    problems.append("variables not sequential")
if body.strip().startswith("{{") or body.strip().endswith("}}"):
    problems.append("body starts/ends with a variable")
if re.search(r"\}\}\s*\{\{", body):
    problems.append("adjacent variables")
if len(spec["body_examples"]) != len(set(vars_)):
    problems.append("examples count")
texts = {"body": body, "footer": spec.get("footer", ""), **{"button%d" % i: b["text"] for i, b in enumerate(spec["buttons"])}, **{"example%d" % i: e for i, e in enumerate(spec["body_examples"])}}
for k, t in texts.items():
    for pat in BANNED:
        if re.search(pat, t, re.I):
            problems.append("%s: banned pattern %r" % (k, pat))
for b in spec["buttons"]:
    if len(b["text"]) > 25:
        problems.append("button >25: " + b["text"])
if len(spec["footer"]) > 60:
    problems.append("footer >60")
if "STOP" not in spec["footer"] and not any("STOP" in b["text"] for b in spec["buttons"]):
    problems.append("no STOP")
longest = 0
for r in leads:
    v = r["body_params"]
    if len(v) != 2:
        problems.append("%s: param count" % r["key"]); continue
    for x in v:
        if re.search(r"[\n\r\t]|\s{5,}|\{\{|https?://|\"|​", x) or not x.strip():
            problems.append("%s: bad param %r" % (r["key"], x))
        if len(x) > 150:
            problems.append("%s: param too long" % r["key"])
        for pat in BANNED:
            if re.search(pat, x, re.I):
                problems.append("%s: banned pattern %r in param" % (r["key"], pat))
    rendered = body.replace("{{1}}", v[0]).replace("{{2}}", v[1])
    longest = max(longest, len(rendered))
    if len(rendered) > 540:
        problems.append("%s: rendered %d chars (>540)" % (r["key"], len(rendered)))
print("spec:", spec["name"], spec["language"], spec["category"], "| buttons:", [b["text"] for b in spec["buttons"]], "| footer:", spec["footer"])
print("leads:", len(leads), "| longest rendered:", longest, "chars | fixed body chars:", len(re.sub(r"\{\{\d+\}\}", "", body)))
print("PROBLEMS:", problems or "none")
