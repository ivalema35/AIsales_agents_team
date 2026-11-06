# build_proposal.py - builds the Nexus360 proposal from prices.json.
#
# What it does: reads prices.json, fills proposal_assets/proposal_template.html, draws the three SVG diagrams (and an HTML
# twin of each for phone screens), draws the dashboard figures in HTML (so text is real text, not a screenshot),
# embeds fonts + images (so proposal.html is one self-contained file), then renders proposal.pdf (A4), one PNG per PDF page
# and the two HTML views (desktop and phone), and checks that no page overflows.
#
# Run (Windows, Git Bash or PowerShell):
#   C:/ivtools/venv/Scripts/python.exe build_proposal.py            # html + pdf + page PNGs + html views
#   C:/ivtools/venv/Scripts/python.exe build_proposal.py --html     # html only (fast)
#
# Change a price: edit prices.json, run the line above. Nothing is sent anywhere by this script.
import base64, html, json, re, sys, threading, http.server, socketserver, functools
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "proposal_assets"
P = json.loads((ROOT / "prices.json").read_text(encoding="utf-8"))

INK, MUTED, LINE, SOFT, ACC, ACC_SOFT, AMBER, AMBER_SOFT, FAINT = "#14213D", "#4B5563", "#D3D9E2", "#F2F5F3", "#0F5132", "#E1EEE6", "#7A4E00", "#FBF0D4", "#6B7280"


# ---------------------------------------------------------------- number formats
def indian(n):
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if n < 0 else "") + s


def rs(n):
    return "\u20b9" + indian(n)


def rs2(x, d=2):
    return "\u20b9" + f"{x:.{d}f}"


def round_to(n, step):
    return int(round(n / step) * step)


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def png(name):
    return "data:image/png;base64," + b64(ASSETS / name)


def jpg(name):
    return "data:image/jpeg;base64," + b64(ASSETS / name)


