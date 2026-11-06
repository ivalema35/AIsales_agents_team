# -*- coding: utf-8 -*-
"""Lean, deliverable INDICATIVE estimate model for the Nexus360 side lead (20 Oct 2026).

Run:  python estimate_model.py          -> prints the tables and writes estimate_model.json next to this file.
Stdlib only. Every input is tagged FACT (source in estimate_model.md) or ASSUMPTION (change it here and rerun).
All money is INR before GST unless a name says gst. Hours are IV Infotech staff hours.

This file is INTERNAL (it holds our cost lines, hour rates and margin). Nothing in it goes to Sridhar as is.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = ("low", "base", "high")
RATES = (500, 1000, 1500)            # Rs per staff hour. The owner's range is 500-1,000; 1,500 is a stress test
CHANGE_RATE = 1000                   # Rs per hour for change requests (owner instruction)

# ---------------------------------------------------------------- FX and Claude prices
FX = {"low": 92.0, "base": 96.5, "high": 100.0}      # ASSUMPTION. Last datapoint found: 96.5 on 22 Jul 2026 (pluang.com); 52-week range 86.25-96.96
HAIKU = {"inp": 0.10, "out": 0.50}                   # FACT platform.claude.com pricing, Haiku 5.5, prompts up to 100k tokens. USD per MTok
SONNET = {"inp": 2.00, "out": 10.00}                 # FACT Sonnet 5.5
OPUS = {"inp": 4.00, "out": 20.00}                   # FACT Opus 5.5
FABLE = {"inp": 10.00, "out": 50.00}                 # FACT Fable 5.1 (stress case only)
SEARCH_USD = 0.01                                    # FACT $10 per 1,000 searches
CONTINGENCY = 0.20                                   # re-runs, retries. ASSUMPTION (same as the 20 Oct unit-cost model)
AI_AS_IS_NOTE = {"low": 24, "base": 76, "high": 279}  # Rs per builder, owner's note (unit_costs.md, FX 88/90/95)
PLAN_API_CREDIT_USD = 100                            # FACT Anthropic: Max 5x includes USD 100 a month of API credit (announced 7 Oct 2026)

# Lean per-builder pipeline: tokens per step and scenario. DESIGN TARGET, not yet measured (the 6-builder calibration measures it)
LEAN = {
    #        small model (Haiku 5.5)      deep model (Sonnet 5.5)       web searches
    "low":  {"h_in": 46_000,  "h_out": 5_000,  "s_in": 30_000,  "s_out": 3_000,  "searches": 4},
    "base": {"h_in": 78_000,  "h_out": 7_000,  "s_in": 45_000,  "s_out": 4_000,  "searches": 6},
    "high": {"h_in": 112_000, "h_out": 11_000, "s_in": 120_000, "s_out": 10_000, "searches": 14},
}
TOKEN_CAP_PER_BUILDER = 300_000                      # hard cap enforced by the budget meter
RS_CAP_PER_BUILDER = 100                             # hard cap in Rs (about USD 1.04)


def lean_usd(sc, price_small=HAIKU, price_deep=SONNET, mult=1.0):
    c = LEAN[sc]
    small = (c["h_in"] * price_small["inp"] + c["h_out"] * price_small["out"]) / 1e6
    deep = (c["s_in"] * price_deep["inp"] + c["s_out"] * price_deep["out"]) / 1e6
    srch = c["searches"] * SEARCH_USD
    return (small + deep) * mult + srch, small, deep, srch


def lean_tokens(sc):
    c = LEAN[sc]
    return c["h_in"] + c["h_out"] + c["s_in"] + c["s_out"]


def lean_inr(sc, **kw):
    usd = lean_usd(sc, **kw)[0] * (1 + CONTINGENCY)
    return usd * FX[sc]


# ---------------------------------------------------------------- WhatsApp
BSP_RATE = 1.5            # Rs per MARKETING message, from the owner. Basis (delivered only?) to be confirmed with the BSP
GST = 0.18
TOUCHES = 2
NUMBERS_PER_MESSAGED = 1.0
P_OBS = 1 / 6             # FACT: 1 of 6 tested builders had a business-published number wired for WhatsApp (n = 6)
P_SCEN = {"observed 1 of 6 (17%)": 1 / 6, "assumption 35%": 0.35, "upper end of 95% interval (56%)": 0.56}
DELIVERY = (0.30, 0.45, 0.60)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


# ---------------------------------------------------------------- hours: LEAN (Standard) pilot, 50 builders
# (id, name, low, base, high, previous base hours in the 20 Oct low-price model, note)
SETUP = [
    ("S1", "Research pipeline: detail-page pull, group resolution, site contact extraction, small + deep model calls, budget meter, record format, 6-builder calibration", 6, 9, 14, 5,
     "More hours than before ON PURPOSE: scripts replace most agent work, so AI cost per builder falls and no subscription is needed. Reusable for the monthly run"),
    ("S2", "ONE master video (English) + script-filled builder page (beacons, mobile check)", 4, 6, 9, 15,
     "Cut: no per-builder video, no Hindi cut, designs/animatic/sample page already exist, Sridhar supplies recordings"),
    ("S3", "+91 number, display name, 2 templates (touch 1 with video header, touch 2 text), BSP rate/billing confirm, Meta approvals", 3, 4, 5, 4, "Same as before"),
    ("S4", "Forward-only reply routing to Sridhar + STOP rule + alert test", 4, 6, 8, 6, "Same as before; required by Sridhar's own rule that he takes every genuine reply"),
    ("S5", "Read-only view for Sridhar (viewer login, this campaign only, numbers masked, CSV export)", 3, 5, 8, 8, "Cut: reuse existing pages, no new charts"),
    ("S6", "Claims and copy QA, test sends to our own phones, go-live check", 2, 3, 4, 3, "Same as before"),
]


def run_hours(n_builders, rev_min, daily_min, days, kick, mid, final, upkeep):
    return {
        "R1": n_builders * rev_min / 60,
        "R2": days * daily_min / 60,
        "R3": kick,
        "R4": mid + final,
        "R5": upkeep,
    }


REV_MIN = {"low": 2.5, "base": 4.5, "high": 9.0}      # per builder: 3 QA + 1.5 review = 4.5 base (20 Oct model); 9 min = manual registry lookups (enrichment test 5-10 min)
DAILY_MIN = {"low": 3, "base": 5, "high": 10}
KICK = {"low": 0.75, "base": 1.0, "high": 1.5}
MID = {"low": 0.25, "base": 0.5, "high": 1.0}
FINAL = {"low": 1.5, "base": 2.5, "high": 3.5}        # final report + review call
UPKEEP = {"low": 0.5, "base": 1.0, "high": 3.0}
PILOT_DAYS = 14

CASH_PILOT_PARTS = {      # Rs, excluding AI (computed) and WhatsApp (passed through)
    "report_llm": {"low": 90, "base": 180, "high": 450},
    "voice_licence": {"low": 0, "base": 540, "high": 1100},      # ElevenLabs Starter USD 6 (FACT, our notes); 0 if Sridhar records the voice
    "number_domain_once": {"low": 0, "base": 1000, "high": 3000},  # ASSUMPTION; BSP fee for a 2nd number UNKNOWN
    "hosting_alloc": {"low": 0, "base": 500, "high": 1500},
}


def pilot_hours(sc, setup_override=None, run_override=None):
    setup = sum(row[2 + S.index(sc)] for row in SETUP) if setup_override is None else setup_override[sc]
    if run_override is None:
        r = run_hours(50, REV_MIN[sc], DAILY_MIN[sc], PILOT_DAYS, KICK[sc], MID[sc], FINAL[sc], UPKEEP[sc])
        run = sum(r.values())
    else:
        run = run_override[sc]
    return setup, run


def pilot_cash(sc, builders=50, voice=True, ai_as_is=False):
    ai = (AI_AS_IS_NOTE[sc] if ai_as_is else lean_inr(sc)) * builders
    parts = {k: v[sc] for k, v in CASH_PILOT_PARTS.items()}
    if not voice:
        parts["voice_licence"] = 0
    return ai + sum(parts.values()), ai, parts


# Starter variant (deeper cuts) so that Rs 35,000 can be defended. Each cut is a share of the Standard line it trims (same share at low/base/high)
STARTER_CUTS = [
    ("S1", "Pipeline: calibrate on 3 builders (not 6); group resolution by hand for flagged ones only", "setup", 0, 1.0 / 9),
    ("S2", "Page + video: reuse the sample page and animatic, captions only, no new recordings, one hook", "setup", 1, 1.0 / 6),
    ("S4", "Hand-off: alert + reply log only; STOP rule kept; no routing rules", "setup", 3, 2.0 / 6),
    ("S5", "Read-only view: daily static snapshot page (unlisted link, numbers masked) instead of a login", "setup", 4, 2.0 / 5),
    ("S6", "QA and test sends trimmed", "setup", 5, 0.5 / 3),
    ("R4", "Final report only (no mid-pilot note), one review call", "run", None, 1.0 / 3.0),
    ("R2/R3/R5", "Lighter check-ins and upkeep", "run", None, 0.75 / 3.17),
]


def starter_hours(sc):
    su = sum(row[2 + S.index(sc)] for row in SETUP)
    for cid, _t, kind, idx, frac in STARTER_CUTS:
        if kind == "setup":
            su -= SETUP[idx][2 + S.index(sc)] * frac
    r = run_hours(50, REV_MIN[sc], DAILY_MIN[sc], PILOT_DAYS, KICK[sc], MID[sc], FINAL[sc], UPKEEP[sc])
    ru = sum(r.values())
    ru -= (MID[sc] + FINAL[sc]) * (1.0 / 3.0)
    ru -= (r["R2"] + r["R3"] + r["R5"]) * (0.75 / 3.17)
    return su, ru


def cost(cash, hours, rate):
    return cash + hours * rate


def breakeven_rate(price, cash, hours):
    return (price - cash) / hours


# ---------------------------------------------------------------- monthly run
MONTH_FIXED_HOURS = {"low": 4.5, "base": 7.55, "high": 12.0}   # daily check 22 d x 5 min + weekly notes + review call + upkeep + pool refresh
MONTH_CASH_FIXED = {"low": 600, "base": 1840, "high": 4500}     # voice 540, hosting 500, number/BSP alloc 500, report LLM 300 (base)


def month_hours(n, sc):
    return MONTH_FIXED_HOURS[sc] + n * REV_MIN[sc] / 60


def month_cash(n, sc):
    return MONTH_CASH_FIXED[sc] + n * lean_inr(sc)


# ---------------------------------------------------------------- (d) driver table: requirement -> effect on price
# hours = (low, base, high) at the change rate of Rs 1,000 an hour. cash = Rs (low, base, high). All hours are ASSUMPTIONS unless noted.
DRIVERS = [
    dict(id="D1", req="More builders (each extra batch of 50, Chhattisgarh)", once_h=(0, 0, 0), month_h=(2.1, 3.75, 7.5), cash_once=(0, 0, 0), cash_month=(757, 1166, 2980),
         note="Review time 2.5/4.5/9 min per builder plus AI at the lean cost. The pool is the real limit: about 72 shortlisted now, about 424 on a loose rule, about 4 new qualifying builders a month. Above about 150 the small/medium rule must be loosened (Sridhar's decision)."),
    dict(id="D2", req="Per-builder video (name, project, city inside the video)", once_h=(3, 4, 5), month_h=(0.9, 1.5, 2.5), cash_once=(0, 0, 0), cash_month=(0, 100, 300),
         note="Per 50: about 1 hour of unattended render (1.45 min each is MEASURED for the 38 s video) plus a person looking at the first and last frame; 2 of 6 campaign-1 renders needed rework for a wrong name. Whether this BSP accepts a different video per recipient in a template header was not checked (UNKNOWN). No evidence that a name in the video lifts replies."),
    dict(id="D3", req="Hindi (or Gujarati) variant of page, video text and templates", once_h=(4, 5.5, 7), month_h=(0.25, 0.5, 1), cash_once=(0, 500, 2000), cash_month=(0, 0, 0),
         note="Per language. Needs a native-speaker check (none done so far). Voice clips are recorded by Sridhar. Gujarati is not relevant to Chhattisgarh."),
    dict(id="D4", req="Another state's RERA fetcher (only where the site allows bots; Madhya Pradesh excluded)", once_h=(8, 12, 20), month_h=(1, 1.5, 3), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="Per state. Includes a robots.txt and terms check. From our 20 Oct table: Odisha, Gujarat, Rajasthan were readable; Telangana has an image CAPTCHA (we do not bypass); UP gave errors. MP RERA robots.txt says Disallow all, so MP is NOT automated."),
    dict(id="D4b", req="Madhya Pradesh as a hand-built list (a person looks up each builder)", once_h=(0, 0, 0), month_h=(0, 0, 0), cash_once=(0, 0, 0), cash_month=(0, 0, 0), per_builder_min=(15, 27, 40),
         note="15 to 40 minutes per builder by hand = Rs 250 to 670 per builder at Rs 1,000 an hour (no human timing was taken; ASSUMPTION). Not automation. Asking MP RERA for permission is possible but not promised."),
    dict(id="D5", req="Nexus360 CRM integration (push qualified builders or replies into his CRM)", once_h=None, month_h=None, cash_once=None, cash_month=None,
         planning_bracket_h=(6, 20, 40),
         note="NOT QUOTABLE until we see his API. Free 1 to 2 hour API review first, then a range. Internal planning bracket only (not for Sridhar): file import 3 to 6 h, one-way push 8 to 20 h, two-way sync 30 h or more."),
    dict(id="D6", req="Email as a second channel (business-published role inboxes)", once_h=(5, 7, 9), month_h=(1, 1.5, 2.5), cash_once=(0, 0, 0), cash_month=(0, 0, 1800),
         note="Templates, page link, inbox-placement test, bounce handling, and a reply path that is actually monitored (campaign 1: 9 of 12 emails had an unmonitored Reply-To). Mail-sending plan cost is an ASSUMPTION. Raises the share of builders we can contact: 4 of 6 tested had some business-published channel, but that count includes landlines."),
    dict(id="D7", req="Calls by us (instead of Sridhar's team)", once_h=(0, 0, 0), month_h=(0, 0, 0), cash_once=(0, 0, 0), cash_month=(0, 0, 0), per_builder_min=(10, 20, 30),
         note="Up to 3 tries per builder = 10 to 30 minutes = Rs 170 to 500 per builder, so Rs 8,300 to 25,000 per 50 at Rs 1,000 an hour, plus telecom cost. Telecom (TRAI) rules for B2B calls not established. We recommend his team calls the warm ones. WhatsApp voice notes cannot open a conversation (templates carry text, image, video or document headers: INFERENCE from general WhatsApp knowledge, not re-checked today)."),
    dict(id="D8", req="Faster start (days instead of about 7 working days to first send)", once_h=(4, 8, 12), month_h=(0, 0, 0), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="About 25% of setup hours as overtime. It cannot beat outside waits: Meta template approval (16 to 20 min measured for one template), +91 number availability (UNKNOWN), and Sridhar's own inputs."),
    dict(id="D9", req="More reports (extra weekly report, extra review call)", once_h=(0, 0, 0), month_h=(2, 3, 4), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="Per month: 4 extra written reports at 0.5 to 1 h plus one extra call 0.75 h. Custom analysis on request: 2 to 4 h each."),
    dict(id="D10", req="Licensed registry data source (company and director records)", once_h=(4, 6, 8), month_h=(-1, -0.8, -0.4), cash_once=(0, 0, 0), cash_month=None,
         note="Licence fee is UNKNOWN: pass it through at cost, we do not guess it. Our tests used manual single lookups because the free sites bar scraping. It saves manual minutes only for the builders we upgrade from LIKELY to VERIFIED (about 10 per 50)."),
    dict(id="D11", req="Separate +91 number and display name", once_h=(0, 0, 0), month_h=(0, 0, 0), cash_once=(0, 0, 0), cash_month=(0, 750, 1500),
         note="Already INSIDE the lean price (3 to 5 h, row S3). Not yet known: whether our BSP can give a +91 number, its fee, Meta display-name approval, our business-verification status (a new portfolio is capped at 250 unique recipients per 24 h until verified). Cash shown is the possible BSP fee for the extra number (ASSUMPTION)."),
    dict(id="D12", req="Forward-only reply routing (every reply goes to Sridhar)", once_h=(3, 4.5, 6), month_h=(0.5, 1, 1.5), cash_once=(0, 0, 0), cash_month=(0, 0, 45),
         note="The basic version (one recipient, STOP rule, alert) is INSIDE the lean price (row S4). The row shows extras: second recipient, working-hour rules, fallback alert by another channel. Each alert sent from our number is a marketing-category message at Rs 1.5 (as seen on 19 Oct)."),
    dict(id="D13", req="Also message the mobile number filed on the RERA page (official contact, often an operator or adviser, not the owner)", once_h=(1, 2, 3), month_h=(0.8, 1.2, 2.0), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="Raises the share of builders we can message a lot (every tested builder had a filed mobile) but Sridhar himself says these are not the owners. Opt-in risk with Meta is higher (error 131049 hit 2 of 7 in campaign 1). Needs the owner's and Sridhar's decision. Not legal advice."),
    dict(id="D14", req="A third or fourth follow-up message", once_h=(0.5, 0.5, 1), month_h=(0.1, 0.2, 0.4), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="Plus Rs 1.5 per delivered message passed through. More touches raise Meta limit and block risk."),
    dict(id="D15", req="One more change round (page, video or message text)", once_h=(2, 3, 4), month_h=(0, 0, 0), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="One round is inside the lean price. Each extra round is quoted before work starts."),
    dict(id="D16", req="Custom dashboard views or more viewers", once_h=(3, 5, 8), month_h=(0.25, 0.5, 1), cash_once=(0, 0, 0), cash_month=(0, 0, 0),
         note="Two viewers and the standard views are inside the lean price."),
]

PROMISE = {
    "we_promise_if_inputs_arrive": [
        "Research records for up to 50 Chhattisgarh builders from the public RERA register, each fact with a source link and date, and a label VERIFIED / LIKELY / UNKNOWN for the owner or decision-maker. Where we cannot find one the record says UNKNOWN.",
        "A first WhatsApp message and at most one follow-up, in English, only to numbers the business itself published (own website, own ad or the register), only after a person on our side has checked the record, from our +91 line, with a STOP line.",
        "One master video and one personalised page per messaged builder, built from the register fields.",
        "Every genuine reply forwarded to the person Sridhar names, without any AI answer to the owner. We stop messaging a builder at once after any reply or STOP.",
        "A read-only view of the pilot data (funnel counts, builder table with labels, send and reply log) and a CSV export.",
        "One mid-pilot note and one final report (Day 17) with the funnel and what we learned, and an updated estimate for what comes next.",
    ],
    "we_never_promise": [
        "Replies, demos, meetings, customers or any reply rate. Our own first campaign: 9 contacted, no confirmed genuine reply; 2 of 7 cold WhatsApp messages arrived on time.",
        "A direct WhatsApp number or verified personal contact for every owner. Tested on 6 builders: owner or decision-maker named for 4 (labels LIKELY or VERIFIED, n = 6), a number wired for WhatsApp for 1, a verified direct owner number for 0.",
        "That every builder can be messaged. Builders without a business-published WhatsApp-capable number are researched and handed over as records, not messaged.",
        "Delivery of every message. Meta decides; some messages will not arrive.",
        "Madhya Pradesh automation (its RERA site disallows bots), other states, email, calls, Hindi or Gujarati, CRM integration. Each is a priced option, not included.",
        "A reply-rate verdict from 50 builders. At most about 8 to 28 of them can be messaged and a few of those delivered; a verdict needs roughly 90 to 600 researched builders depending on reach.",
        "Anything about Nexus360's own sales results or savings.",
    ],
}

CLAUSES = {
    "indicative": "This is an indicative estimate. It can change once we have your written requirements. We confirm a fixed price in writing before any work starts, and nothing is charged before you approve it.",
    "whatsapp_passthrough": "WhatsApp: Rs 1.5 per delivered marketing message, billed at our provider's rate with no markup, plus GST. Estimated Rs 10 to 100 for the pilot; the most it can reach inside the caps is Rs 195; we do not bill more than Rs 300 without your approval. Any other third-party fee we cannot know today (for example a fee for an extra number or a licensed data source) is passed through at cost only with your prior approval.",
    "price_change": "This price assumes AI, messaging and platform prices as of 20 October 2026. If any of them rises so that our direct cost per builder or per message rises by more than 25%, we pass the actual increase through at cost after 30 days' written notice, and you may stop at that point without penalty. No other price change happens without your written approval.",
    "change_requests": "Anything outside the caps is quoted in hours before work starts (change rate Rs 1,000 per hour).",
    "inputs": "The clock starts when we have the items on your list of inputs. If they arrive late, the dates move by the same number of days.",
}

CAPS = [
    "Builders: up to 50, Chhattisgarh only, chosen by the rules agreed at the kickoff call from the public RERA register.",
    "Research depth: one record per builder with sources, up to 10 manual company-record lookups, and a time-box per builder (a builder we cannot resolve inside it is marked UNKNOWN).",
    "Messages: WhatsApp only, English only, at most 2 per builder and at most 100 in total, only to numbers the business itself published, only after our check; STOP honoured at once.",
    "Video and page: one master video (up to 45 seconds) and one page per messaged builder, built from register fields; no per-builder video.",
    "Hand-off: every genuine reply forwarded to one person and number you name; up to 30 alerts.",
    "Dashboard: read-only, up to 2 viewers, pilot period plus 14 days; CSV export at the end.",
    "Reports: one mid-pilot note and one final report at Day 17.",
    "Change rounds: one round of changes to page, video or message text; further rounds quoted.",
    "Not included: calls, email, CRM integration, Hindi or Gujarati, other states, any reply handling by us.",
]


def build():
    out = {}
    out["meta"] = {
        "date": "2026-10-20", "status": "INTERNAL working model; not for Sridhar", "currency": "INR before GST", "rates_rs_per_hour": list(RATES),
        "fx_inr_per_usd": FX, "contingency_on_ai": CONTINGENCY,
    }

    # ---------- (a) unit costs
    lo, hi = wilson(1, 6)
    lo4, hi4 = wilson(4, 6)
    a = {"p_whatsapp_reach_observed": {"k": 1, "n": 6, "share": P_OBS, "wilson95": [lo, hi]},
         "p_owner_named_observed": {"k": 4, "n": 6, "share": 4 / 6, "wilson95": [lo4, hi4]}}
    ai = {}
    for sc in S:
        usd, small, deep, srch = lean_usd(sc)
        ai[sc] = {"tokens": lean_tokens(sc), "usd_before_contingency": usd, "usd_small": small, "usd_deep": deep, "usd_search": srch,
                  "inr_with_contingency": lean_inr(sc), "as_is_note_inr": AI_AS_IS_NOTE[sc]}
    a["ai_per_builder"] = ai
    a["wa_msg_cost"] = {"bsp_rs_per_marketing_msg": BSP_RATE, "with_gst": BSP_RATE * (1 + GST), "per_builder_2_touches_delivered": BSP_RATE * TOUCHES}
    # variable cost per researched builder
    var = {}
    for rate in RATES:
        var[rate] = {}
        for sc in S:
            human = REV_MIN[sc] / 60 * rate
            ai_inr = lean_inr(sc)
            var[rate][sc] = {"ai": ai_inr, "human": human, "total": ai_inr + human + 2.0}   # +2 = page/hosting/render share (ASSUMPTION, Rs 2 per the owner's note)
    a["variable_per_researched_builder"] = var
    # fixed allocations
    a["fixed_alloc_per_builder"] = {"pilot_50": (540 + 500) / 50, "month_150": (540 + 500 + 500 + 300) / 150}

    # cost per messaged / delivered builder, variable only and fully loaded (pilot)
    cash_b, ai_b, parts_b = pilot_cash("base")
    su, ru = pilot_hours("base")
    fully = {}
    for rate in RATES:
        total = cost(cash_b, su + ru, rate)
        fully[rate] = {"pilot_total_cost": total, "per_researched": total / 50}
    a["pilot_fully_loaded_base"] = fully
    matrix = {}
    for pname, p in P_SCEN.items():
        matrix[pname] = {}
        for d in DELIVERY:
            reach = 50 * p
            delivered = reach * d
            row = {"reachable_builders": reach, "delivered_builders": delivered}
            for rate in (500, 1000):
                v = var[rate]["base"]["total"]
                row[f"variable_per_messaged_rate{rate}"] = v / p + BSP_RATE * TOUCHES * d * 1.0 / 1
                row[f"variable_per_delivered_rate{rate}"] = (v * 50 + BSP_RATE * TOUCHES * delivered) / delivered
                row[f"full_pilot_per_delivered_rate{rate}"] = fully[rate]["pilot_total_cost"] / delivered
                row[f"full_pilot_per_reachable_rate{rate}"] = fully[rate]["pilot_total_cost"] / reach
            matrix[pname][f"{int(d*100)}%"] = row
    a["cost_matrix_base"] = matrix
    # builders needed for 30 delivered first touches
    need = {}
    for pname, p in P_SCEN.items():
        need[pname] = {f"{int(d*100)}%": 30 / (p * d) for d in DELIVERY}
    a["builders_needed_for_30_delivered"] = need
    # monthly run per delivered (fully loaded)
    mm = {}
    for n in (50, 100, 150):
        cash = month_cash(n, "base")
        hrs = month_hours(n, "base")
        c1000 = cost(cash, hrs, 1000)
        mm[n] = {"cost_rate1000": c1000, "per_delivered": {pname: {f"{int(d*100)}%": c1000 / (n * p * d) for d in DELIVERY} for pname, p in P_SCEN.items()}}
    a["monthly_full_cost_per_delivered_rate1000"] = mm
    out["a_unit_costs"] = a

    # ---------- (b) capacity
    b = {}
    b["credit_inr"] = PLAN_API_CREDIT_USD * FX["base"]
    cap = {}
    for sc in S:
        cap[f"lean_{sc}"] = PLAN_API_CREDIT_USD * FX["base"] / lean_inr(sc)
    cap["as_is_note_base"] = PLAN_API_CREDIT_USD * FX["base"] / AI_AS_IS_NOTE["base"]
    cap["as_is_note_high"] = PLAN_API_CREDIT_USD * FX["base"] / AI_AS_IS_NOTE["high"]
    b["builders_per_month_covered_by_100usd_credit"] = cap
    # price shock on AI
    shock = {}
    for label, mult in (("today", 1), ("x2", 2), ("x5", 5)):
        shock[label] = {sc: lean_inr(sc) * mult for sc in S}
    deep_opus = {sc: lean_usd(sc, price_deep=OPUS)[0] * (1 + CONTINGENCY) * FX[sc] for sc in S}
    deep_fable = {sc: lean_usd(sc, price_deep=FABLE)[0] * (1 + CONTINGENCY) * FX[sc] for sc in S}
    all_sonnet = {sc: lean_usd(sc, price_small=SONNET)[0] * (1 + CONTINGENCY) * FX[sc] for sc in S}
    shock["deep_call_on_opus_5_5"] = deep_opus
    shock["deep_call_on_fable_5_1"] = deep_fable
    shock["small_model_unavailable_all_on_sonnet"] = all_sonnet
    b["ai_cost_per_builder_inr_shocks"] = shock
    # human ceiling
    hum = {}
    for hrs_avail in (12, 20, 30):
        hum[f"{hrs_avail}h_a_month"] = {sc: max(0, (hrs_avail - MONTH_FIXED_HOURS[sc]) / (REV_MIN[sc] / 60)) for sc in S}
    b["builders_per_month_by_human_review_ceiling"] = hum
    b["pool"] = {"shortlist_now": 72, "loose_3_districts_no_date_limit": 424, "all_cg_no_date_limit": 798, "new_qualifying_per_month": "about 4 (8.4 new valid approvals a month)",
                 "source": "cg_rera_demo_summary.txt, unit_costs.md section 6B, comparison.md section 6"}
    out["b_capacity"] = b

    # ---------- (c) pilot
    c = {}
    hours = {}
    for sc in S:
        su, ru = pilot_hours(sc)
        hours[sc] = {"setup": su, "run": ru, "total": su + ru}
    c["hours_standard"] = hours
    c["hours_previous_low_price_model"] = {"low": 35.4, "base": 51.9, "high": 75.8}
    cashes = {}
    for sc in S:
        tot, ai_c, parts = pilot_cash(sc)
        cashes[sc] = {"total": tot, "ai": ai_c, **parts}
    c["cash_standard"] = cashes
    c["cash_if_ai_as_is_note"] = {sc: pilot_cash(sc, ai_as_is=True)[0] for sc in S}
    # starter
    st_hours = {}
    for sc in S:
        a_, b_ = starter_hours(sc)
        st_hours[sc] = {"setup": a_, "run": b_, "total": a_ + b_}
    c["hours_starter"] = st_hours
    st_cash = {sc: pilot_cash(sc, voice=False)[0] for sc in S}
    c["cash_starter"] = st_cash

    def price_grid(prices, hours_d, cash_d):
        g = {}
        for price in prices:
            g[price] = {}
            for rate in RATES:
                g[price][rate] = {}
                for sc in S:
                    cst = cost(cash_d[sc], hours_d[sc]["total"], rate)
                    g[price][rate][sc] = {"cost": cst, "margin": price - cst, "margin_pct": (price - cst) / price * 100}
        return g

    cash_std_tot = {sc: cashes[sc]["total"] for sc in S}
    c["price_grid_standard"] = price_grid((35000, 40000, 45000, 48000, 50000), hours, cash_std_tot)
    c["price_grid_starter"] = price_grid((30000, 35000, 38000, 40000), st_hours, st_cash)
    c["breakeven_rate_standard"] = {price: {sc: breakeven_rate(price, cash_std_tot[sc], hours[sc]["total"]) for sc in S} for price in (35000, 40000, 45000, 48000, 50000)}
    c["breakeven_rate_starter"] = {price: {sc: breakeven_rate(price, st_cash[sc], st_hours[sc]["total"]) for sc in S} for price in (30000, 35000, 38000, 40000)}
    # what if the AI cost were the owner's as-is notes (Rs 24 / 76 / 279 per builder) instead of the lean pipeline
    c["extra_cash_if_ai_as_is_vs_lean"] = {sc: pilot_cash(sc, ai_as_is=True)[0] - pilot_cash(sc)[0] for sc in S}
    # line items for the md
    c["setup_items"] = [{"id": r[0], "name": r[1], "low": r[2], "base": r[3], "high": r[4], "previous_base": r[5], "note": r[6]} for r in SETUP]
    ri = {sc: run_hours(50, REV_MIN[sc], DAILY_MIN[sc], PILOT_DAYS, KICK[sc], MID[sc], FINAL[sc], UPKEEP[sc]) for sc in S}
    c["run_items"] = {k: {sc: ri[sc][k] for sc in S} for k in ("R1", "R2", "R3", "R4", "R5")}
    c["starter_cuts"] = [{"id": x[0], "what": x[1]} for x in STARTER_CUTS]
    # delivery test (price 45,000, base hours/cash, rate 1,000), reach 17/35/56 and delivery 30/60, BSP billing delivered-only vs on-send
    dtest = {}
    price = 48000
    base_cost = cost(cash_std_tot["base"], hours["base"]["total"], 1000)
    for pname, p in P_SCEN.items():
        dtest[pname] = {}
        sent = 50 * p * NUMBERS_PER_MESSAGED * TOUCHES
        for d in (0.30, 0.60):
            delivered = sent * d
            bill_delivered = delivered * BSP_RATE
            bill_sent = sent * BSP_RATE
            passthrough = delivered * BSP_RATE
            dtest[pname][f"{int(d*100)}%"] = {
                "messages_sent": sent, "messages_delivered": delivered, "passthrough_billed_to_sridhar": passthrough,
                "our_margin_if_bsp_bills_delivered_only": price - base_cost + passthrough - bill_delivered,
                "our_margin_if_bsp_bills_every_message_sent": price - base_cost + passthrough - bill_sent,
            }
    c["delivery_test_price48000_base_rate1000"] = dtest
    # whatsapp pass-through caps
    max_msgs = 50 * TOUCHES
    alerts = 30
    c["whatsapp_passthrough"] = {"max_messages": max_msgs, "max_cost_all_delivered": max_msgs * BSP_RATE, "alerts_cap": alerts, "alerts_cost": alerts * BSP_RATE,
                                 "max_total_before_gst": (max_msgs + alerts) * BSP_RATE, "max_total_with_gst": (max_msgs + alerts) * BSP_RATE * (1 + GST),
                                 "expected_range_before_gst": [8.5 * 2 * 0.30 * BSP_RATE, 28 * 2 * 0.60 * BSP_RATE]}
    out["c_pilot"] = c

    # ---------- monthly tests
    m = {}
    grid = {}
    for n in (50, 100, 150):
        grid[n] = {}
        for sc in S:
            hrs = month_hours(n, sc)
            cash = month_cash(n, sc)
            grid[n][sc] = {"hours": hrs, "cash": cash, **{f"cost_rate{r}": cost(cash, hrs, r) for r in RATES}}
    m["cost_grid"] = grid
    m["breakeven_rate"] = {f"price{p}_n{n}": {sc: breakeven_rate(p, grid[n][sc]["cash"], grid[n][sc]["hours"]) for sc in S}
                           for p in (25000, 30000, 36000) for n in (50, 100, 150)}
    # per extra 50 builders
    ex = {}
    for sc in S:
        ex[sc] = {"hours": 50 * REV_MIN[sc] / 60, "ai": 50 * lean_inr(sc)}
        ex[sc]["cost_rate1000"] = ex[sc]["hours"] * 1000 + ex[sc]["ai"]
    m["extra_50_builders"] = ex
    # capped worst case: review time-boxed to 6 min, AI hard cap
    capped = {}
    for n in (100, 150):
        hrs = MONTH_FIXED_HOURS["base"] + n * 6 / 60
        cash = MONTH_CASH_FIXED["base"] + n * RS_CAP_PER_BUILDER * 0.5      # AI budget meter: monthly AI budget = half of the per-builder hard cap x N (ASSUMPTION)
        capped[n] = {"hours": hrs, "cash": cash, "cost_rate1000": cost(cash, hrs, 1000)}
    m["capped_worst_case_6min_box"] = capped
    out["c_monthly"] = m

    # ---------- research-only cross-check
    ro = {}
    for label, setup_h in (("first_list_incl_pipeline_build", 9.0), ("repeat_list_pipeline_exists", 0.0)):
        hrs = setup_h + 50 * 4.5 / 60 + 2.0
        cash = 50 * lean_inr("base") + 180
        ro[label] = {"hours": hrs, "cash": cash, "cost_rate500": cost(cash, hrs, 500), "cost_rate1000": cost(cash, hrs, 1000), "breakeven_rate_at_12000": breakeven_rate(12000, cash, hrs)}
    out["research_only_check_50_builders_price12000"] = ro

    # ---------- (f) sensitivity
    f = {}
    # builders per month before loss at the pilot price per builder
    for price in (35000, 48000):
        per_b = price / 50
        row = {}
        for sc in S:
            var_rate = {}
            for rate in (500, 1000):
                var_cost = lean_inr(sc) + REV_MIN[sc] / 60 * rate + 2.0
                fixed = MONTH_FIXED_HOURS[sc] * rate + MONTH_CASH_FIXED[sc]
                be = fixed / (per_b - var_cost) if per_b > var_cost else float("inf")
                max_min = (per_b - lean_inr(sc) - 2.0) / rate * 60
                var_rate[rate] = {"price_per_builder": per_b, "var_cost_per_builder": var_cost, "fixed_month": fixed, "min_builders_to_break_even": be, "max_human_minutes_per_builder_before_loss_ignoring_fixed": max_min}
            row[sc] = var_rate
        f[f"pilot_price_{price}"] = row
    # at a monthly fee of 30,000: how many builders until we lose money
    fee = {}
    for sc in S:
        fee[sc] = {}
        for rate in (500, 1000, 1500):
            fixed = MONTH_FIXED_HOURS[sc] * rate + MONTH_CASH_FIXED[sc]
            var_cost = lean_inr(sc) + REV_MIN[sc] / 60 * rate
            fee[sc][rate] = {"max_builders_before_loss_at_fee30000": (30000 - fixed) / var_cost if var_cost > 0 else None}
    f["monthly_fee_30000_max_builders"] = fee
    out["f_sensitivity"] = f

    # ---------- (d) drivers, (e) promise boundary, clauses, recommended prices
    drv = []
    for d in DRIVERS:
        row = dict(d)
        row["once_rs_at_change_rate"] = None
        if d.get("once_h") is not None and d.get("cash_once") is not None:
            row["once_rs_at_change_rate"] = [h * CHANGE_RATE + c for h, c in zip(d["once_h"], d["cash_once"])]
        row["month_rs_at_change_rate"] = None
        if d.get("month_h") is not None and d.get("cash_month") is not None:
            row["month_rs_at_change_rate"] = [h * CHANGE_RATE + c for h, c in zip(d["month_h"], d["cash_month"])]
        if d.get("per_builder_min"):
            row["rs_per_builder_at_change_rate"] = [m / 60 * CHANGE_RATE for m in d["per_builder_min"]]
        drv.append(row)
    out["d_drivers"] = drv
    out["e_promise_boundary"] = PROMISE
    out["pilot_caps"] = CAPS
    out["clauses"] = CLAUSES
    ss_h = MONTH_FIXED_HOURS["base"] + 40 * REV_MIN["base"] / 60
    ss_c = MONTH_CASH_FIXED["base"] + 40 * lean_inr("base")
    out["steady_state_check_40_builders"] = {"hours": ss_h, "cash": ss_c, "cost_rate1000": cost(ss_c, ss_h, 1000)}
    out["recommended"] = {
        "pilot_standard_from_rs": 48000, "pilot_starter_from_rs": 35000,
        "monthly_up_to_100_builders_from_rs": 30000, "monthly_up_to_150_builders_from_rs": 36000, "monthly_each_extra_50_builders_rs": 6000,
        "monthly_steady_state_from_month_4_up_to_40_builders_rs": 15000,
        "all_prices_before_gst": True, "whatsapp_passthrough_rs_per_delivered_marketing_msg_before_gst": 1.5, "pilot_whatsapp_cap_rs_before_gst": 300,
        "change_rate_rs_per_hour": CHANGE_RATE,
        "basis": ("Standard 48,000 covers base hours at Rs 1,000 an hour (cost about 46,300). Starter 35,000 covers base hours down to about Rs 930 an hour. "
                  "Monthly 30,000 for 100 builders covers even the 6-minute time-boxed worst case at Rs 1,000 an hour (about 24,400)."),
    }
    std_cost_1000 = cost(cash_std_tot["base"], hours["base"]["total"], 1000)
    out["key_numbers"] = {
        "ai_rs_per_builder_lean_low_base_high": [round(lean_inr(sc), 1) for sc in S],
        "ai_rs_per_builder_as_is_notes": [AI_AS_IS_NOTE[sc] for sc in S],
        "tokens_per_builder_lean_low_base_high": [lean_tokens(sc) for sc in S],
        "variable_rs_per_researched_builder_at_rate1000_low_base_high": [round(a["variable_per_researched_builder"][1000][sc]["total"]) for sc in S],
        "variable_rs_per_researched_builder_at_rate500_low_base_high": [round(a["variable_per_researched_builder"][500][sc]["total"]) for sc in S],
        "pilot_standard_hours_low_base_high": [round(hours[sc]["total"], 1) for sc in S],
        "pilot_standard_cash_low_base_high": [round(cash_std_tot[sc]) for sc in S],
        "pilot_standard_cost_base_hours_at_500_1000_1500": [round(cost(cash_std_tot["base"], hours["base"]["total"], r)) for r in RATES],
        "pilot_starter_hours_low_base_high": [round(st_hours[sc]["total"], 1) for sc in S],
        "pilot_starter_cost_base_hours_at_500_1000_1500": [round(cost(st_cash["base"], st_hours["base"]["total"], r)) for r in RATES],
        "breakeven_rate_standard_48000_low_base_high": [round(breakeven_rate(48000, cash_std_tot[sc], hours[sc]["total"])) for sc in S],
        "breakeven_rate_standard_35000_low_base_high": [round(breakeven_rate(35000, cash_std_tot[sc], hours[sc]["total"])) for sc in S],
        "breakeven_rate_starter_35000_low_base_high": [round(breakeven_rate(35000, st_cash[sc], st_hours[sc]["total"])) for sc in S],
        "credit_inr_per_month": round(PLAN_API_CREDIT_USD * FX["base"]),
        "builders_covered_by_credit_lean_base_high": [round(PLAN_API_CREDIT_USD * FX["base"] / lean_inr(sc)) for sc in ("base", "high")],
    }
    return out


def fmt(x):
    return f"{x:,.0f}"


def show(o):
    a, b, c, m = o["a_unit_costs"], o["b_capacity"], o["c_pilot"], o["c_monthly"]
    print("== AI per builder (lean) ==")
    for sc in S:
        x = a["ai_per_builder"][sc]
        print(sc, "tokens", x["tokens"], "USD", round(x["usd_before_contingency"], 3), "(small", round(x["usd_small"], 4), "deep", round(x["usd_deep"], 3), "search", round(x["usd_search"], 3), ") Rs w/ contingency", round(x["inr_with_contingency"], 1), "as-is note", x["as_is_note_inr"])
    print("\n== variable cost per researched builder (AI + human + Rs 2) ==")
    for rate in RATES:
        print(rate, {sc: round(a["variable_per_researched_builder"][rate][sc]["total"]) for sc in S})
    print("\n== pilot hours ==")
    for sc in S:
        print(sc, {k: round(v, 2) for k, v in c["hours_standard"][sc].items()}, "cash", round(c["cash_standard"][sc]["total"]), "starter", {k: round(v, 2) for k, v in c["hours_starter"][sc].items()}, "cash", round(c["cash_starter"][sc]))
    print("\n== standard price grid (margin Rs) ==")
    for price, g in c["price_grid_standard"].items():
        print(price, {r: {sc: round(g[r][sc]["margin"]) for sc in S} for r in RATES})
    print("breakeven rate standard", {p: {sc: round(v) for sc, v in d.items()} for p, d in c["breakeven_rate_standard"].items()})
    print("\n== starter ==")
    for price, g in c["price_grid_starter"].items():
        print(price, {r: {sc: round(g[r][sc]["margin"]) for sc in S} for r in RATES})
    print("breakeven rate starter", {p: {sc: round(v) for sc, v in d.items()} for p, d in c["breakeven_rate_starter"].items()})
    print("\n== delivery test ==")
    for pn, d in c["delivery_test_price48000_base_rate1000"].items():
        print(pn, {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in d.items()})
    print("\nWA", c["whatsapp_passthrough"])
    print("\n== monthly ==")
    for n, d in m["cost_grid"].items():
        print(n, {sc: {k: round(v, 1) for k, v in d[sc].items()} for sc in S})
    print("breakeven", {k: {sc: round(v) for sc, v in d.items()} for k, d in m["breakeven_rate"].items()})
    print("extra 50", {sc: {k: round(v) for k, v in d.items()} for sc, d in m["extra_50_builders"].items()})
    print("capped", m["capped_worst_case_6min_box"])
    print("\n== capacity ==")
    print(b["builders_per_month_covered_by_100usd_credit"], round(b["credit_inr"]))
    print("shocks", {k: {sc: round(v, 1) for sc, v in d.items()} for k, d in b["ai_cost_per_builder_inr_shocks"].items()})
    print("human ceiling", {k: {sc: round(v) for sc, v in d.items()} for k, d in b["builders_per_month_by_human_review_ceiling"].items()})
    print("\n== cost matrix base (p x d) ==")
    for pn, dd in a["cost_matrix_base"].items():
        for dn, row in dd.items():
            print(pn, dn, {k: round(v) for k, v in row.items()})
    print("builders needed for 30 delivered", {k: {kk: round(vv) for kk, vv in v.items()} for k, v in a["builders_needed_for_30_delivered"].items()})
    print("fully loaded pilot (base hours/cash)", a["pilot_fully_loaded_base"])
    print("monthly per delivered rate1000", {n: {pn: {k: round(v) for k, v in d.items()} for pn, d in x["per_delivered"].items()} for n, x in a["monthly_full_cost_per_delivered_rate1000"].items()})
    print("\nwilson", a["p_whatsapp_reach_observed"], a["p_owner_named_observed"])
    print("\nresearch-only", o["research_only_check_50_builders_price12000"])
    print("\nsensitivity", json.dumps(o["f_sensitivity"], indent=1, default=lambda x: round(x, 1))[:3500])


if __name__ == "__main__":
    out = build()
    show(out)
    (HERE / "estimate_model.json").write_text(json.dumps(out, indent=2, default=lambda x: round(x, 4) if isinstance(x, float) else x), encoding="utf-8")
    print("\nwrote", HERE / "estimate_model.json")
