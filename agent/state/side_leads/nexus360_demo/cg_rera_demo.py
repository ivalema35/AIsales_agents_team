# -*- coding: utf-8 -*-
"""Demo for the Nexus360 side lead: fetch Chhattisgarh's PUBLIC RERA register and turn it into a short, ranked list of small/medium builders.

What it does (and nothing more):
  1. ONE polite GET of https://rera.cgstate.gov.in/Approved_project_List.aspx (about 11 MB, no login, no CAPTCHA, no search form, no detail pages),
     cached on disk. Pass --html FILE to reuse an already downloaded copy (no request is made at all).
  2. Parses the 15-column table into rows (project, registration number, promoter, type, district, tehsil, approval date ...). The authorised person's
     name, phones, e-mails and bank fields are NOT kept.
  3. Applies filters that are printed as rules (the register has no 'company size' field, so 'small/medium' is a STAND-IN: 3 or fewer registered projects).
  4. Writes the funnel counts and a ranked table with the source URL and the fetch time on every row. No contact data anywhere.
Run:   python cg_rera_demo.py --html PATH_TO_SAVED_LIST.html        (reuse a saved copy)
       python cg_rera_demo.py --fetch                                (one live request)
Output files go next to this script: cg_rera_public_list.csv, cg_rera_demo_ranked.csv, cg_rera_demo_summary.txt
"""
import argparse
import csv
import html as htmllib
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = "https://rera.cgstate.gov.in/Approved_project_List.aspx"
UA = "IVInfotech-research/1.0 (one request for a demo; public RERA list)"
TABLE_ID = "ContentPlaceHolder1_gv_ProjectList"
DISTRICTS = ("RAIPUR", "DURG", "RAJNANDGAON")           # Sridhar's belt; Bilaspur can be added with --districts
HOUSING_TYPES = ("residential", "group housing", "plotted", "mixed", "apartment", "villa", "township")
GOVERNMENT = re.compile(r"(?i)\b(development authority|housing board|nagar nigam|municipal|corporation|authority|government|govt|vikas pradhikaran|state of)\b")


def fetch(path):
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as response:
        data = response.read()
    path.write_bytes(data)
    return datetime.now()


def clean(cell):
    text = re.sub(r"(?s)<input[^>]*>", " ", cell)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return " ".join(htmllib.unescape(text).split())


def parse(html_text):
    start = html_text.find(TABLE_ID)
    if start < 0:
        sys.exit("table %s not found: the page layout changed" % TABLE_ID)
    end = html_text.find("</table>", start)
    block = html_text[start:end]
    rows = []
    for tr in re.findall(r"(?s)<tr>(.*?)</tr>", block):
        cells = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
        if len(cells) < 13:
            continue
        website = re.search(r"href='([^']+)'", cells[11]) or re.search(r'href="([^"]+)"', cells[11])
        rows.append({
            "project": clean(cells[1]),
            "reg_no": clean(cells[2]),
            "promoter": clean(cells[4]),
            "ptype": clean(cells[5]),
            "district": clean(cells[6]).upper(),
            "tehsil": clean(cells[7]).upper(),
            "approved": clean(cells[8]),
            "end": clean(cells[9]),
            "expired": "Expired" in clean(cells[12]),
            "website": website.group(1) if website and "void(0)" not in website.group(1) else "",
        })
    return rows


def parse_date(text):
    try:
        return datetime.strptime(text.strip(), "%d %b %Y")
    except ValueError:
        return None


