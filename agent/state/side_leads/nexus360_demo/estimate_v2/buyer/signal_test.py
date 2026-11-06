"""
Signal test on the PUBLIC Chhattisgarh RERA register (no personal data is printed or saved).

What it does: reads the public project list we already saved (cg_rera_public_list.csv) and the register's
own "Ongoing projects" page, groups promoter names into builder groups (same promoter name, or same website),
removes government / co-operative / trust bodies and Nexus360's own customers, and counts how many builders
fit each signal. It prints counts only.

Run:  C:/ivtools/venv/Scripts/python.exe -I signal_test.py [path_to_ongoing_page.html]
If no path is given it makes ONE polite GET of https://rera.cgstate.gov.in/Approved_project_List_ongoing.aspx
(public page, no login, no CAPTCHA). Date of the numbers in buyer_explained.md: 20 Oct 2026.
"""
import csv, sys, re, html, collections, urllib.request
from datetime import datetime
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")
BASE = "C:/Users/Administrator/Desktop/AISales_agent_team/agent/state/side_leads/nexus360_demo/"
TODAY = datetime(2026, 10, 20)
CORE = {"RAIPUR", "DURG", "RAJNANDGAON"}  # the belt where Nexus360 already has customers
APARTMENT_LIKE = ("Group Housing", "Mixed Development", "Commercial")
PLOTTED = ("Plotted Development", "Residential Plotted Development", "Commercial Plotted Development", "Mixed Plotted Development")


def parse_date(s):
    try:
        return datetime.strptime(s.strip(), "%d %b %Y")
    except Exception:
        return None


def norm(n):
    # Same promoter written in different ways -> one key
    n = re.sub(r"[^A-Z0-9 ]", " ", n.upper())
    n = re.sub(r"\bM S\b|\bMS\b", "", n)
    n = re.sub(r"\bPRIVATE\b", "PVT", n)
    n = re.sub(r"\bLIMITED\b", "LTD", n)
    n = re.sub(r"\bPVT LTD\b|\bPVT\b|\bLTD\b|\bLLP\b|\bTHE\b", "", n)
    return re.sub(r"\s+", " ", n).strip()


GOV_NAME = re.compile(r"HOUSING BOARD|\bCGHB\b|MUNICIPAL|NAGAR NIGAM|NAGAR PALIK|PALIKA|DEVELOPMENT AUTHORITY|\bAUTHORITY\b|SAHKARI|SAHAKARI|SAMITI|\bSOCIETY\b|GOVT|GOVERNMENT|PRADHIKARAN|PANCHAYAT|RAILWAY|\bPWD\b|UNIVERSITY|AIIMS|\bTRUST\b|NAYA RAIPUR|\bNIGAM\b|E\.E\.|EXECUTIVE ENGINEER|COMMISSIONER|CHIEF MUNICIPAL|SADA\b", re.I)
BAD_DOMAINS = {"google.com", "na.com", "https:", "", "rera.cgstate.gov.in"}
GOV_DOMAINS = ("cghb.gov.in", "cghb.cg.nic.in", "nagarnigamraipur.nic.in", "cgpmay.in", "bhilainagarnigam.com", "mcrjn.com", "municipalcorporationdurg.in")


def domain_of(ws):
    ws = (ws or "").strip()
    if not ws:
        return ""
    h = urlparse(ws if "://" in ws else "http://" + ws).netloc.lower().replace("www.", "")
    return "" if h in BAD_DOMAINS else h


def is_gov(name, dom):
    return bool(GOV_NAME.search(name)) or dom in GOV_DOMAINS or dom.endswith(".nic.in") or dom.endswith(".gov.in")


def table_rows(page):
    page = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", page)
    out = []
    for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", page):
        cells = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip() for c in cells]
        if cells:
            out.append(cells)
    return out


# ---------- load data ----------
main = list(csv.DictReader(open(BASE + "cg_rera_public_list.csv", encoding="utf-8-sig")))
cust = list(csv.DictReader(open(BASE + "2_nexus360_customers_in_cg_rera.csv", encoding="utf-8-sig")))
ranked = list(csv.DictReader(open(BASE + "cg_rera_demo_ranked.csv", encoding="utf-8-sig")))
if len(sys.argv) > 1:
    ong_page = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
