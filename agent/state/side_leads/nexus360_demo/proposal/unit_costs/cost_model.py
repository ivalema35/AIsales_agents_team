# -*- coding: utf-8 -*-
"""Cost model behind unit_costs.md (Nexus360 / Chhattisgarh builders proposal, 20 Oct 2026).
Pure arithmetic, stdlib only: python cost_model.py
Every input is tagged FACT (sourced in unit_costs.md) or ASSUMPTION (owner can change it here).
Prices are in INR, before 18% GST on IV Infotech's own invoice."""

FX = {"low": 88.0, "base": 90.0, "high": 95.0}          # INR per USD. ASSUMPTION (last datapoint found: 88.70 on 30 Oct 2025)

# ---- WhatsApp (per DELIVERED marketing message, INR, before GST) ----
META_MARKETING = 0.8631        # FACT (secondary: Free Press Journal citing Meta's rate card, 30 Sep 2026; Monty Mobile; ChatMaxima)
META_UTILITY = 0.115           # FACT (same sources)
GST = 0.18                     # FACT per vendor sources (not on Meta's page)
BSP_RATE = {"low": META_MARKETING, "base": 0.9926, "high": 1.09}   # base = Gallabox list (0.8631 x 1.15), high = AiSensy blog; our BSP's own markup is UNKNOWN
MSG_ALL_IN = {k: v * (1 + GST) for k, v in BSP_RATE.items()}

# ---- AI / data per builder, USD ----
TOKENS = {"low": 200_000, "base": 300_000, "high": 500_000}         # observed 121k-342k per candidate/qualified lead (agent/memory.md), see md
BLEND = {"low": 0.50, "base": 1.50, "high": 3.50}                   # USD per MTok, Sonnet 5.5, depends on cache-read share. ASSUMPTION
OPUS_BLEND_HIGH = 7.00                                              # Opus 5.5 = 2x Sonnet 5.5 list prices
SEARCHES = {"low": 10, "base": 15, "high": 40}                      # API web searches per builder. ASSUMPTION; $10 per 1,000 = FACT
SEARCH_USD = 0.01
DATA_USD = {"low": 0.03, "base": 0.10, "high": 0.30}                # Apify / ad-library / registry lookups. ASSUMPTION (own notes: ~$0.05-0.08 per lead)
CONTINGENCY = 0.20                                                  # re-runs and failures, on research cash. ASSUMPTION


def research_usd(s, opus=False):
    llm = TOKENS[s] / 1e6 * (OPUS_BLEND_HIGH if opus else BLEND[s])
    return llm, SEARCHES[s] * SEARCH_USD, DATA_USD[s]


def research_inr(s, opus=False):
    llm, web, data = research_usd(s, opus)
    return (llm + web + data) * FX[s]


# ---- Human time (hours) and rate (INR/h). ASSUMPTION ----
RATE = {"low": 500, "base": 1000, "high": 1500}
MARGIN = 0.30

# per-builder human minutes: dossier QA (identity + owner source check) and message/video preview review
QA_MIN = {"low": 1.5, "base": 3.0, "high": 6.0}
REVIEW_MIN = {"low": 1.0, "base": 1.5, "high": 3.0}
DAILY_CHECK_MIN = {"low": 5, "base": 10, "high": 20}            # replies, alerts, send health
SYNC_H = {"low": 0.5, "base": 0.75, "high": 1.0}                # one sync call with the client incl. prep
UPKEEP_H = {"low": 0.5, "base": 1.0, "high": 3.0}               # pilot: template/Meta quality fixes
UPKEEP_H_MONTH = {"low": 1.0, "base": 3.0, "high": 6.0}
SETUP_H = {"low": 29, "base": 41, "high": 56}                   # one-time build for the client, see table in the md
FINAL_REPORT_H = {"low": 2.0, "base": 3.0, "high": 4.0}
LIST_SETUP_H = {"low": 4, "base": 6, "high": 8}
LIST_DELIVERY_H = {"low": 1, "base": 2, "high": 4}

