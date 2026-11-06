# -*- coding: utf-8 -*-
"""Arithmetic behind comparison.md (employee vs system vs hybrid) for the Nexus360 side lead.
Every number is either sourced in comparison.md or labelled ASSUMPTION here. Run: python calc_comparison.py
Prints tables and writes comparison_numbers.json next to this file. No network, no secrets."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = {}

# ------------------------------------------------------------------ 1. EMPLOYEE COST
# PF base: ASSUMPTION basic = 50% of fixed pay (Labour Code 50% wage rule), PF wage ceiling Rs 25,000 since 17 Sep 2026
# (S.O. 5109(E)). Employer outgo ~ 12% + 0.5% EDLI + 0.5% admin = 13% of PF wages. ESI employer 3.25% only if gross <= Rs 21,000.
PF_CEILING = 25000


def employee(label, fixed, incentive, phone, crm, equip, recruit_months, ramp_loss_months, tenure_months=24):
    pf_wage = min(fixed * 0.5, PF_CEILING)
    pf = 0.13 * pf_wage
    esi = 0.0325 * fixed if fixed <= 21000 else 0.0
    cash = fixed + pf + esi + incentive + phone + crm + equip
    recruit = fixed * recruit_months / tenure_months      # one-time agency/portal cost spread over expected tenure
    ramp = fixed * ramp_loss_months / tenure_months       # pay for output not yet delivered, spread over tenure
    allin = cash + recruit + ramp
    return dict(label=label, fixed=round(fixed), pf_edli_admin=round(pf), esi=round(esi), incentive=incentive, phone=phone, crm=crm,
                equipment=equip, cash_monthly=round(cash), recruit_amortised=round(recruit), ramp_amortised=round(ramp), allin_monthly=round(allin),
                annual_ctc_fixed=round(fixed * 12))


emp = [
    employee("CG junior caller / appointment setter", 15000, 2000, 600, 0, 0, 0.5, 1.0),
    employee("CG mid BDE (central case)", 25000, 5000, 800, 800, 1100, 1.0, 1.5),
    employee("CG experienced BDE (ERP/real-estate, can talk to owners)", 40000, 8000, 1000, 1400, 1250, 1.5, 1.5),
    employee("Metro mid-level BDE (Bengaluru modelled median Rs 4.9 L)", 40833, 8000, 1000, 1400, 1250, 1.5, 1.5),
]
# sensitivity corners for the CG band
emp_low = employee("CG low corner (Rs 15k fixed, minimal extras)", 15000, 2000, 600, 0, 0, 0.5, 1.0)
emp_high = employee("CG high corner (Rs 45k fixed)", 45000, 10000, 1000, 1400, 1250, 1.5, 1.5)
OUT["employee_cases"] = emp
OUT["employee_low_high"] = [emp_low, emp_high]
C_E = emp[1]["allin_monthly"]          # central employee all-in monthly cost
C_E_LOW, C_E_HIGH = emp_low["allin_monthly"], emp_high["allin_monthly"]
print("EMPLOYEE all-in monthly (Rs):")
for e in emp + [emp_low, emp_high]:
    print("  %-62s fixed %6d  cash %6d  all-in %6d" % (e["label"], e["fixed"], e["cash_monthly"], e["allin_monthly"]))

# ------------------------------------------------------------------ 2. COST PER 100 BUILDERS RESEARCHED
HOURS_PER_MONTH = 22 * 8
rate_central = C_E / HOURS_PER_MONTH
research_hours = (0.75, 1.0, 1.5)          # ASSUMPTION hours per deep dossier incl. real-owner hunt by a person
emp_per100 = [round(100 * h * rate_central) for h in research_hours]
OUT["employee_cost_per_hour"] = round(rate_central)
OUT["employee_cost_per_100_researched"] = emp_per100
print("\nEmployee hourly all-in Rs %d; cost per 100 researched (0.75/1.0/1.5 h each): %s" % (rate_central, emp_per100))

# system cost-to-serve per builder (INTERNAL), USD->INR ASSUMPTION 95 (90..97)
FX = 95
BLEND = 3.2 / 1e6       # USD per token: 85% input at $2 + 15% output at $10 per MTok (Sonnet 5.5 prices in the blueprint) - ASSUMPTION mix
tok_low, tok_cent, tok_high = 121e3, 250e3, 684e3     # 4.1M/34 measured; mid; 342K per qualified x2 for owner hunt
c_low, c_cent, c_high = [t * BLEND * FX for t in (tok_low, tok_cent, tok_high)]
qa_min = (5, 8, 12)
LABOUR_RS_H = 375       # ASSUMPTION Rs 250-500/h for IV staff time
sys_per_builder = [c + m / 60 * LABOUR_RS_H for c, m in zip((c_low, c_cent, c_high), qa_min)]
sys_per100 = [round(100 * x) for x in sys_per_builder]
OUT["system_compute_rs_per_builder"] = [round(c_low), round(c_cent), round(c_high)]
OUT["system_cost_to_serve_per_100_researched"] = sys_per100
print("System compute Rs/builder: %s ; incl. QA labour per 100: %s" % ([round(c_low), round(c_cent), round(c_high)], sys_per100))

# ------------------------------------------------------------------ 3. SYSTEM COST TO SERVE (INTERNAL)
def sys_month(builders_researched, videos, wa_msgs, hours_week, tools=3000):
    compute = builders_researched * c_cent
    video = videos * 60                      # ASSUMPTION Rs 0-120 per video (local render ~0; bespoke vendor ~Rs 119)
    wa = wa_msgs * 0.8631 * 1.15 * 1.18      # Rs 0.8631 Meta marketing rate x 15% BSP markup (assumption) x 18% GST
    labour = hours_week * 4.3 * LABOUR_RS_H
    return dict(compute=round(compute), video=round(video), whatsapp=round(wa), labour=round(labour), tools=tools,
                total=round(compute + video + wa + labour + tools))


m1 = sys_month(150, 50, 150 * 3 * 0.5, 12)
steady = sys_month(8, 3, 8 * 3 + 60, 6)
OUT["system_cost_to_serve_month1_pool150"] = m1
OUT["system_cost_to_serve_steady"] = steady
print("\nSystem cost-to-serve month 1 (150 builders):", m1)
print("System cost-to-serve steady month (new builders + follow-up):", steady)

# ------------------------------------------------------------------ 4. CLOPPER-PEARSON
def cp(k, n, alpha=0.05):
    def cdf(kk, p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(kk + 1))
    lo = 0.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(80):
            m = (a + b) / 2
            if 1 - cdf(k - 1, m) > alpha / 2:
                b = m
            else:
                a = m
        lo = (a + b) / 2
    hi = 1.0
    if k < n:
        a, b = 0.0, 1.0
        for _ in range(80):
            m = (a + b) / 2
            if cdf(k, m) < alpha / 2:
                b = m
            else:
                a = m
        hi = (a + b) / 2
    return lo, hi


for k, n in ((2, 7), (3, 7), (0, 9), (0, 30)):
    lo, hi = cp(k, n)
    print("CP 95%% %d/%d: %.1f%% - %.1f%%" % (k, n, 100 * lo, 100 * hi))
    OUT["cp_%d_of_%d" % (k, n)] = [round(100 * lo, 1), round(100 * hi, 1)]

# ------------------------------------------------------------------ 5. EXPECTED QUALIFIED CONVERSATIONS (QC) IN 90 DAYS FOR A POOL
# QC = the REAL owner / decision-maker of a builder has a two-way conversation (call or WhatsApp) about Nexus360 and does not say no.
# All rates below are ASSUMPTIONS in (pessimistic, central, optimistic) form; only pieces with a source are noted in comparison.md.
EMP = dict(route=(0.35, 0.50, 0.65),      # share of builders for whom a person finds a direct line to the real owner (asking around, site office, network)
           reach=(0.245, 0.40, 0.60),     # owners actually spoken to within 90 days (0.245 = Belkins per-prospect connect after ~3 tries)
           pos=(0.046, 0.08, 0.15))       # spoken owners who agree to a conversation/meeting (0.046 = Belkins conversation-to-meeting)
SYS = dict(route=(0.20, 0.40, 0.60),      # share of builders with a named owner AND a usable WhatsApp number from public sources
           deliver=(0.29, 0.45, 0.60),    # delivered on a cold number (our own 2 of 7 = 29% on time; Meta per-recipient limits)
           reply=(0.0, 0.025, 0.06))      # genuine owner-level reply per delivered message (own 0 of 9; vendor claims 1-2% up to 15-20%, all weak)


def qc_emp(pool, i):
    return pool * EMP["route"][i] * EMP["reach"][i] * EMP["pos"][i]


def qc_sys(pool, i):
    return pool * SYS["route"][i] * SYS["deliver"][i] * SYS["reply"][i]


def qc_hyb(pool, i):
    # executive calls the builders the system has found a line to (call prep from dossier), WhatsApp touch also reaches some the caller misses.
    return qc_emp(pool, i) + 0.7 * qc_sys(pool, i)      # 0.7 = ASSUMPTION 30% overlap


POOLS = (72, 150, 470)
rows = {}
print("\nEXPECTED QC in 90 days (pess / central / opt):")
for pool in POOLS:
    for name, f in (("employee", qc_emp), ("system", qc_sys), ("hybrid", qc_hyb)):
        vals = [round(f(pool, i), 2) for i in range(3)]
        rows["%s_pool%d_90d" % (name, pool)] = vals
        print("  pool %3d %-9s 90 days: %s   per month: %s" % (pool, name, vals, [round(v / 3, 2) for v in vals]))
OUT["expected_qc_90d"] = rows

# ------------------------------------------------------------------ 6. BREAK-EVEN
print("\nBREAK-EVEN: system beats employee on cost per QC when QC_sys >= QC_emp x (S / C_E); C_E = Rs %d" % C_E)
fees = (20000, 35000, 50000)
emp_qc = (0.5, 1.0, 2.0, 4.0)
be = {}
for s in fees:
    be[s] = {q: round(q * s / C_E, 2) for q in emp_qc}
    print("  S=%6d  ratio S/C_E=%.2f  required system QC/month for employee QC/month %s -> %s" % (s, s / C_E, emp_qc, [be[s][q] for q in emp_qc]))
OUT["breakeven_required_system_qc_per_month"] = {str(k): {str(q): v for q, v in d.items()} for k, d in be.items()}
OUT["fee_to_employee_ratio"] = {str(s): round(s / C_E, 2) for s in fees}
# cost per QC at given QC
print("\nCOST PER QC (Rs) at central cost:")
for q in emp_qc:
    print("  QC/month %.1f -> employee Rs %d ; system S=20k/35k/50k: %s" % (q, C_E / q, [round(s / q) for s in fees]))
OUT["cost_per_qc_employee"] = {str(q): round(C_E / q) for q in emp_qc}

# break-even fee for system at the central expected QCs (pool 150): fee at which cost/QC equal
for pool in (72, 150, 470):
    qe, qs = qc_emp(pool, 1) / 3, qc_sys(pool, 1) / 3
    print("  pool %d central: employee %.2f QC/month, system %.2f QC/month; fee that equalises cost per QC: Rs %d" % (pool, qe, qs, C_E * qs / qe))
    OUT["equalising_fee_pool%d_central" % pool] = round(C_E * qs / qe)

# QC needed per won customer: decision rule independent of Nexus360 price
print("\nDecision rule: allowed outbound cost per won customer = share x first-year contract value V.")
for close in (0.10, 0.20, 0.30):
    print("  close rate from QC %.0f%% -> cost per won = cost per QC / %.2f" % (close * 100, close))

# first-90-days cumulative view (decision day = day 0)
# employee: 5 weeks hiring (no pay), then 2 months at full pay, 50% output for 3 months of ramp -> within 90 days: ~2 paid months, ~0.5 effective months
# system: starts week 2 ; 2.5 months running
emp_90_cost = round(2 * C_E)           # about two paid months inside 90 days
sys_90_cost_factor = 3                  # three months of fee (S) - month 1 may carry setup
OUT["employee_first90_cost"] = emp_90_cost
print("\nFirst 90 days: employee pays ~2 months (Rs %d) with ~half output; system pays up to 3 x S" % emp_90_cost)

# pilot sizing: probability of at least one genuine reply among delivered messages at a true rate p; one-sided 95% upper bound if 0 replies
def upper0(n):
    return 1 - 0.05 ** (1.0 / n)


pilot = {}
for delivered in (13, 27, 29, 45, 100):
    pilot[delivered] = dict(p_any_at_2_5=round(1 - 0.975 ** delivered, 2), p_any_at_5=round(1 - 0.95 ** delivered, 2), p_any_at_10=round(1 - 0.90 ** delivered, 2),
                            upper95_if_zero=round(upper0(delivered), 3))
    print("  delivered %3d: P(>=1 reply) at true 2.5%% = %.0f%%, 5%% = %.0f%%, 10%% = %.0f%% ; 0 replies -> one-sided 95%% upper bound %.1f%%" % (
        delivered, 100 * (1 - 0.975 ** delivered), 100 * (1 - 0.95 ** delivered), 100 * (1 - 0.90 ** delivered), 100 * upper0(delivered)))
OUT["pilot_sizing"] = pilot
print("  0 of 9 one-sided 95%% upper bound: %.1f%%" % (100 * upper0(9)))

# delivered messages expected from a pool at central coverage (route 0.40 x deliver 0.45)
for pool in (72, 150, 470):
    print("  pool %d -> routes %.0f, delivered %.0f at central coverage" % (pool, pool * 0.40, pool * 0.40 * 0.45))

# break-even fee S* = rho x C_E ; rho = QC_sys / QC_emp
print("Break-even fee S* (Rs/month) = rho x C_E:")
sstar = {}
for rho in (0.25, 0.5, 0.75, 1.0, 1.5):
    sstar[rho] = round(rho * C_E)
    print("  rho %.2f -> Rs %d" % (rho, rho * C_E))
OUT["breakeven_fee_by_rho"] = {str(k): v for k, v in sstar.items()}
for i, name in enumerate(("pessimistic", "central", "optimistic")):
    print("  rho (system / employee, same scenario) %s: %.2f" % (name, qc_sys(150, i) / qc_emp(150, i)))
print("  rho system optimistic / employee central: %.2f ; system central / employee pessimistic: %.2f" % (qc_sys(150, 2) / qc_emp(150, 1), qc_sys(150, 1) / qc_emp(150, 0)))

# pilot floor: average monthly cost-to-serve over 3 months
floor3 = (m1["total"] + 2 * steady["total"]) / 3
OUT["pilot_floor_3_months_avg_per_month"] = round(floor3)
OUT["pilot_floor_3_months_total"] = m1["total"] + 2 * steady["total"]
print("INTERNAL: 3-month pilot cost-to-serve total Rs %d, average Rs %d per month" % (m1["total"] + 2 * steady["total"], floor3))
OUT["employee_annual_allin_central"] = C_E * 12
print("Employee annual all-in central Rs %d ; fixed CTC Rs %d" % (C_E * 12, 25000 * 12))

# new-builder flow: 151 valid approvals in 18 months in the three districts (own count) -> per month ; 72 of 146 survive the script filters (49%)
flow = 151 / 18
OUT["new_projects_per_month"] = round(flow, 1)
OUT["new_qualifying_builders_per_month"] = round(flow * 72 / 146, 1)
print("New valid approvals per month %.1f ; after the same filters about %.1f builders per month" % (flow, flow * 72 / 146))

(HERE / "comparison_numbers.json").write_text(json.dumps(OUT, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote comparison_numbers.json")