else:
    req = urllib.request.Request("https://rera.cgstate.gov.in/Approved_project_List_ongoing.aspx", headers={"User-Agent": "Mozilla/5.0 (research; IV Infotech)"})
    ong_page = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", errors="ignore")

reg_dom = {r["reg_no"].replace("*", "").strip().upper(): domain_of(r["website"]) for r in main}
ongoing = []
for c in table_rows(ong_page):
    if len(c) == 15 and c[0].isdigit():
        reg = c[2].strip().upper()
        ongoing.append(dict(reg=reg, promoter=c[4], ptype=c[5], district=c[6].upper(), ap=parse_date(c[8]), end=parse_date(c[9]), dom=reg_dom.get(reg, "")))

print("=== A. The register on 20 Oct 2026 ===")
print("project registrations in the saved list:", len(main))
print("distinct promoter names (after tidy-up):", len(set(norm(r["promoter"]) for r in main)))
print("share of rows that have a website filled on the register: %.1f%%" % (100 * sum(bool(domain_of(r["website"])) for r in main) / len(main)))

# ---------- builder groups: same promoter name OR same website ----------
parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    parent[find(a)] = find(b)


for r in main:
    k = "P:" + norm(r["promoter"])
    find(k)
    dm = domain_of(r["website"])
    if dm and not is_gov(r["promoter"], dm):
        union(k, "D:" + dm)
group_main = collections.defaultdict(list)
for r in main:
    group_main[find("P:" + norm(r["promoter"]))].append(r)
print("builder groups after merging names that share a website:", len(group_main))

cust_dom = set(domain_of(c["website"]) for c in cust if c["website"].strip())
cust_pn = set(norm(c["promoter"]) for c in cust)

groups = collections.defaultdict(list)
for r in ongoing:
    r["pn"] = norm(r["promoter"])
    r["gov"] = is_gov(r["promoter"], r["dom"])
    r["late"] = bool(r["end"] and r["end"] < TODAY)
    r["new12"] = bool(r["ap"] and (TODAY - r["ap"]).days <= 365)
    groups[find("P:" + r["pn"])].append(r)

gov_groups = {k for k, v in groups.items() if sum(x["gov"] for x in v) >= len(v) / 2}
cust_groups = {k for k, v in groups.items() if any(x["pn"] in cust_pn or (x["dom"] and x["dom"] in cust_dom) for x in v)}
private = {k: v for k, v in groups.items() if k not in gov_groups and k not in cust_groups}
core = {k: v for k, v in private.items() if any(x["district"] in CORE for x in v)}

print("\n=== B. Who is building RIGHT NOW (register's own 'Ongoing projects' page) ===")
print("ongoing projects:", len(ongoing))
print("builder groups with at least one ongoing project:", len(groups))
print("  minus government / housing board / municipal / co-operative / trust bodies:", len(gov_groups))
print("  minus Nexus360's own customers (name or website match):", len(cust_groups))
print("  = private builder groups that could be prospects (all Chhattisgarh):", len(private))
print("  of which with an ongoing project in Raipur / Durg / Rajnandgaon:", len(core))


def band(n):
    return "1" if n == 1 else "2" if n == 2 else "3-4" if n <= 4 else "5-8" if n <= 8 else "9+"


for label, S in (("all Chhattisgarh", private), ("Raipur+Durg+Rajnandgaon", core)):
    c = collections.Counter(band(len(v)) for v in S.values())
    print("\n--- " + label + f" ({len(S)} builder groups) ---")
    print("ongoing projects per builder:", {k: c[k] for k in ("1", "2", "3-4", "5-8", "9+")})
    two = [v for v in S.values() if len(v) >= 2]
    print("builders with 2+ ongoing projects:", len(two), "= %.0f%%" % (100 * len(two) / len(S)))
    print("builders whose ONLY ongoing project is a plotted layout:", sum(len(v) == 1 and v[0]["ptype"] in PLOTTED for v in S.values()))
    print("builders with 2+ ongoing AND one running past its ORIGINAL end date:", sum(len(v) >= 2 and any(x["late"] for x in v) for v in S.values()))
    print("builders with ANY ongoing project past its original end date:", sum(any(x["late"] for x in v) for v in S.values()))
    print("builders with 2+ ongoing AND one registered in the last 12 months (second/third project):", sum(len(v) >= 2 and any(x["new12"] for x in v) for v in S.values()))
    best = sum(2 <= len(v) <= 8 and any(x["new12"] for x in v) and any(not x["new12"] for x in v) and any(x["ptype"] in APARTMENT_LIKE for x in v) for v in S.values())
    print("BEST FIT (2-8 ongoing, a new one in last 12 months plus an older one, at least one apartment/mixed/commercial):", best)
    print("large groups with 9+ ongoing (probably have their own IT already - treat separately):", c["9+"])