PILOT = dict(builders=50, working_days=10, numbers=dict(low=1.0, base=1.3, high=1.6), touches=dict(low=2, base=2, high=3),
             delivered=dict(low=0.30, base=0.55, high=1.00),
             misc_cash=dict(low=90, base=180 + 1000 + 500, high=450 + 3000 + 1500),    # reports LLM + number/domain + hosting
             voice=dict(low=6 * 88, base=6 * 90, high=11 * 95))                         # ElevenLabs Starter $6 (FACT) / Creator $11
MONTH = dict(builders=150, working_days=22, numbers=PILOT["numbers"], touches=PILOT["touches"], delivered=PILOT["delivered"],
             misc_cash=dict(low=225, base=450 + 1000 + 500, high=900 + 3000 + 1500),
             voice=PILOT["voice"])


def wa_pass_through(p, s):
    msgs = p["builders"] * p["numbers"][s] * p["touches"][s]
    return msgs * p["delivered"][s] * MSG_ALL_IN[s], msgs


def r(x, step=500):
    return int(round(x / step) * step)


def hours_pilot(s):
    n = PILOT["builders"]
    per_builder = n * (QA_MIN[s] + REVIEW_MIN[s]) / 60
    daily = PILOT["working_days"] * DAILY_CHECK_MIN[s] / 60
    syncs = 2 * SYNC_H[s] + FINAL_REPORT_H[s]
    ops = per_builder + daily + syncs + UPKEEP_H[s]
    return SETUP_H[s], ops


def hours_month(s):
    n = MONTH["builders"]
    per_builder = n * (QA_MIN[s] + REVIEW_MIN[s]) / 60
    daily = MONTH["working_days"] * DAILY_CHECK_MIN[s] / 60
    syncs = 4 * SYNC_H[s]
    return per_builder + daily + syncs + UPKEEP_H_MONTH[s]


def hours_list(n, s):
    return LIST_SETUP_H[s] + n * QA_MIN[s] / 60 + LIST_DELIVERY_H[s]


def pilot_costs():
    out = {}
    for s in ("low", "base", "high"):
        research = research_inr(s) * PILOT["builders"] * (1 + CONTINGENCY)
        misc = PILOT["misc_cash"][s] + PILOT["voice"][s]
        setup, ops = hours_pilot(s)
        wa, msgs = wa_pass_through(PILOT, s)
        out[s] = dict(research=research, misc=misc, cash=research + misc, setup_h=setup, ops_h=ops, hours=setup + ops, wa=wa, msgs=msgs)
    return out


def monthly_costs():
    out = {}
    for s in ("low", "base", "high"):
        research = research_inr(s) * MONTH["builders"] * (1 + CONTINGENCY)
        misc = MONTH["misc_cash"][s] + MONTH["voice"][s]
        wa, msgs = wa_pass_through(MONTH, s)
        out[s] = dict(research=research, misc=misc, cash=research + misc, hours=hours_month(s), wa=wa, msgs=msgs)
    return out


def list_costs(n):
    out = {}
    for s in ("low", "base", "high"):
        research = research_inr(s) * n * (1 + CONTINGENCY)
        out[s] = dict(research=research, cash=research, hours=hours_list(n, s))
    return out


def price_ladder(cash, hours):
    """floor = base cash + base hours @ low rate, no margin; recommended = @ base rate + margin; high = @ high rate + margin."""
    return dict(floor=cash + hours * RATE["low"],
                recommended=(cash + hours * RATE["base"]) * (1 + MARGIN),
                high=(cash + hours * RATE["high"]) * (1 + MARGIN),
                cost_at_base_rate=cash + hours * RATE["base"])