def norm_promoter(name):
    name = re.sub(r"(?i)\b(m/s|messrs|pvt|private|ltd|limited|llp|the)\b\.?", " ", name)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", name.lower()).split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="reuse a saved copy of the list page (no request)")
    ap.add_argument("--fetch", action="store_true", help="make ONE live request")
    ap.add_argument("--districts", default=",".join(DISTRICTS))
    ap.add_argument("--months", type=int, default=18, help="approved within the last N months")
    ap.add_argument("--max-projects", type=int, default=3, help="stand-in for 'small/medium': promoter has at most this many registered projects")
    ap.add_argument("--exclude", default="", help="comma list of name fragments to drop (e.g. the lead's own customers, with his OK)")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    if args.html:
        source = Path(args.html)
        fetched_at = datetime.fromtimestamp(source.stat().st_mtime)
    elif args.fetch:
        source = HERE / "cg_rera_list_cache.html"
        fetched_at = fetch(source)
    else:
        sys.exit("give --html FILE or --fetch")
    rows = parse(source.read_text(encoding="utf-8", errors="replace"))
    stamp = fetched_at.strftime("%Y-%m-%d %H:%M")

    with open(HERE / "cg_rera_public_list.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["project", "reg_no", "promoter", "ptype", "district", "tehsil", "approved", "end", "expired", "website"])
        writer.writeheader()
        writer.writerows(rows)

    districts = {d.strip().upper() for d in args.districts.split(",") if d.strip()}
    excluded = [x.strip().lower() for x in args.exclude.split(",") if x.strip()]
    per_promoter = Counter(norm_promoter(r["promoter"]) for r in rows)
    cutoff = datetime.now() - timedelta(days=30 * args.months)
    funnel = [("All registered projects in the register", len(rows))]
    step = [r for r in rows if r["district"] in districts]
    funnel.append(("In %s" % ", ".join(sorted(districts)), len(step)))
    step = [r for r in step if not r["expired"]]
    funnel.append(("Registration still valid (not 'Expired')", len(step)))
    step = [r for r in step if (parse_date(r["approved"]) or datetime(1970, 1, 1)) >= cutoff]
    funnel.append(("Approved in the last %d months" % args.months, len(step)))
    step = [r for r in step if any(t in r["ptype"].lower() for t in HOUSING_TYPES)]
    funnel.append(("Residential / plotted / mixed projects", len(step)))
    step = [r for r in step if not GOVERNMENT.search(r["promoter"])]
    funnel.append(("Government bodies removed", len(step)))
    step = [r for r in step if per_promoter[norm_promoter(r["promoter"])] <= args.max_projects]
    funnel.append(("Promoter has %d or fewer registered projects (stand-in for small/medium)" % args.max_projects, len(step)))
    if excluded:
        step = [r for r in step if not any(x in (r["promoter"] + " " + r["project"] + " " + r["website"]).lower() for x in excluded)]
        funnel.append(("Names you already serve removed (name match only)", len(step)))
    seen, ranked = set(), []
    for r in sorted(step, key=lambda r: parse_date(r["approved"]) or datetime(1970, 1, 1), reverse=True):
        key = norm_promoter(r["promoter"])
        if key in seen:
            continue
        seen.add(key)
        ranked.append(r)
    funnel.append(("One row per promoter (newest registration first)", len(ranked)))

    top = ranked[: args.top]
    with open(HERE / "cg_rera_demo_ranked.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "promoter", "project", "district", "tehsil", "type", "approved", "valid_until", "registration_no", "website_on_register", "source", "fetched_at"])
        for i, r in enumerate(top, 1):
            writer.writerow([i, r["promoter"], r["project"], r["district"], r["tehsil"], r["ptype"], r["approved"], r["end"], r["reg_no"], r["website"], URL, stamp])

    lines = ["CHHATTISGARH RERA - public register, fetched %s from %s" % (stamp, URL),
             "One request, no login, no CAPTCHA, no detail pages. No phone, e-mail or personal name is kept.", "", "FUNNEL (every filter is a visible rule):"]
    lines += ["  %-82s %5d" % (name, count) for name, count in funnel]
    lines += ["", "NOTE: the register has no company-size field. 'Small/medium' above is a stand-in (few registered projects), not a measurement.", "", "TOP %d:" % len(top)]
    for i, r in enumerate(top, 1):
        lines.append("  %2d. %s | %s | %s/%s | approved %s | %s" % (i, r["promoter"][:38], r["project"][:46], r["district"], r["tehsil"], r["approved"], r["reg_no"]))
    text = "\n".join(lines)
    (HERE / "cg_rera_demo_summary.txt").write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