# ---------- flow of new entrants ----------
print("\n=== C. Flow: how many builders appear each month ===")
for mo in (3, 6, 12, 24):
    rows = [r for r in main if parse_date(r["approved"]) and (TODAY - parse_date(r["approved"])).days <= mo * 30.4]
    print(f"registered in the last {mo} months: {len(rows)} projects from {len(set(norm(r['promoter']) for r in rows))} promoter names")
first = {}
for k, v in group_main.items():
    ds = [parse_date(r["approved"]) for r in v if parse_date(r["approved"])]
    if ds:
        first[k] = min(ds)
new_groups = [k for k, d in first.items() if (TODAY - d).days <= 365]
priv_new = [k for k in new_groups if not (sum(is_gov(r["promoter"], domain_of(r["website"])) for r in group_main[k]) >= len(group_main[k]) / 2)]
print("builder groups whose FIRST EVER registration is in the last 12 months (private):", len(priv_new), "= about %.0f a month" % (len(priv_new) / 12))

# ---------- earlier ranked list ----------
print("\n=== D. The earlier top-20 list (3 or fewer projects, newest first) judged by the new rule ===")
bands = []
for r in ranked:
    k = find("P:" + norm(r["promoter"]))
    bands.append(band(len(groups[k])) if k in groups else "none ongoing")
print("ongoing projects per builder in that top 20:", dict(collections.Counter(bands)))

# ---------- expansion flow: new project from a builder that already had one ----------
print("\n=== E. Trigger flow: second / third projects ===")
recent = [r for r in main if parse_date(r["approved"]) and (TODAY - parse_date(r["approved"])).days <= 365]
expansion = 0
new_builder = 0
for r in recent:
    g = group_main[find("P:" + norm(r["promoter"]))]
    older = [x for x in g if parse_date(x["approved"]) and parse_date(x["approved"]) < parse_date(r["approved"])]
    if older:
        expansion += 1
    else:
        new_builder += 1
print("projects registered in the last 12 months:", len(recent), "| from a builder that already had an earlier registration:", expansion, "| first-ever for that builder:", new_builder)
print("= about %.0f expansion projects and %.0f first-time projects a month (statewide, includes government bodies)" % (expansion / 12, new_builder / 12))

# ---------- simple fit score (OPINION: points are a starting point, to be tuned on Sridhar's real customers) ----------
print("\n=== F. Simple fit score on the Raipur/Durg/Rajnandgaon builders (max 9 points) ===")
print("+3 two to eight ongoing projects | +2 a new project in last 12 months AND an older one | +2 at least one apartment/commercial/mixed project | +1 website on register | +1 any project past its original end date")
tiers = collections.Counter()
for k, v in core.items():
    n = len(v)
    s = 0
    if 2 <= n <= 8:
        s += 3
    if any(x["new12"] for x in v) and any(not x["new12"] for x in v):
        s += 2
    if any(x["ptype"] in APARTMENT_LIKE for x in v):
        s += 2
    if any(x["dom"] for x in v):
        s += 1
    if any(x["late"] for x in v):
        s += 1
    tier = "A (6-9)" if s >= 6 else "B (3-5)" if s >= 3 else "C (0-2)"
    if n >= 9:
        tier = "Large (9+ ongoing, handle separately)"
    tiers[tier] += 1
for t, c in sorted(tiers.items()):
    print(f"  tier {t}: {c} builders")

# ---------- where else (districts outside the 3-district belt) ----------
print("\n=== G. Private builder groups with an ongoing project, by district (a group can appear in more than one) ===")
dist = collections.Counter()
for k, v in private.items():
    for dd in set(x["district"] for x in v):
        dist[dd] += 1
print(dict(dist.most_common(8)))