def show():
    print("USD->INR", FX)
    print("WhatsApp all-in INR per delivered marketing msg (incl. GST):", {k: round(v, 3) for k, v in MSG_ALL_IN.items()})
    print()
    print("RESEARCH PER BUILDER (USD llm, web, data | INR total)")
    for s in ("low", "base", "high"):
        llm, web, data = research_usd(s)
        print(" ", s, round(llm, 2), round(web, 2), round(data, 2), "| INR", round(research_inr(s)), "| with contingency", round(research_inr(s) * (1 + CONTINGENCY)))
    llm, web, data = research_usd("high", opus=True)
    print("  high on Opus 5.5:", round(llm, 2), round(web, 2), round(data, 2), "| INR", round(research_inr("high", opus=True)))
    print()
    pc = pilot_costs()
    print("OPTION A (2-week pilot, 50 builders)")
    for s in ("low", "base", "high"):
        print(" ", s, {k: round(v, 1) for k, v in pc[s].items()})
    lad = price_ladder(pc["base"]["cash"], pc["base"]["hours"])
    print("  ladder:", {k: round(v) for k, v in lad.items()})
    mc = monthly_costs()
    print("OPTION B (monthly, 150 builders)")
    for s in ("low", "base", "high"):
        print(" ", s, {k: round(v, 1) for k, v in mc[s].items()})
    ladB = price_ladder(mc["base"]["cash"], mc["base"]["hours"])
    print("  ladder:", {k: round(v) for k, v in ladB.items()})
    for n in (50, 150):
        lc = list_costs(n)
        print("OPTION C (research only)", n)
        for s in ("low", "base", "high"):
            print(" ", s, {k: round(v, 1) for k, v in lc[s].items()})
        print("  ladder:", {k: round(v) for k, v in price_ladder(lc["base"]["cash"], lc["base"]["hours"]).items()})
    print()
    # marginal cost of one more builder
    print("MARGINAL COST PER BUILDER (base): cash", round(research_inr("base") * (1 + CONTINGENCY)), "+ human",
          round((QA_MIN['base'] + REVIEW_MIN['base']) / 60 * RATE['base']), "+ WhatsApp", round(MSG_ALL_IN['base'] * 1.3 * 2 * 0.55, 1))
    print()
    # ---- value-based check ----
    print("VALUE CHECK")
    arpa = {"low": 40_000, "base": 50_000, "high": 60_000}       # INR per customer per year. ASSUMPTION from public per-user / per-project prices
    years = 3                                                    # ASSUMPTION
    ltv = {k: v * years for k, v in arpa.items()}
    reply = {"low": 0.0, "base": 0.02, "high": 0.05}              # genuine owner reply per builder messaged. ASSUMPTION (own campaign: 0 of 9)
    demo = 0.40                                                  # reply -> demo held. ASSUMPTION
    paid = {"low": 0.10, "base": 0.15, "high": 0.20}             # demo -> paying customer. ASSUMPTION
    for label, n in (("pilot 50", 50), ("month 150", 150)):
        row = {}
        for s in ("low", "base", "high"):
            cust = n * reply[s] * demo * paid[s]
            row[s] = (round(n * reply[s], 2), round(n * reply[s] * demo, 2), round(cust, 3), round(cust * ltv["base"]))
        print(" ", label, "(replies, demos, customers, expected 3-yr revenue INR @1.5L LTV):", row)
    pilot_price, month_price = 75_000, 45_000
    be = lambda price, n: price / (ltv["base"] * n * demo * paid["base"])
    print(f"  break-even genuine-reply rate: pilot @{pilot_price}: {be(pilot_price, 50) * 100:.1f} pct ; month @{month_price}: {be(month_price, 150) * 100:.1f} pct")
    print("  customers needed to repay: pilot ->", round(pilot_price / ltv["base"], 2), "; month ->", round(month_price / ltv["base"], 2))
    reach = {"low": 0.40 * 0.30, "base": 0.55 * 0.45, "high": 0.70 * 0.60}   # named owner x owner number found. ASSUMPTION
    print("  owner-level reachable builders per 50:", {k: round(50 * v, 1) for k, v in reach.items()}, "per 150:", {k: round(150 * v) for k, v in reach.items()})
    print("  per reachable owner (base): pilot", round(pilot_price / (50 * reach['base'])), " month", round(month_price / (150 * reach['base'])))
    print("  per builder worked: pilot", round(pilot_price / 50), " month", round(month_price / 150))
    print("  pool runway months @150/month: 3 districts all-valid <=3 projects 424 ->", round(424 / 150, 1), "; all CG 798 ->", round(798 / 150, 1))


if __name__ == "__main__":
    show()