def esc(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- derived numbers
G = P["gst_rate"]
pilot, monthly, ro, emp = P["pilot"], P["monthly"], P["research_only"], P["employee"]
assert sum(emp["components"].values()) == emp["all_in_monthly"], "employee components must add up to all_in_monthly"
valid_until = (date(2026, 10, 20) + timedelta(days=P["valid_days"]))
gates = P["pilot_gates"]
N = pilot["builders"]
emp_hour = emp["all_in_monthly"] / emp["hours_per_month"]
emp_per100_low = round_to(100 * emp["research_hours_each_low"] * emp_hour, 100)
emp_per100_high = round_to(100 * emp["research_hours_each_high"] * emp_hour, 100)
sys_per100 = round_to(monthly["fee"] / monthly["builders"] * 100, 1000)


def gst(x):
    return x * G


tokens = {
    "pilot_fee": rs(pilot["fee"]), "pilot_gst": rs(gst(pilot["fee"])), "pilot_total": rs(pilot["fee"] * (1 + G)),
    "pilot_builders": str(N), "pilot_days": str(pilot["days"]), "report_day": str(pilot["report_day"]),
    "reply_window": str(pilot["report_day"] - pilot["days"]), "pilot_touches": str(pilot["max_touches"]),
    "pilot_wa_low": rs(pilot["whatsapp_estimate_low"]), "pilot_wa_high": rs(pilot["whatsapp_estimate_high"]), "pilot_wa_cap": rs(pilot["whatsapp_cap"]),
    "pilot_msgs_low": str(pilot["messages_sent_low"]), "pilot_msgs_high": str(pilot["messages_sent_high"]),
    "numbers_per_builder_high": f"{pilot['numbers_per_builder_high']:.1f}",
    "monthly_fee": rs(monthly["fee"]), "monthly_builders": str(monthly["builders"]), "monthly_status": esc(monthly["price_status"]),
    "monthly_wa_low": rs(monthly["whatsapp_estimate_low"]), "monthly_wa_high": rs(monthly["whatsapp_estimate_high"]), "monthly_wa_cap": rs(monthly["whatsapp_cap"]),
    "monthly_msgs_low": str(monthly["messages_sent_low"]), "monthly_msgs_high": str(monthly["messages_sent_high"]),
    "setup_if_no_pilot": rs(monthly["setup_if_no_pilot"]),
    "alt_retainer": rs(monthly["alt_retainer"]), "alt_per_demo": rs(monthly["alt_per_demo"]),
    "r_small_fee": rs(ro["small"]["fee"]), "r_small_builders": str(ro["small"]["builders"]),
    "r_large_fee": rs(ro["large"]["fee"]), "r_large_builders": str(ro["large"]["builders"]),
    "emp_all_in": rs(emp["all_in_monthly"]),
    "ratio": f"{monthly['fee'] / emp['all_in_monthly']:.1f}",
    "pilot_months": f"{pilot['fee'] / emp['all_in_monthly']:.1f}",
    "valid_until": f"{valid_until.day} {valid_until.strftime('%b %Y')}",
    "meta_rate": rs2(P["whatsapp"]["meta_marketing_inr"], 4), "meta_rate_gst": rs2(P["whatsapp"]["per_message_incl_gst_low"]),
    "provider_rate_gst": rs2(P["whatsapp"]["per_message_incl_gst_high"]),
    "payment_terms": esc(P["payment_terms_text"]), "credit_text": esc(P["credit_text"]), "data_exit_text": esc(P["data_exit_text"]),
    "emp_per100_low": rs(emp_per100_low), "emp_per100_high": rs(emp_per100_high), "sys_per100": rs(sys_per100),
    "emp_hours_low": f"{emp['research_hours_each_low']:.2f}".rstrip("0").rstrip("."), "emp_hours_high": f"{emp['research_hours_each_high']:.2f}".rstrip("0").rstrip("."),
    "emp_minutes_low": str(int(round(emp["research_hours_each_low"] * 60))), "emp_minutes_high": str(int(round(emp["research_hours_each_high"] * 60))),
    "cov_n": str(int(round(N * gates["owner_coverage_pass_share"]))), "cov_pct": str(int(gates["owner_coverage_pass_share"] * 100)),
    "reach_n": str(int(round(N * gates["whatsapp_reach_pass_share"]))), "reach_pct": str(int(gates["whatsapp_reach_pass_share"] * 100)),
    "deliv_pct": str(int(gates["delivery_pass_share"] * 100)),
    "reply_pass": str(gates["genuine_replies_pass"]),
    "c1_sentence": ("Our first campaign contacted 9 builders and has no confirmed genuine reply yet. That is too few to conclude anything."
                    if P["display"]["show_campaign1_reply_count"] else "Our own results so far are too few to conclude anything."),
    "c1_cell": ("None yet for builders. Our first campaign: 9 contacted, no confirmed genuine reply, 2 of 7 templates on time. Too few to conclude."
                if P["display"]["show_campaign1_reply_count"] else "None yet for builders. Our own WhatsApp templates reached 2 of 7 people on time. Too few to conclude."),
    "date": P["date"],
}


def alt_block():
    if not monthly.get("show_alternative"):
        return ""
    r, d = monthly["alt_retainer"], monthly["alt_per_demo"]
    cells = "".join(f'<div><b>{n} demo{"s" if n != 1 else ""}</b><span>{rs(r + d * n)}</span></div>' for n in (0, 2, 3, 5))
    cross = int((emp["all_in_monthly"] - r) / d)
    same = int((monthly["fee"] - r) / d)
    return (f'<div class="card"><h3>Alternative to B: shared risk <span class="tag asm">Option</span></h3>'
            f'<p class="small">Instead of B you can pay <b>{rs(r)} a month plus {rs(d)} for each demo held</b> with an owner-level contact (15 minutes or more, confirmed by you). You choose after the pilot. Same {monthly["builders"]} builders and the same service.</p>'
            f'<div class="demo-strip">{cells}</div>'
            f'<p class="small">Up to {cross} demos a month this costs less than one employee ({rs(emp["all_in_monthly"])}); at {same} demos it costs the same as B. '
            + (f'<b>B itself is about {monthly["fee"] / emp["all_in_monthly"]:.1f} times one employee and is not cheaper on cost alone.</b></p></div>' if monthly["fee"] >= emp["all_in_monthly"]
               else f'<b>B itself costs about {monthly["fee"] / emp["all_in_monthly"]:.1f} times one employee, but it does a different job: it does not close deals or build relationships.</b></p></div>'))


tokens["alt_block"] = alt_block()
tokens["cmp_lead"] = ("On cost alone the monthly run is not cheaper than one employee, and on research alone an employee is cheaper. What decides it is how many real conversations each one produces, which nobody can say yet."
                      if monthly["fee"] >= emp["all_in_monthly"] else
                      "The monthly run costs less than one employee, but it does a different job: it researches, drafts, sends and tracks, and it does not close deals or build relationships. On research alone an employee can still be cheaper. What decides it is how many real conversations each one produces, which nobody can say yet.")
tokens["alt_note"] = ""


# ---------------------------------------------------------------- svg helpers
def t(x, y, text, size=2.9, weight=400, fill=INK, anchor="start", cls="svg-t", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" class="{cls}" {extra}>{esc(text)}</text>'


STEPS = [
    ("RERA register", "shortlist by rules", "shortlist",
     ["We read the public Chhattisgarh RERA list (one request,", "no login) and apply rules you can see: three districts,", "valid registration, housing, private builders, not your", "customers. Today that leaves 72 builders."], ["AUTOMATED"]),
    ("Real-owner research", "and enrichment", "checked records",
     ["For each builder we look for who is behind it, where public", "evidence supports it: its own site, company records and the", "filing. Each record carries VERIFIED, LIKELY or UNKNOWN, a", "source link and a date. A person checks it before any message."], ["A PERSON", "CHECKS"]),
    ("WhatsApp message,", "page and video", "messages sent",
     ["Only where the business published a WhatsApp-capable number:", "a short message from IV Infotech's line with a personalised", "page and a 17-second video. You approve the wording first.", "Every message has a STOP line. Others are not messaged."], ["AUTOMATED"]),
    ("Follow-up", "and tracking", "a builder replies",
     ["One fixed follow-up if there is no reply and no STOP. The", "dashboard shows sent, delivered, read, page opened and", "replied. When a builder replies or taps a button, all", "automatic messages to that builder stop."], ["AUTOMATED"]),
    ("Genuine reply", "handed to you", "",
     ["A typed reply or button tap from a person (not STOP, a", "greeting or an auto-reply) is alerted to you on WhatsApp with", "the exact words, the builder, the owner and what they opened.", "No AI conversation with an owner: you answer."], ["YOU"]),
]


def svg_process():
    W, row_h, gap = 172, 21.2, 3.8
    H = 5 * row_h + 4 * gap
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five steps: RERA register, real-owner research and enrichment, WhatsApp message with page and video, follow-up and tracking, genuine reply handed to Sridhar. No AI conversation with an owner.">',
         f'<defs><marker id="ah" markerWidth="3.2" markerHeight="3.2" refX="2.6" refY="1.6" orient="auto"><path d="M0,0 L3.2,1.6 L0,3.2 z" fill="{INK}"/></marker></defs>']
    for i, (t1, t2, arrow, lines, pill) in enumerate(STEPS):
        y = i * (row_h + gap)
        last = i == 4
        fill = ACC if last else SOFT
        tc = "#FFFFFF" if last else INK
        o.append(f'<rect x="0" y="{y}" width="52" height="{row_h}" rx="2" fill="{fill}"/>')
        o.append(f'<circle cx="7.4" cy="{y + row_h / 2}" r="4.1" fill="{"#FFFFFF" if last else INK}"/>')
        o.append(t(7.4, y + row_h / 2 + 1.5, str(i + 1), 4.2, 700, ACC if last else "#FFFFFF", "middle", "svg-d"))
        o.append(t(14.6, y + row_h / 2 - 0.6, t1, 3.5, 700, tc, "start", "svg-d"))
        o.append(t(14.6, y + row_h / 2 + 3.7, t2, 3.5, 700, tc, "start", "svg-d"))
        ty = y + 5.6
        for j, line in enumerate(lines):
            o.append(t(57.5, ty + j * 4.35, line, 2.9, 400, INK))
        ph = 7.4 if len(pill) == 1 else 9.6
        px, pw = 147, 25
        pfill, pstroke, ptxt = ("#FFFFFF", INK, INK)
        if pill[0] == "A PERSON":
            pfill, pstroke, ptxt = (AMBER_SOFT, "#E2C474", AMBER)
        if pill[0] == "YOU":
            pfill, pstroke, ptxt = (ACC, ACC, "#FFFFFF")
        py = y + (row_h - ph) / 2
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{ph / 2}" fill="{pfill}" stroke="{pstroke}" stroke-width="0.35"/>')
        for k, ptext in enumerate(pill):
            yy = py + ph / 2 + 0.95 + (k - (len(pill) - 1) / 2) * 3.1
            o.append(t(px + pw / 2, yy, ptext, 2.55, 700, ptxt, "middle", extra='letter-spacing="0.15"'))
        if i < 4:
            x = 26
            o.append(f'<line x1="{x}" y1="{y + row_h + 0.4}" x2="{x}" y2="{y + row_h + gap - 0.6}" stroke="{INK}" stroke-width="0.5" marker-end="url(#ah)"/>')
            o.append(t(x + 3, y + row_h + gap / 2 + 1.0, arrow, 2.7, 500, MUTED))
    o.append("</svg>")
    return "".join(o)


def html_process():
    out = []
    for i, (t1, t2, arrow, lines, pill) in enumerate(STEPS):
        cls = "hp-step end" if i == 4 else "hp-step"
        out.append(f'<li class="{cls}"><span class="hp-n">{i + 1}</span><div><b>{esc(t1)} {esc(t2)}</b><p>{esc(" ".join(lines))}</p><span class="hp-pill">{esc(" ".join(pill))}</span></div></li>')
    return '<ol class="html-twin hp">' + "".join(out) + "</ol>"


FUNNEL = [
    ("All registered projects", "", 2173, ""),
    ("In Raipur, Durg or Rajnandgaon", "", 1317, ""),
    ("Registration still valid", "not marked Expired", 1127, ""),
    ("Approved in the last 18 months", "", 146, ""),
    ("Housing projects", "residential, plotted or mixed", 135, ""),
    ("Private builders", "government bodies removed", 131, ""),
    ("Promoter has 3 or fewer projects", "STAND-IN for small or medium", 82, "asm"),
    ("Not already your customer", "NAME MATCH ONLY", 80, "asm"),
    ("One row per builder", "newest registration first", 72, "final"),
]


def svg_funnel():
    W = 172
    rows = FUNNEL
    x0, bw, rh, top = 56, 78, 4.9, 8
    H = top + len(rows) * rh + 1.5
    mx = rows[0][2]
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Funnel from 2,173 registered Chhattisgarh projects to 72 builders, nine visible rules.">']
    o.append(t(0, 3.4, "RULE APPLIED", 2.5, 600, MUTED, "start", extra='letter-spacing="0.2"'))
    o.append(t(x0, 3.4, "PROJECTS LEFT, BARS TO SCALE", 2.5, 600, MUTED, "start", extra='letter-spacing="0.2"'))
    o.append(t(W, 3.4, "REMOVED", 2.5, 600, MUTED, "end", extra='letter-spacing="0.2"'))
    o.append(f'<line x1="0" y1="5.2" x2="{W}" y2="5.2" stroke="{INK}" stroke-width="0.3"/>')
    prev = None
    for i, (rule, sub, n, kind) in enumerate(rows):
        y = top + i * rh
        o.append(f'<line x1="0" y1="{y + rh - 0.2}" x2="{W}" y2="{y + rh - 0.2}" stroke="#E7EBF0" stroke-width="0.25"/>')
        o.append(t(0, y + 3.7, rule, 3.0, 600 if kind == "final" else 500, INK))
        w = max(n / mx * bw, 1.2)
        fill = ACC if kind == "final" else INK
        o.append(f'<rect x="{x0}" y="{y + 0.9}" width="{w:.2f}" height="3.4" rx="0.6" fill="{fill}"/>')
        o.append(t(x0 + w + 1.8, y + 3.85, indian(n), 3.1, 700, ACC if kind == "final" else INK, "start", "svg-d"))
        if sub:
            col = AMBER if kind == "asm" else MUTED
            sx = x0 + w + 12.5 if n < 1000 else x0 + w + 14
            o.append(t(sx, y + 3.75, sub, 2.6, 700 if kind == "asm" else 400, col, extra='letter-spacing="0.08"' if kind == "asm" else ""))
        if prev is not None:
            o.append(t(W, y + 3.7, "\u2212" + indian(prev - n), 2.9, 400, MUTED, "end"))
        prev = n
    o.append("</svg>")
    return "".join(o)


def html_funnel():
    mx = FUNNEL[0][2]
    out, prev = [], None
    for rule, sub, n, kind in FUNNEL:
        w = max(n / mx * 100, 1.5)
        drop = f'<span class="hf-d">\u2212{indian(prev - n)}</span>' if prev is not None else ""
        subtxt = f'<small class="{"asm" if kind == "asm" else ""}">{esc(sub)}</small>' if sub else ""
        out.append(f'<li class="hf-row {kind}"><div class="hf-t"><b>{esc(rule)}</b>{subtxt}</div><div class="hf-b"><i style="width:{w:.1f}%"></i><span>{indian(n)}</span></div>{drop}</li>')
        prev = n
    return '<ol class="html-twin hf">' + "".join(out) + "</ol>"


TL_DAYS = pilot["report_day"]
TIMELINE = [
    ("Your approval and inputs", "bar", 0, 3, INK),
    ("Number, display name, templates (Meta)", "bar", 0, 6, INK),
    ("Research and enrichment, 50 builders", "bar", 1, 6, INK),
    ("Review: you approve records and wording", "dia", 6, 6, AMBER),
    ("First sends, 10 to 25 a day", "bar", 7, 10, INK),
    ("One follow-up if no reply and no STOP", "bar", 10, 13, INK),
    ("Genuine replies handed to you", "bar", 7, TL_DAYS, ACC),
    ("Replies counted to Day 17, then report and decision call", "dia", TL_DAYS, TL_DAYS, AMBER),
]


def svg_timeline():
    W = 172
    x0, x1 = 62, 168
    dx = (x1 - x0) / TL_DAYS
    rh, top = 6.8, 8
    rows = TIMELINE
    H = top + len(rows) * rh + 2
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Timeline from Day 0 to Day {TL_DAYS}: inputs and approval, number and templates, research, review on Day 6, first sends from Day 7, follow-up, hand-off, replies counted to Day {TL_DAYS}, report on Day {TL_DAYS}.">']
    for d in range(0, TL_DAYS + 1, 1):
        x = x0 + d * dx
        major = d % 2 == 0
        o.append(f'<line x1="{x:.2f}" y1="{top - 1.5}" x2="{x:.2f}" y2="{H - 1}" stroke="{"#E7EBF0" if major else "#F1F3F6"}" stroke-width="0.25"/>')
        if major or d == TL_DAYS:
            o.append(t(x, 3.2, str(d), 2.7, 600, MUTED, "middle"))
    o.append(t(x0 - 2, 3.2, "DAY", 2.6, 600, MUTED, "end", extra='letter-spacing="0.2"'))
    # the two weeks of work end on Day 14, the reply window runs on to Day 17
    xa, xb = x0 + pilot["days"] * dx, x0 + TL_DAYS * dx
    o.append(f'<rect x="{xa:.2f}" y="{top - 1.5}" width="{xb - xa:.2f}" height="{H - top - 0.5}" fill="#F2F5F3"/>')
    o.append(t((xa + xb) / 2, H - 0.6, "reply window", 2.55, 600, MUTED, "middle", extra='letter-spacing="0.1"'))
    for i, (label, kind, a, b, col) in enumerate(rows):
        y = top + i * rh
        o.append(t(0, y + 4.25, label, 2.85, 500, INK))
        if kind == "bar":
            xa2, xb2 = x0 + a * dx, x0 + b * dx
            o.append(f'<rect x="{xa2:.2f}" y="{y + 1.2}" width="{xb2 - xa2:.2f}" height="3.6" rx="0.7" fill="{col}"/>')
        else:
            x = x0 + a * dx
            c = y + 3.0
            o.append(f'<path d="M{x:.2f},{c - 2.5} L{x + 2.5:.2f},{c} L{x:.2f},{c + 2.5} L{x - 2.5:.2f},{c} Z" fill="{col}"/>')
            tx = x - 4.0 if a >= TL_DAYS - 2 else x + 4.0
            o.append(t(tx, c + 1.0, f"Day {a}", 2.8, 700, col, "end" if a >= TL_DAYS - 2 else "start"))
    o.append("</svg>")
    return "".join(o)


def html_timeline():
    out = []
    for label, kind, a, b, col in TIMELINE:
        left = a / TL_DAYS * 100
        width = max((b - a) / TL_DAYS * 100, 2.2)
        cls = "dia" if kind == "dia" else ("acc" if col == ACC else "")
        day = f"Day {a}" if kind == "dia" else f"Day {a} to {b}"
        out.append(f'<li class="ht-row {cls}"><div class="ht-t"><b>{esc(label)}</b><small>{day}</small></div><div class="ht-b"><i style="left:{left:.1f}%;width:{width:.1f}%"></i></div></li>')
    return '<ol class="html-twin ht">' + "".join(out) + "</ol>"


# ---------------------------------------------------------------- dashboard figures drawn in HTML (sample, invented numbers)
PIPE = [  # (group, n, name, count, bar share, note)
    ("Research", 1, "Researched", 50, 1.0, "all in the batch"),
    ("Research", 2, "Real owner named", 30, 0.60, "60% of the step before"),
    ("Research", 3, "Ready to send", 16, 0.32, "53%. Number and text approved"),
    ("WhatsApp", 4, "Sent", 15, 0.30, "94%. 1 still queued"),
    ("WhatsApp", 5, "Delivered", 7, 0.14, "47%. Meta limits cold messages"),
    ("WhatsApp", 6, "Read", 4, 0.08, "57%"),
    ("WhatsApp", 7, "Page opened", 2, 0.04, "50%"),
    ("Conversation", 8, "Replied", 2, 0.04, "1 genuine, 1 automatic greeting"),
    ("Conversation", 9, "Handed off to you", 1, 0.02, "genuine replies only"),
]


def html_pipeline():
    rows, last = [], None
    for g, n, name, cnt, k, note in PIPE:
        first = g != last
        last = g
        end = " end" if n == 9 else ""
        grp = f'<span class="pg">{g}</span>' if first else '<span class="pg"></span>'
        rows.append(f'<div class="pr{" first" if first else ""}{end}">{grp}<span class="pn">{n}</span><span class="pnm">{esc(name)}</span>'
                    f'<span class="pb"><i style="width:{k * 100:.0f}%"></i></span><span class="pc">{cnt}</span><span class="pnt">{esc(note)}</span></div>')
    return ('<div class="pipe-fig"><div class="pf-head"><b>Pipeline: where every builder stands</b><span class="tag sample big">Sample: invented numbers</span></div>'
            f'<div class="pl">{"".join(rows)}</div>'
            '<p class="pf-foot"><b>A first batch of 50 builders. Not a forecast and not from any real send.</b> Delivery to cold numbers is limited by Meta, so delivered is below sent. Builders with no WhatsApp-capable published number are not messaged; they stay as researched records. The last stage is a person, not the system.</p></div>')


def html_leadcard():
    tick1 = '<svg class="tk" viewBox="0 0 12 11"><path d="M1.5 6.2l3.3 3.3L10.5 1.8"/></svg>'
    tick2 = '<svg class="tk" viewBox="0 0 18 11"><path d="M1.5 6.2l3.3 3.3L11 1.8M6.8 6.2l3.3 3.3L16.3 1.8"/></svg>'
    i_page = '<svg class="tk" viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/></svg>'
    i_chat = '<svg class="tk" viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/></svg>'
    i_bell = '<svg class="tk" viewBox="0 0 24 24"><path d="M6 16v-5a6 6 0 0112 0v5l2 2H4z"/><path d="M10 21h4"/></svg>'
    i_user = '<svg class="tk" viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-4 3.5-6 7-6s7 2 7 6"/></svg>'
    ev = [
        ("Day 0, 10:42", "k0", tick2, "<b>Message sent, reached their phone</b><small>Video and page link, from the IV Infotech WhatsApp line</small>"),
        ("Day 0, 13:05", "kb", i_page, "<b>Opened the message, then the page</b><small>Page opened 2 times in total</small>"),
        ("Day 1, 09:18", "kr", i_chat, '<b>They wrote back</b><span class="qt">"Excel mostly. Send me the details."</span>'),
        ("Day 1, 09:18", "kh", i_bell, "<b>Genuine reply: you are alerted on WhatsApp</b><small>All automatic messages to this builder stop</small>"),
        ("Day 1, 09:40", "kh", i_user, "<b>You took over</b><small>You reply yourself from here</small>"),
    ]
    tl = "".join(f'<li class="{k}"><span class="w">{w}</span><span class="mk">{m}</span><p>{txt}</p></li>' for w, k, m, txt in ev)
    return ('<div class="lead-fig"><div class="lf-head"><span class="av">ER</span><div class="lf-t"><b>Example Realty Pvt Ltd</b><span>Sample Residency &middot; Raipur &middot; plotted development</span></div><span class="ho-pill">Handed off to you</span></div>'
            '<div class="lf-body"><div class="lf-col"><h5>Who is behind it <span class="tag sample">Sample</span></h5><ol class="who">'
            '<li><i class="pt"></i><span class="r">Company on the RERA register</span><b>Example Realty Pvt Ltd</b><span class="e">Source: RERA register</span></li>'
            '<li><i class="pt"></i><span class="r">Runs the project day to day</span><b>Anil Sharma <em>(example name)</em></b><span class="e">Sales head. Source: company website</span></li>'
            '<li class="own"><i class="pt"></i><span class="r">Owner and decision-maker</span><b>Rakesh Verma <em>(example name)</em></b><span class="chip lik">&#9680; Likely</span><span class="e">Director. Sources: company website, a local news item</span></li></ol>'
            '<div class="route"><span>Goes to the owner&#39;s number ending <code>4821</code>, from the company website. The RERA contact ending <code>0917</code> is set aside: it reaches the office.</span></div></div>'
            f'<div class="lf-col"><h5>Since we messaged them <span class="tag sample">Sample</span></h5><ol class="tl">{tl}</ol></div></div></div>')


tokens["pipeline_fig"] = html_pipeline()
tokens["lead_fig"] = html_leadcard()


# ---------------------------------------------------------------- tables
CONF = {"ver": ("Verified", "ver", "✓"), "lik": ("Likely", "lik", "◐"), "unk": ("Unknown", "unk", "○")}
WA = {"yes": ("Wired for WhatsApp", "wa-y"), "rera": ("RERA mobile only", "wa-r"), "none": ("None found", "wa-n")}


def conf_chip(k):
    name, cls, icon = CONF[k]
    return f'<span class="chip {cls}">{icon} {name}</span>'


def table_records():
    # show_owner_names=false in prices.json: no private individual's name is printed anywhere (owner decision, review of 20 Oct)
    show = P["display"]["show_owner_names"]
    rec = [
        ("Dee Vee Projects Ltd", "Raipur", "Authorised officer, not a listed director",
         "A whole-time director named on the company's own site; the director lists disagree.", "Dinesh Kumar Patel", "lik", "none",
         "Landlines and a role inbox. A large group."),
        ("Biltech Estates", "Bhilai", "Owner-level: matches the group's managing director",
         "Managing director of Biltech Engineers Pvt Ltd. The link to this firm is inferred (shared address, name).", "Manish Gupta", "lik", "yes",
         "An enquiry line, not his own."),
        ("Sendh Integrated Project Pvt Ltd", "Raipur", "Authorised officer, not a director",
         "Directors of a larger group.", "Shrawan Agrawal and Ayush Agrawal", "lik", "none",
         "A project sales line. A large group."),
        ("Family firm", "Dongargarh", "A promoter; the filed email looks like an adviser's",
         "The family promoters.", "", "lik", "rera",
         "WhatsApp on that mobile not confirmed."),
        ("New private company", "Naya Raipur", "Unknown", "Not found.", "", "unk", "none",
         "Not messaged."),
        ("Individual promoter", "Rajnandgaon", "The promoter; the filed email is another firm's", "Not found beyond the promoter.", "", "unk", "none",
         "Not messaged."),
    ]
    rows = []
    for b, loc, c, o_role, o_name, k, wa, route in rec:
        owner = esc(o_role)
        if show and o_name:
            owner += f"<br><b>{esc(o_name)}</b>"
        owner += f'<span class="cf">{conf_chip(k)}</span>'
        wlabel, wcls = WA[wa]
        rows.append(f'<tr><td class="lab" data-label="Builder, as on the register">{esc(b)}<span class="sub">{esc(loc)}</span></td>'
                    f'<td data-label="Who the RERA contact is (our reading)">{esc(c)}</td>'
                    f'<td data-label="Real owner or decision-maker, and confidence">{owner}</td>'
                    f'<td data-label="WhatsApp-capable published number?"><span class="wa {wcls}">{wlabel}</span>{esc(route)}</td></tr>')
    head = ("<thead><tr><th style='width:30mm'>Builder, as on the register</th><th style='width:38mm'>Who the RERA contact is (our reading)</th>"
            "<th style='width:56mm'>Real owner or decision-maker</th><th>WhatsApp-capable published number?</th></tr></thead>")
    return f'<table class="t rec" style="margin-top:1.4mm">{head}<tbody>{"".join(rows)}</tbody></table>'


def table_gates():
    rows = [
        ("1  Owner coverage", "Builders with a named owner or decision-maker and a source (Verified or Likely). Our test: 4 of 6.",
         f"<b>{tokens['cov_n']} of {N}</b> or more ({tokens['cov_pct']}%)", "Narrow the segment or add research before any monthly run."),
        ("2  Builders with a WhatsApp-capable published number", "A published number wired for WhatsApp, or a promoter's RERA-filed mobile. Our test: 1 of 6 wired, 1 more RERA mobile.",
         f"<b>{tokens['reach_n']} of {N}</b> or more ({tokens['reach_pct']}%)", "WhatsApp alone does not fit this market. The first touch moves to a person phoning the office line."),
        ("3  Delivery", "Messages delivered to owner-level numbers, divided by messages sent to them. Not \"on time\". Our first campaign: 2 of 7 on time.",
         f"<b>{tokens['deliv_pct']}%</b> or more", "Change the number, the channel or the first touch."),
        ("4  Genuine owner-level replies", "A real two-way reply from an owner or decision-maker, typed or a button tap, including those you log or forward from your own number. STOP, auto-replies, greetings and wrong numbers do not count.",
         f"<b>{tokens['reply_pass']}</b> or more", "None: we do not recommend the monthly run. We offer the research-only list, or we stop."),
        ("5  Line health and hand-off", f"Meta quality rating and any restriction, read on Day {pilot['report_day']}. Each genuine reply alerted to you, with the minutes from reply to alert.",
         "No warning or restriction. Every genuine reply alerted", "Pause sends and use a separate number. We report each miss and fix the route."),
    ]
    body = "".join(f'<tr><td class="lab" data-label="Measure">{a}</td><td data-label="How it is counted">{b}</td><td data-label="Pass">{c}</td><td data-label="If not met">{d}</td></tr>' for a, b, c, d in rows)
    head = "<thead><tr><th style='width:30mm'>Measure</th><th style='width:66mm'>How it is counted</th><th style='width:28mm'>Pass</th><th>If not met</th></tr></thead>"
    return f'<table class="t gates" style="margin-top:1.4mm">{head}<tbody>{body}</tbody></table>'


def table_price():
    pf, mf, rs_, rl = pilot["fee"], monthly["fee"], ro["small"], ro["large"]
    pb, mb = pilot["builders"], monthly["builders"]
    la, lb, lc = "A. Pilot", "B. Monthly run", "C. Research-only"

    def arith(fee, n):
        return f"{n} builders \u00d7 {rs(fee / n)} = {rs(fee)}"

    head = (f'<thead><tr><th class="rowh"></th>'
            f'<th class="rec">A. Two-week pilot<small>Recommended first step</small></th>'
            f'<th>B. Monthly managed run<small>After the pilot, if you want it</small></th>'
            f'<th>C. Research-only list<small>No messages sent. Lowest risk</small></th></tr></thead>')
    r = []
    r.append(f'<tr><th class="rowh">Scope</th><td class="rec" data-label="{la}">{pb} builders over {pilot["days"]} days, replies counted to Day {pilot["report_day"]}: research, page, video, WhatsApp where a number is published, hand-off, dashboard, report.</td>'
             f'<td data-label="{lb}">{mb} unworked builders a month, with a weekly report and a monthly review call.</td>'
             f'<td data-label="{lc}">One row per builder: real owner, sources, best route, confidence.</td></tr>')
    r.append(f'<tr><th class="rowh">Fee, proposed,<br>before GST</th><td class="rec" data-label="{la}"><span class="big">{rs(pf)}</span><span class="unit">once, fixed, due whether or not builders reply. {arith(pf, pb)}</span></td>'
             f'<td data-label="{lb}"><span class="big">{rs(mf)}</span><span class="unit">per month, stop at the end of any month. {arith(mf, mb)}. <b>Indicative:</b> confirmed in writing after the pilot.</span></td>'
             f'<td data-label="{lc}"><span class="big">{rs(rs_["fee"])}</span><span class="unit">for {rs_["builders"]} builders ({rs_["builders"]} \u00d7 {rs(rs_["fee"] / rs_["builders"])}), or {rs(rl["fee"])} for {rl["builders"]} ({rl["builders"]} \u00d7 {rs(rl["fee"] / rl["builders"])})</span></td></tr>')
    r.append(f'<tr><th class="rowh">With 18% GST</th><td class="rec" data-label="{la}"><span class="total">{rs(pf * (1 + G))}</span> ({rs(pf)} + {rs(gst(pf))})</td>'
             f'<td data-label="{lb}"><span class="total">{rs(mf * (1 + G))}</span> per month ({rs(mf)} + {rs(gst(mf))})</td>'
             f'<td data-label="{lc}"><span class="total">{rs(rs_["fee"] * (1 + G))}</span> or <span class="total">{rs(rl["fee"] * (1 + G))}</span></td></tr>')
    r.append(f'<tr><th class="rowh">WhatsApp fees<br>at cost, extra</th><td class="rec" data-label="{la}">About {rs(pilot["whatsapp_estimate_low"])} to {rs(pilot["whatsapp_estimate_high"])}, capped at {rs(pilot["whatsapp_cap"])}</td>'
             f'<td data-label="{lb}">About {rs(monthly["whatsapp_estimate_low"])} to {rs(monthly["whatsapp_estimate_high"])} a month, capped at {rs(monthly["whatsapp_cap"])}</td><td data-label="{lc}">None. Nothing is sent.</td></tr>')
    r.append(f'<tr><th class="rowh">Included</th><td class="rec" data-label="{la}"><ul><li>A checked research record per builder</li><li>One master video, a personalised page, up to {pilot["max_touches"]} WhatsApp messages each</li>'
             f'<li>Every genuine reply to you, a dashboard, a Day {pilot["report_day"]} report</li></ul></td>'
             f'<td data-label="{lb}"><ul><li>Everything in A, for unworked builders</li><li>Template and number upkeep</li></ul></td>'
             f'<td data-label="{lc}"><ul><li>Research records, a CSV and a dashboard view</li><li>One correction round in 14 days</li></ul></td></tr>')
    r.append(f'<tr><th class="rowh">Not included</th><td class="rec" data-label="{la}"><ul class="no"><li>Any promise of replies, demos or customers</li><li>Email, calls, ads, other states, CRM integration, a licensed registry data source</li></ul></td>'
             f'<td data-label="{lb}"><ul class="no"><li>As A</li><li>We suggest it only if the pilot measures are met</li></ul></td>'
             f'<td data-label="{lc}"><ul class="no"><li>Video, page, messages, hand-off</li><li>A promise that every owner can be reached</li></ul></td></tr>')
    return f'<table class="price">{head}<tbody>{"".join(r)}</tbody></table>'


def table_cmp():
    e = emp
    cmpv = list(e["components"].values())  # fixed pay, PF, incentive, phone/laptop, hiring+ramp (order as in prices.json)
    rows = [
        ("Monthly cost<br><span class='tag asm'>Assumption</span>",
         f"<b>{rs(e['all_in_monthly'])}</b> all-in (band {rs(e['band_low'])} to {rs(e['band_high'])}): pay {rs(cmpv[0])}, PF {rs(cmpv[1])}, incentive {rs(cmpv[2])}, phone and laptop {rs(cmpv[3])}, hiring and ramp {rs(cmpv[4])}. Excludes travel, gratuity and leave.",
         f"<b>{rs(monthly['fee'])}</b> a month for the run (indicative), after a {rs(pilot['fee'])} pilot, plus WhatsApp fees. About {tokens['ratio']} times one employee.",
         f"With you closing: the system fee only. With an executive: {rs(monthly['fee'])} + {rs(e['all_in_monthly'])} = <b>{rs(monthly['fee'] + e['all_in_monthly'])}</b>."),
        ("Time to start<br><span class='tag asm'>Assumption</span>",
         "4 to 8 weeks to hire, then about 3 months to full speed.",
         "First sends about 7 days after we have your inputs, subject to Meta's approvals.",
         "As the system. A hire adds the hiring time."),
        ("Cost per 100 builders researched<br><span class='tag asm'>Assumption</span>",
         f"{tokens['emp_per100_low']} to {tokens['emp_per100_high']}, at {tokens['emp_minutes_low']} to {tokens['emp_minutes_high']} minutes per builder. No human timing was taken.",
         f"About {tokens['sys_per100']}, including messaging, follow-up, dashboard and hand-off. Our own staff time is assumed at 4.5 minutes per builder; a manual registry lookup can take 5 to 10. <b>On research alone an employee is cheaper.</b>",
         "Both costs."),
        ("Talking to owners",
         "Yes: phone, visits, Hindi and local dialect, objections. Can confirm by phone who the owner is.",
         "No, by design. Every genuine reply goes to you.",
         "You or the executive."),
        ("Records, and if it stops",
         "Depends on discipline. If the person leaves, contacts leave unless logged.",
         "A source and date for every fact; every send and reply logged. Stop at the end of any month.",
         "Both."),
        ("Cannot do",
         "Write a dossier for 100 builders a week, or log everything by itself.",
         "Talk to an owner, phone, visit, negotiate or close. Promise delivery or a reply. Reach Madhya Pradesh.",
         "Fix a weak offer."),
        ("Results so far",
         "None yet for Nexus360.",
         tokens["c1_cell"],
         "None yet."),
    ]
    body = "".join(f'<tr><td class="d">{a}</td><td data-label="One sales employee">{b}</td><td class="us" data-label="Our system">{c}</td><td data-label="Both">{d}</td></tr>' for a, b, c, d in rows)
    head = ('<thead><tr><th class="d"></th><th>One sales employee<small>Raipur, Bhilai or Rajnandgaon</small></th>'
            '<th class="us">Our system<small>Pilot, then monthly run</small></th><th>Both<small>System with you, or with an executive</small></th></tr></thead>')
    return f'<table class="cmp">{head}<tbody>{body}</tbody></table>'


# ---------------------------------------------------------------- assemble
def build_html():
    tpl = (ASSETS / "proposal_template.html").read_text(encoding="utf-8")
    tokens.update({
        "svg_process": svg_process(), "svg_funnel": svg_funnel(), "svg_timeline": svg_timeline(),
        "html_process": html_process(), "html_funnel": html_funnel(), "html_timeline": html_timeline(),
        "table_records": table_records(), "table_gates": table_gates(), "table_price": table_price(), "table_cmp": table_cmp(),
        "img_m1": png("fig_page_m1.png"), "img_m2": png("fig_page_m_screens.png"),
        "img_v1": jpg("f1_hook_t00.0.jpg"), "img_v2": jpg("f2_screenA_checks12_t04.2.jpg"),
        "img_v3": jpg("f4_screenB_t11.0.jpg"), "img_v4": jpg("f5_ask_t14.5.jpg"),
    })
    run = (f'<header class="run"><img src="{png("iv-infotech-logo.png")}" alt="IV Infotech">'
           f'<div class="meta"><b>Proposal for Nexus360</b> &middot; {tokens["date"]} &middot; prices proposed, valid until {tokens["valid_until"]}</div></header>')
    tpl = tpl.replace("<!--RUN-->", run)
    tpl = re.sub(r"<!--FOOT (\d+)-->", lambda m: f'<footer class="foot"><span><b>IV Infotech</b> &middot; Mehsana, Gujarat &middot; prepared for GreyBoard Consulting, confidential</span><span>Page {m.group(1)} of 10</span></footer>', tpl)

    def rep(m):
        k = m.group(1)
        if k not in tokens:
            raise KeyError("missing token: " + k)
        return tokens[k]
    # two passes so tokens inside inserted fragments (like alt_block) also resolve
    for _ in range(2):
        tpl = re.sub(r"\{\{(\w+)\}\}", rep, tpl)
    css = (ASSETS / "proposal.css").read_text(encoding="utf-8")
    fonts = (f'@font-face{{font-family:"Inter";src:url(data:font/woff2;base64,{b64(ASSETS / "inter.woff2")}) format("woff2");font-weight:100 900;font-style:normal}}'
             f'@font-face{{font-family:"Space Grotesk";src:url(data:font/woff2;base64,{b64(ASSETS / "space-grotesk.woff2")}) format("woff2");font-weight:300 700;font-style:normal}}')
    doc = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
           '<title>IV Infotech proposal for Nexus360</title>'
           f'<style>{fonts}\n{css}</style></head><body>\n{tpl}\n</body></html>')
    out = ROOT / "proposal.html"
    out.write_text(doc, encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB")
    return out


def render_pdf(html_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1000, "height": 1200})
        pg.goto("file:///" + str(html_path).replace("\\", "/"))
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(800)
        # overflow check: each .body must not scroll
        res = pg.evaluate("""() => [...document.querySelectorAll('.page')].map((p,i)=>{
            const b=p.querySelector('.body'); const kids=[...b.children];
            const cs=getComputedStyle(b); const limit=b.getBoundingClientRect().bottom-parseFloat(cs.paddingBottom);
            const src=kids.find(k=>k.classList.contains('src'));
            const content=kids.filter(k=>k!==src); const lastContent=content[content.length-1].getBoundingClientRect().bottom;
            const srcH=src?src.getBoundingClientRect().height+parseFloat(getComputedStyle(b).rowGap):0;
            const free=(limit-lastContent-srcH)/96*25.4;   // mm free between the last content block and the sources line
            const over=(b.scrollHeight-b.clientHeight);
            return {page:i+1, freeMm:Math.round(free*10)/10, over:over};})""")
        bad = False
        for r in res:
            flag = "  <-- OVERFLOW" if (r["freeMm"] < 0 or r["over"] > 1) else ""
            bad = bad or bool(flag)
            print(f"page {r['page']}: free space above the sources line {r['freeMm']} mm, scroll overflow {r['over']} px{flag}")
        # smallest printed type: figures (HTML figures + SVG diagrams) and body text, in pt. SVG text is scaled by the figure's CTM.
        fs = pg.evaluate("""() => {
            const pt = px => Math.round(px * 0.75 * 10) / 10;
            const rec = (root, tag, out) => root.querySelectorAll('*').forEach(el => {
                if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
                let px = parseFloat(getComputedStyle(el).fontSize);
                if (el instanceof SVGElement && el.getAttribute('font-size')) { const m = el.getScreenCTM(); px = parseFloat(el.getAttribute('font-size')) * (m ? m.a : 1); }
                out.push([pt(px), tag, el.textContent.trim().slice(0, 28)]);
            });
            const figs = [], bodies = [];
            document.querySelectorAll('.pipe-fig, .lead-fig, .fig-svg svg').forEach(f => rec(f, 'fig', figs));
            document.querySelectorAll('.page .body').forEach(b => b.querySelectorAll('p, li, td, th, .lead, figcaption').forEach(el => {
                if (el.closest('.pipe-fig, .lead-fig, .fig-svg, .src, figure.fig-svg')) return;
                if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
                bodies.push([pt(parseFloat(getComputedStyle(el).fontSize)), el.tagName, el.textContent.trim().slice(0, 28)]);
            }));
            figs.sort((a, b) => a[0] - b[0]); bodies.sort((a, b) => a[0] - b[0]);
            return {figs: figs.slice(0, 4), bodies: bodies.slice(0, 6)};
        }""")
        print("smallest figure text (pt):", fs["figs"])
        print("smallest body text (pt):", fs["bodies"])
        pg.pdf(path=str(ROOT / "proposal.pdf"), format="A4", print_background=True, prefer_css_page_size=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    print("wrote", ROOT / "proposal.pdf")
    return res


def render_pngs(scale=2.0):
    """Renders each PDF page to PNG with pdf.js (loaded from cdnjs in the browser; nothing is downloaded to disk)."""
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    handler = functools.partial(Quiet, directory=str(ROOT))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    viewer = ("<!doctype html><meta charset=utf-8><script src='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js'></script>"
              "<body><script>pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';"
              "window.renderPage=async function(url,n,scale){const d=await pdfjsLib.getDocument(url).promise;if(n===0)return d.numPages;"
              "const p=await d.getPage(n);const vp=p.getViewport({scale:scale});const c=document.createElement('canvas');c.width=vp.width;c.height=vp.height;"
              "await p.render({canvasContext:c.getContext('2d'),viewport:vp}).promise;return c.toDataURL('image/png');}</script></body>")
    vpath = ROOT / "_pdfview_tmp.html"
    vpath.write_text(viewer, encoding="utf-8")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto(f"http://127.0.0.1:{port}/_pdfview_tmp.html")
            pg.wait_for_function("window.pdfjsLib !== undefined", timeout=30000)
            url = f"http://127.0.0.1:{port}/proposal.pdf"
            n = pg.evaluate("([u])=>window.renderPage(u,0,1)", [url])
            print("pdf pages:", n)
            for i in range(1, n + 1):
                data = pg.evaluate("([u,i,s])=>window.renderPage(u,i,s)", [url, i, scale])
                (ROOT / f"page_{i}.png").write_bytes(base64.b64decode(data.split(",", 1)[1]))
            b.close()
    finally:
        srv.shutdown()
        vpath.unlink(missing_ok=True)
    return n


def render_html_views():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w, name, sc in ((1440, "html_view_desktop.png", 1), (390, "html_view_mobile.png", 2)):
            ctx = b.new_context(viewport={"width": w, "height": 900}, device_scale_factor=sc)
            pg = ctx.new_page()
            pg.goto("file:///" + str(ROOT / "proposal.html").replace("\\", "/"))
            pg.wait_for_timeout(700)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            print(f"html at {w}px: scrollWidth {sw}")
            pg.screenshot(path=str(ROOT / name), full_page=True)
            ctx.close()
        b.close()


if __name__ == "__main__":
    out = build_html()
    if "--html" in sys.argv:
        sys.exit(0)
    render_pdf(out)
    render_pngs()
    if "--noviews" not in sys.argv:
        render_html_views()
