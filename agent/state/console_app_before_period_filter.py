# -*- coding: utf-8 -*-
"""Agent Console - the owner's read-only dashboard for the agentic sales system (replaces the old CRM screens).

The owner logs in and LOOKS. The agent writes: everything on screen comes from generic "entries" (type + JSON data + tags) that the agent
creates through an authenticated HTTPS API, so the agent decides what to track and no field is hard-coded here.
  entry types the screens understand (all fields optional; unknown types / fields are simply stored):
    product   key=slug   data: name, tagline, description, buyers[]
    campaign  key=slug   data: name, product, segment, status (draft|active|paused|done), leads, sent, replies, budget_used, budget_cap, unit
    lead      data: name, city, product, campaign (+campaign_key), grade (A|B|C|reject), status, contacted, best_angle, best_channel, case_for, case_against,
              observed_facts[], hypotheses[], contacts[{kind,value,source,note}], ...  (see leads_view.prepare; every field optional)
    activity  data: text, kind (sent|reply|lead_found|...), campaign
    metric    key=apify_spend|kie_credits|claude_usage  data: label, used, cap, unit      approval / handoff  data: title, status (open|pending|done)
    heartbeat key=agent  data: state, text      (its updated_at tells whether the agent is alive)
No hard delete (business data): DELETE only sets deleted_at. Every write is recorded in the audit table.
PUBLIC exception (no login): /p/<slug> serves the unlisted lead landing pages that the agent builds (agent/pages/build_pages.py) from the pages folder,
noindex, own CSP, and counts non-bot opens in `pageviews` (read by the agent at GET /v1/pageviews, shown on the Leads page).

Run locally:  CONSOLE_PASSWORD=... CONSOLE_API_KEY=... python console/app.py      Production: gunicorn (see deploy/deploy_console.sh)
"""
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_from_directory, session, url_for

BASE = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(BASE))
import calendar_view as cv  # noqa: E402
import email_hooks  # noqa: E402
import leads_view as lv  # noqa: E402

# The owner works in India: "today" on the calendar and in the greeting is IST unless CONSOLE_TZ_OFFSET_MIN says otherwise.
LOCAL_TZ = timezone(timedelta(minutes=int(os.environ.get("CONSOLE_TZ_OFFSET_MIN", "330"))))
TYPE_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")
RANGES = {"today": 1, "7d": 7, "30d": 30}
STATUSES = ("active", "paused", "draft", "done")
SENT_KINDS = {"sent", "email_sent", "wa_sent", "whatsapp_sent", "template_sent"}
REPLY_KINDS = {"reply", "reply_received", "lead_reply"}
# Login ke baad sirf in pages par bheja jaata hai: "next" ko kabhi bhi aise hi redirect nahi karte (open redirect se phishing ho sakti hai)
ALLOWED_NEXT = {"/", "/leads", "/products", "/campaigns"}
# Agent ki likhi entry par limit: gehri nesting ya lakhon chhote items se page load par memory/CPU na phoole (64 KB size limit akeli kaafi nahi)
MAX_DEPTH, MAX_NODES, MAX_LIST = 6, 3000, 300
LEADS_LIMIT = 2000


def load_dotenv(path):
    """KEY=VALUE lines -> os.environ (only keys that are not set yet). Used for local runs; systemd passes the real environment."""
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_ts(value):
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def backdated(value):
    """Optional created_at sent by the agent when it creates an entry (a fact that happened earlier than the sync that noticed it, e.g. yesterday's email):
    an ISO time that is not in the future (5 minutes of clock slack) and not older than 120 days; anything else is ignored (the entry gets 'now')."""
    d = parse_ts(value) if value else None
    if d is None:
        return None
    now = datetime.now(timezone.utc)
    if d > now + timedelta(minutes=5) or d < now - timedelta(days=120):
        return None
    return d.astimezone(timezone.utc).isoformat(timespec="seconds")


def relative_time(value):
    d = parse_ts(value)
    if not d:
        return ""
    s = (datetime.now(timezone.utc) - d).total_seconds()
    if s < 45:
        return "just now"
    if s < 3600:
        return "%d min ago" % max(1, s // 60)
    if s < 86400:
        return "%d h ago" % (s // 3600)
    if s < 86400 * 2:
        return "yesterday"
    return "%d days ago" % (s // 86400)


SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, key TEXT, data TEXT NOT NULL DEFAULT '{}', tags TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS ux_entries_type_key ON entries(type, key) WHERE key IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_entries_type ON entries(type, updated_at);
CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, entry_id INTEGER, detail TEXT);
CREATE TABLE IF NOT EXISTS pageviews (id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL, ts TEXT NOT NULL, device TEXT);
CREATE INDEX IF NOT EXISTS ix_pageviews_slug ON pageviews(slug, ts);
"""


def create_app(overrides=None):
    load_dotenv(BASE / ".env")
    app = Flask(__name__)
    data_dir = Path(os.environ.get("CONSOLE_DATA_DIR") or BASE / "data")
    data_dir.mkdir(parents=True, exist_ok=True)
    secret_file = data_dir / "secret_key"
    if not os.environ.get("CONSOLE_SECRET_KEY"):
        if not secret_file.exists():
            secret_file.write_text(secrets.token_hex(32), encoding="utf-8")
            try:
                os.chmod(secret_file, 0o600)
            except OSError:
                pass
        os.environ["CONSOLE_SECRET_KEY"] = secret_file.read_text(encoding="utf-8").strip()
    app.config.update(
        SECRET_KEY=os.environ["CONSOLE_SECRET_KEY"], DB_PATH=str(data_dir / "console.db"), PAGES_DIR=str(os.environ.get("CONSOLE_PAGES_DIR") or data_dir / "pages"),
        PAGES_ON=os.environ.get("CONSOLE_PAGES_ENABLED") == "1",                 # the public /p/<slug> pages are OFF unless explicitly enabled (the live landing pages are on ivinfotech.com)
        PASSWORD=os.environ.get("CONSOLE_PASSWORD", ""), API_KEY=os.environ.get("CONSOLE_API_KEY", ""),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.environ.get("CONSOLE_INSECURE_COOKIES") != "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12), MAX_CONTENT_LENGTH=256 * 1024)
    app.config.update(overrides or {})
    app.jinja_env.filters["ago"] = relative_time
    app.failed_logins = {}

    # ------------------------------------------------------------------ database
    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA journal_mode=WAL")
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    def init_db():
        conn = sqlite3.connect(app.config["DB_PATH"])
        conn.executescript(SCHEMA)
        # Products from seed/products.json (ivinfotech.com services). Safe to run on every start and on every update, and it never makes a duplicate:
        #   - a product is added only if its key AND its name are both unknown (a product the agent already added under another key counts);
        #   - one the database already has gets only its MISSING fields filled in (the website link ...): nothing the agent or the owner wrote is overwritten;
        #   - one that was deleted (soft delete) stays deleted.
        seed = BASE / "seed" / "products.json"
        if seed.exists():
            ts = now_iso()
            live_names = {str(json.loads(r[0] or "{}").get("name", "")).strip().lower()
                          for r in conn.execute("SELECT data FROM entries WHERE type='product' AND deleted_at IS NULL")}
            for p in json.loads(seed.read_text(encoding="utf-8")):
                have = conn.execute("SELECT id, data, deleted_at FROM entries WHERE type='product' AND key=? ORDER BY id DESC LIMIT 1", (p["key"],)).fetchone()
                if have is None:
                    if str(p["data"].get("name", "")).strip().lower() in live_names:
                        continue
                    conn.execute("INSERT INTO entries(type,key,data,tags,created_at,updated_at) VALUES('product',?,?,?,?,?)",
                                 (p["key"], json.dumps(p["data"], ensure_ascii=False), "[]", ts, ts))
                elif have[2] is None:
                    current = json.loads(have[1] or "{}")
                    missing = {k: v for k, v in p["data"].items() if k not in current}
                    if missing:
                        conn.execute("UPDATE entries SET data=? WHERE id=?", (json.dumps({**current, **missing}, ensure_ascii=False), have[0]))
        conn.commit()
        conn.close()

    init_db()

    def row(r):
        return {"id": r["id"], "type": r["type"], "key": r["key"], "data": json.loads(r["data"] or "{}"), "tags": json.loads(r["tags"] or "[]"),
                "created_at": r["created_at"], "updated_at": r["updated_at"]}

    def entries(etype, limit=500):
        rs = db().execute("SELECT * FROM entries WHERE type=? AND deleted_at IS NULL ORDER BY updated_at DESC, id DESC LIMIT ?", (etype, limit)).fetchall()
        return [row(r) for r in rs]

    def engagement_by_slug():
        """slug -> engagement entry (agent har messaged lead ke liye ek likhta hai, key = page slug). Leads aur Overview dono isi se padhte hain."""
        return {e["key"]: e for e in entries("engagement", LEADS_LIMIT) if e.get("key")}

    def audit(actor, action, entry_id=None, detail=""):
        db().execute("INSERT INTO audit(ts,actor,action,entry_id,detail) VALUES(?,?,?,?,?)", (now_iso(), actor, action, entry_id, str(detail)[:300]))

    # ------------------------------------------------------------------ security headers
    @app.after_request
    def headers(resp):
        public = request.path.startswith("/p/")
        resp.headers["Content-Security-Policy"] = ("default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; font-src 'self'; "
                                                   + ("media-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'" if public else
                                                      "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"))
        if public:                                   # an unlisted page for one lead: never indexed, small cache for the heavy files (video, fonts)
            resp.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
            resp.headers["Referrer-Policy"] = "no-referrer"
            resp.headers["X-Content-Type-Options"] = "nosniff"
            resp.headers["X-Frame-Options"] = "DENY"
            resp.headers["Cache-Control"] = "no-cache" if request.path.count("/") == 2 else "public, max-age=3600"
            return resp
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Cache-Control"] = "no-store" if request.path != "/static" and not request.path.startswith("/static/") else resp.headers.get("Cache-Control", "")
        return resp

    # ------------------------------------------------------------------ public lead pages (no login, unlisted, noindex)
    slug_re = re.compile(r"^[a-z0-9][a-z0-9-]{5,60}$")
    asset_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}(/[A-Za-z0-9][A-Za-z0-9._-]{0,79})?$")      # one file, or one file inside one sub-folder (fonts/)
    bot_re = re.compile(r"bot|crawl|spider|preview|facebookexternalhit|whatsapp|slurp|curl|python|monitor|headless", re.I)

    def page_dir(slug):
        if not app.config.get("PAGES_ON"):
            return None
        d = Path(app.config["PAGES_DIR"]) / slug
        return d if slug_re.match(slug) and d.is_dir() else None

    @app.get("/p/<slug>")
    def public_page(slug):
        d = page_dir(slug)
        if not d or not (d / "index.html").is_file():
            abort(404)
        ua = request.headers.get("User-Agent", "")
        device = "bot" if bot_re.search(ua) else ("mobile" if "Mobi" in ua else "desktop")
        db().execute("INSERT INTO pageviews(slug, ts, device) VALUES(?,?,?)", (slug, now_iso(), device))
        db().commit()
        return send_from_directory(d, "index.html", mimetype="text/html")

    @app.get("/p/<slug>/<path:name>")
    def public_page_file(slug, name):
        d = page_dir(slug)
        if not d or not asset_re.match(name) or ".." in name.split("/"):
            abort(404)
        return send_from_directory(d, name, conditional=True)          # conditional = Range requests, so the video can start and seek on phones

    def page_views():
        """slug -> {views (people, bots excluded), last (ISO time), mobile (how many on a phone)}"""
        rows = db().execute("SELECT slug, COUNT(*) n, MAX(ts) last, SUM(device='mobile') mob FROM pageviews WHERE device != 'bot' GROUP BY slug").fetchall()
        return {r["slug"]: {"views": r["n"], "last": r["last"], "mobile": r["mob"] or 0} for r in rows}

    # ------------------------------------------------------------------ owner login (read-only dashboard)
    def client_ip():
        fwd = request.headers.get("X-Forwarded-For", "")
        return (fwd.split(",")[-1].strip() if fwd else "") or request.remote_addr or "?"   # last hop = the one our own proxy added

    def login_required(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if not session.get("owner"):
                return redirect(url_for("login", next=request.path))
            return fn(*a, **kw)
        return wrapper

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            session["csrf"] = secrets.token_urlsafe(24)
            return render_template("login.html", error=None, csrf=session["csrf"], enabled=bool(app.config["PASSWORD"]))
        ip, t = client_ip(), time.time()
        recent = [x for x in app.failed_logins.get(ip, []) if t - x < 600]
        app.failed_logins[ip] = recent
        if len(recent) >= 5:
            return render_template("login.html", error="Too many attempts. Try again in a few minutes.", csrf=session.get("csrf", ""), enabled=True), 429
        ok = (app.config["PASSWORD"] and hmac.compare_digest(request.form.get("password", "").encode(), app.config["PASSWORD"].encode())
              and hmac.compare_digest(str(request.form.get("csrf", "")).encode(), str(session.get("csrf", "")).encode()))
        if not ok:
            recent.append(t)
            session["csrf"] = secrets.token_urlsafe(24)
            return render_template("login.html", error="Wrong password.", csrf=session["csrf"], enabled=bool(app.config["PASSWORD"])), 401
        session.clear()
        session["owner"] = True
        session.permanent = True
        nxt = request.args.get("next", "/")
        return redirect(nxt if nxt in ALLOWED_NEXT else "/")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ------------------------------------------------------------------ shared page data
    def shell():
        beat = next(iter(entries("heartbeat", 1)), None)
        age = (datetime.now(timezone.utc) - parse_ts(beat["updated_at"])).total_seconds() if beat and parse_ts(beat["updated_at"]) else None
        state = "waiting" if beat is None else ("online" if age is not None and age < 600 else "idle")
        label = {"waiting": "Waiting for the agent", "online": "Agent online", "idle": "Agent idle"}[state]
        meters = [m for m in entries("metric", 20) if m["key"] in ("kie_credits", "apify_spend", "claude_usage")]
        return {"agent_state": state, "agent_label": label, "agent_seen": relative_time(beat["updated_at"]) if beat else "", "meters": meters}

    def pct(used, cap):
        try:                              # the agent decides which fields exist: a missing one reaches us as a Jinja "Undefined"
            return max(0, min(100, round(float(used) / float(cap) * 100)))
        except Exception:                 # noqa: BLE001 - TypeError, ValueError, ZeroDivisionError, jinja2.UndefinedError ...
            return None

    app.jinja_env.globals["pct"] = pct

    def sparkline(acts, today, days=14, width=200, height=48, pad=4):
        """Activity per day for the last `days` days as SVG point lists (a line and a filled area). Pure numbers, no inline style needed."""
        counts = {(today - timedelta(days=i)).isoformat(): 0 for i in range(days)}
        for a in acts:
            d = parse_ts(a["created_at"])
            if d:
                key = d.astimezone(LOCAL_TZ).date().isoformat()
                if key in counts:
                    counts[key] += 1
        series = [counts[(today - timedelta(days=days - 1 - i)).isoformat()] for i in range(days)]
        top = max(series) or 1
        pts = [(round(i * width / (days - 1), 1), round(height - pad - (v / top) * (height - 2 * pad), 1)) for i, v in enumerate(series)]
        line = " ".join("%s,%s" % p for p in pts)
        return {"line": line, "area": "0,%d %s %d,%d" % (height, line, width, height), "total": sum(series), "peak": max(series), "days": days,
                "last": pts[-1]}

    def pipeline_tile(lead_entries):
        """Overview ka "Pipeline" tile: har lead sirf ek stage me (jahan abhi hai). Ginti leads_view.pipeline_stage se aati hai - wahi function /leads?stage= ka filter bhi use karta hai,
        isliye tile ka number aur click ke baad ki list hamesha barabar hoti hai."""
        eng = engagement_by_slug()
        counts = lv.pipeline_counts([(e["data"], (eng.get(lv.slug_of(e["data"])) or {}).get("data")) for e in lead_entries])
        total = sum(counts[key] for key, _label, _sub in lv.PIPELINE)
        stages = []
        for number, (key, label, sub) in enumerate(lv.PIPELINE, start=1):
            n = counts[key]
            # bar = poori leads me se kitna hissa (chhota non-zero bhi thoda dikhe, isliye minimum 3)
            stages.append({"no": number, "key": key, "label": label, "sub": sub, "count": n, "pct": max(3, round(n / total * 100)) if n and total else 0,
                           "href": url_for("leads", stage=key) if n else ""})
        return {"stages": stages, "total": total, "closed": counts["closed"], "closed_href": url_for("leads", stage="closed") if counts["closed"] else ""}

    # ------------------------------------------------------------------ pages
    @app.get("/")
    @login_required
    def overview():
        rng = request.args.get("range", "7d")
        rng = rng if rng in RANGES else "7d"
        # "today" starts at midnight in OUR timezone (IST), the same day boundaries the sparkline uses (review 2026-10-17: it started at UTC midnight = 05:30 IST)
        since = datetime.now(timezone.utc) - timedelta(days=RANGES[rng]) if rng != "today" else datetime.now(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
        campaigns, leads = entries("campaign"), entries("lead")
        # newest FACTS first: agent facts are written later than they happened (backdated created_at), so the feed is ordered by when they happened, not by when they were stored
        acts = sorted(entries("activity", 500), key=lambda a: (a["created_at"], a["id"]), reverse=True)
        in_range = [a for a in acts if (parse_ts(a["created_at"]) or since) >= since]
        sent = sum(1 for a in in_range if a["data"].get("kind") in SENT_KINDS)
        replies = sum(1 for a in in_range if a["data"].get("kind") in REPLY_KINDS)
        new_leads = sum(1 for lead in leads if (parse_ts(lead["created_at"]) or since) >= since)
        active = sum(1 for c in campaigns if c["data"].get("status") == "active")
        attention = [e for t in ("approval", "handoff") for e in entries(t, 20) if e["data"].get("status", "open") in ("open", "pending")]
        kpis = [
            {"label": "Active campaigns", "value": active, "sub": "of %d total" % len(campaigns) if campaigns else "none created yet", "icon": "megaphone"},
            {"label": "Leads found", "value": len(leads), "sub": "+%d in this period" % new_leads if leads else "none yet", "icon": "users",
             "href": url_for("leads") if leads else ""},
            {"label": "Messages sent", "value": sent, "sub": "in this period", "icon": "send"},
            {"label": "Replies", "value": replies, "sub": ("%d%% reply rate" % round(replies / sent * 100)) if sent else "no sends yet", "icon": "reply"},
        ]
        today = datetime.now(LOCAL_TZ).date()
        cal_events, _ = cv.collect_events(campaigns, entries("event"))
        pipeline = pipeline_tile(leads)
        hour = datetime.now(LOCAL_TZ).hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        return render_template("overview.html", page="overview", rng=rng, kpis=kpis, activity=acts[:8], attention=attention[:6], greeting=greeting, pipeline=pipeline,
                               spark=sparkline(acts, today), upcoming=cv.agenda(cal_events, today, limit=5), today=today, **shell())

    @app.get("/products")
    @login_required
    def products():
        camps, leads = entries("campaign"), entries("lead")
        rows = []
        for p in sorted(entries("product"), key=lambda e: (e["data"].get("order", 999), e["data"].get("name", ""))):
            name = str(p["data"].get("name", "")).lower()
            rows.append({**p, "n_campaigns": sum(1 for c in camps if str(c["data"].get("product", "")).lower() == name and c["data"].get("status") == "active"),
                         "n_leads": sum(1 for lead in leads if str(lead["data"].get("product", "")).lower() == name)})
        return render_template("products.html", page="products", products=rows, **shell())

    @app.get("/leads")
    @login_required
    def leads():
        # Master-detail: left = list of leads, right = the selected lead's evidence, plan and contacts. Filters live in the URL (grade, campaign, status, product).
        raw = entries("lead", LEADS_LIMIT)
        raw_by_id = {e["id"]: e for e in raw}
        everyone = sorted((lv.prepare_light(e) for e in raw), key=lv.sort_key)             # list ke liye halka data; poora text sirf kholi hui lead ka
        # Ek campaign ke do naam ho sakte hain (key aur naam): campaign entries se map banao taaki dono ek hi campaign gine jaayen
        shown_name, alias = {}, {}
        for c in entries("campaign"):
            if c["key"]:
                shown_name[c["key"]] = str(c["data"].get("name") or c["key"])
                alias[c["key"].lower()] = c["key"]
                alias.setdefault(shown_name[c["key"]].lower(), c["key"])
        for lead in everyone:
            lead["camp"] = next((alias[v.lower()] for v in (lead["campaign_key"], lead["campaign"]) if v and v.lower() in alias), lead["campaign_key"] or lead["campaign"])
        grade, camp, status, product, tier, stage = (request.args.get(k, "all") for k in ("grade", "campaign", "status", "product", "tier", "stage"))
        stage = stage.lower() if stage.lower() in lv.PIPELINE_LABEL else "all"           # Overview ke Pipeline tile ke numbers yahin khulte hain
        grade = grade.upper() if grade.upper() in lv.GRADE_RANK else ("other" if grade.lower() == "other" else "all")
        tier = tier.lower() if tier.lower() in lv.TIER_RANK or tier.lower() == "none" else "all"
        camp_wanted = alias.get(camp.lower(), camp)
        cur = {"tier": tier, "grade": grade, "campaign": camp, "status": status, "product": product, "stage": stage}

        def link(**kw):
            args = {k: v for k, v in {**cur, **kw}.items() if v and v != "all"}
            return url_for("leads", **args)

        def fits(lead, skip=""):
            """Kya lead filters me aati hai? `skip` wala filter ignore hota hai - taaki us filter ke chips me har option ki sahi ginti dikhe."""
            if skip != "grade" and grade != "all" and not (lead["grade"] not in lv.GRADE_RANK if grade == "other" else lead["grade"] == grade):
                return False
            if skip != "tier" and tier != "all" and (lead["tier"] or "none") != tier:
                return False
            return ((skip == "campaign" or camp == "all" or lead["camp"].lower() == camp_wanted.lower())
                    and (skip == "status" or status == "all" or lead["status"] == status)
                    and (stage == "all" or lead["pipe"] == stage)
                    and (product == "all" or lead["product"].lower() == product.lower()))

        eng_by_slug = engagement_by_slug()                                                                   # one small entry per messaged lead (key = page slug)
        for lead in everyone:
            eng_entry = eng_by_slug.get(lead["slug"]) if lead["slug"] else None
            eng_data = eng_entry["data"] if eng_entry else None
            lead["eng"] = lv.engagement_chip(eng_entry)
            lead["ticks"] = lv.journey(eng_data)["ticks"]                                                    # list row ki chhoti tick strip (WA / Mail / Page / Demo)
            lead["pipe"] = lv.pipeline_stage(raw_by_id[lead["id"]]["data"], eng_data)      # pipeline stage (lead["stage"] to plain-text status hai, usse mat takrao)
        shown = [lead for lead in everyone if fits(lead)]
        tier_counts = {t: sum(1 for lead in everyone if fits(lead, "tier") and (t == "all" or (lead["tier"] or "none") == t)) for t in ("all", "hungry", "warm", "cold", "none")}
        tier_tabs = ([("all", "All"), ("hungry", "Hungry"), ("warm", "Warm"), ("cold", "Cold")] + ([("none", "Not rated")] if tier_counts["none"] else [])) if any(lead["tier"] for lead in everyone) else []
        in_grade = lambda lead, g: g == "all" or (lead["grade"] not in lv.GRADE_RANK if g == "other" else lead["grade"] == g)  # noqa: E731
        grade_counts = {g: sum(1 for lead in everyone if fits(lead, "grade") and in_grade(lead, g)) for g in ("all", "A", "B", "C", "other")}
        grade_tabs = [("all", "All"), ("A", "Grade A"), ("B", "Grade B"), ("C", "Grade C")] + ([("other", "Rejected / not graded")] if grade_counts["other"] else [])
        campaign_opts, status_opts = {}, {}
        for lead in everyone:
            if lead["camp"]:
                campaign_opts.setdefault(lead["camp"], [shown_name.get(lead["camp"]) or lead["campaign"] or lead["camp"], 0])
            status_opts.setdefault(lead["status"], [lead["status_label"], 0])
        for lead in everyone:
            if fits(lead, "campaign") and lead["camp"]:
                campaign_opts[lead["camp"]][1] += 1
            if fits(lead, "status"):
                status_opts[lead["status"]][1] += 1
        wanted = request.args.get("lead", type=int)
        selected = next((lead for lead in everyone if lead["id"] == wanted), None) if wanted else None
        explicit = selected is not None
        selected = selected or (shown[0] if shown else None)
        if selected:
            selected = {**lv.prepare(raw_by_id[selected["id"]]), "camp": selected["camp"]}
            selected_eng = eng_by_slug.get(selected["slug"]) if selected["slug"] else None
            selected["eng"] = lv.prepare_engagement(selected_eng)
            selected["journey"] = lv.journey(selected_eng["data"] if selected_eng else None)
            slug = str((raw_by_id[selected["id"]]["data"] or {}).get("page_slug") or "")
            if slug_re.match(slug):
                v = page_views().get(slug)
                selected["page"] = {"slug": slug, "url": "/p/" + slug, "views": v["views"] if v else 0, "last": relative_time(v["last"]) if v else "", "mobile": v["mobile"] if v else 0}
        return render_template("leads.html", page="leads", leads=shown, total=len(everyone), selected=selected, explicit=explicit, link=link, cur=cur,
                               sel_campaign=camp_wanted if camp != "all" else "all", grade_counts=grade_counts, tier_tabs=tier_tabs, tier_counts=tier_counts, grade_tabs=grade_tabs,
                               campaign_opts=campaign_opts if len(campaign_opts) > 1 else {}, status_opts=status_opts if len(status_opts) > 1 else {},
                               stage_label=lv.PIPELINE_LABEL.get(stage, ""), filtered=any(v != "all" for v in cur.values()), capped=len(raw) >= LEADS_LIMIT, limit=LEADS_LIMIT, **shell())

    @app.get("/campaigns")
    @login_required
    def campaigns():
        status = request.args.get("status", "all")
        status = status if status in STATUSES else "all"
        view = "list" if request.args.get("view") == "list" or request.args.get("status") else "calendar"
        allc = entries("campaign")
        counts = {s: sum(1 for c in allc if c["data"].get("status", "draft") == s) for s in STATUSES}
        shown = [c for c in allc if status == "all" or c["data"].get("status", "draft") == status]
        today = datetime.now(LOCAL_TZ).date()
        year, month = cv.parse_month(request.args.get("m"), today)
        events, unscheduled = cv.collect_events(allc, entries("event"))
        return render_template("campaigns.html", page="campaigns", campaigns=shown, status=status, counts=counts, total=len(allc), view=view,
                               cal=cv.build_month(year, month, events, today), month=("%04d-%02d" % (year, month)), unscheduled=unscheduled,
                               agenda=cv.agenda(events, today), has_events=bool(events), today=today, **shell())

    # ------------------------------------------------------------------ agent API (bearer key, writes only through here)
    def api_auth(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            key = app.config["API_KEY"]
            sent = request.headers.get("Authorization", "")
            if not key or len(key) < 24:
                return jsonify(error="api_disabled"), 503
            if not (sent.startswith("Bearer ") and hmac.compare_digest(sent[7:].encode(), key.encode())):
                return jsonify(error="unauthorized"), 401
            return fn(*a, **kw)
        return wrapper

    def shape_ok(value, depth=0, counter=None):
        """False agar data bahut gehra hai, kisi list me MAX_LIST se zyada items hain, ya kul MAX_NODES se zyada values hain."""
        counter = counter if counter is not None else [0]
        counter[0] += 1
        if counter[0] > MAX_NODES or depth > MAX_DEPTH:
            return False
        if isinstance(value, dict):
            return all(shape_ok(v, depth + 1, counter) for v in value.values())
        if isinstance(value, list):
            return len(value) <= MAX_LIST and all(shape_ok(v, depth + 1, counter) for v in value)
        return True

    def clean(body):
        if not isinstance(body, dict):
            return None, "body must be a JSON object"
        data = body.get("data", {})
        tags = body.get("tags", [])
        if not isinstance(data, dict) or len(json.dumps(data)) > 65536:
            return None, "data must be an object up to 64 KB"
        if not shape_ok(data):
            return None, "data is nested too deeply (max %d levels), a list is longer than %d items, or there are more than %d values" % (MAX_DEPTH, MAX_LIST, MAX_NODES)
        if not isinstance(tags, list) or len(tags) > 20 or not all(isinstance(t, str) and 0 < len(t) <= 40 for t in tags):
            return None, "tags must be a list of up to 20 short strings"
        return {"data": data, "tags": tags}, None

    @app.get("/v1/health")
    def health():
        return jsonify(ok=True, time=now_iso())

    @app.get("/v1/pageviews")
    @api_auth
    def api_pageviews():
        return jsonify(items=page_views())

    @app.get("/v1/entries")
    @api_auth
    def api_list():
        sql, args = "SELECT * FROM entries WHERE deleted_at IS NULL", []
        if request.args.get("type"):
            sql += " AND type=?"
            args.append(request.args["type"])
        if request.args.get("key"):
            sql += " AND key=?"
            args.append(request.args["key"])
        sql += " ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?"
        try:
            limit = max(1, min(int(request.args.get("limit", 100) or 100), 500))
            offset = max(0, int(request.args.get("offset", 0) or 0))                    # paging: the sync reads ALL email events, 500 at a time
        except ValueError:
            return jsonify(error="invalid_request", detail="limit and offset must be numbers"), 400
        args += [limit, offset]
        items = [row(r) for r in db().execute(sql, args).fetchall()]
        if request.args.get("tag"):
            items = [i for i in items if request.args["tag"] in i["tags"]]
        return jsonify(items=items)

    @app.post("/v1/entries")
    @api_auth
    def api_upsert():
        body = request.get_json(silent=True)
        c, err = clean(body)
        etype, key = (body or {}).get("type", "") if isinstance(body, dict) else "", (body or {}).get("key") if isinstance(body, dict) else None
        if err or not TYPE_RE.match(str(etype)) or (key is not None and not (isinstance(key, str) and 0 < len(key) <= 120)):
            return jsonify(error="invalid_request", detail=err or "type must look like 'campaign'; key is an optional string up to 120 chars"), 400
        ts, existing = now_iso(), None
        if key is not None:
            existing = db().execute("SELECT id FROM entries WHERE type=? AND key=? AND deleted_at IS NULL", (etype, key)).fetchone()
        if existing:
            db().execute("UPDATE entries SET data=?, tags=?, updated_at=? WHERE id=?", (json.dumps(c["data"], ensure_ascii=False), json.dumps(c["tags"]), ts, existing["id"]))
            eid, action = existing["id"], "update"
        else:
            created = backdated(body.get("created_at")) or ts          # only when the entry is CREATED; an update never changes it
            cur = db().execute("INSERT INTO entries(type,key,data,tags,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                               (etype, key, json.dumps(c["data"], ensure_ascii=False), json.dumps(c["tags"]), created, ts))
            eid, action = cur.lastrowid, "create"
        audit("agent", action, eid, etype)
        db().commit()
        return jsonify(row(db().execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone())), 200 if existing else 201

    @app.route("/v1/entries/<int:eid>", methods=["GET", "PATCH", "DELETE"])
    @api_auth
    def api_one(eid):
        r = db().execute("SELECT * FROM entries WHERE id=? AND deleted_at IS NULL", (eid,)).fetchone()
        if not r:
            return jsonify(error="not_found"), 404
        if request.method == "GET":
            return jsonify(row(r))
        if request.method == "DELETE":
            db().execute("UPDATE entries SET deleted_at=?, updated_at=? WHERE id=?", (now_iso(), now_iso(), eid))
            audit("agent", "delete", eid, r["type"])
            db().commit()
            return jsonify(ok=True)
        body = request.get_json(silent=True)
        c, err = clean(body)
        if err:
            return jsonify(error="invalid_request", detail=err), 400
        merged = {**json.loads(r["data"] or "{}"), **c["data"]}                       # PATCH = shallow merge of data
        if len(json.dumps(merged)) > 65536 or not shape_ok(merged):                 # merge ke baad bhi wahi limit, warna entry PATCH-PATCH karke phool jaati hai
            return jsonify(error="invalid_request", detail="the merged data would be over 64 KB or too deeply nested"), 400
        tags = c["tags"] if isinstance(body, dict) and "tags" in body else json.loads(r["tags"] or "[]")
        db().execute("UPDATE entries SET data=?, tags=?, updated_at=? WHERE id=?", (json.dumps(merged, ensure_ascii=False), json.dumps(tags), now_iso(), eid))
        audit("agent", "patch", eid, r["type"])
        db().commit()
        return jsonify(row(db().execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()))

    # ------------------------------------------------------------------ Resend webhook (PUBLIC route: the Svix signature is the only gate)
    def hook_secret():
        """The webhook secret, read FRESH from the env file on every call (a secret saved or rotated by set_vps_secret.ps1 works without a restart); the process environment
        is only the fallback when the file has no such line (tests, other setups)."""
        try:
            for line in Path(os.environ.get("CONSOLE_ENV_FILE", "/opt/agent-console/.env")).read_text(encoding="utf-8").splitlines():
                if line.startswith("CONSOLE_RESEND_WEBHOOK_SECRET="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
        return os.environ.get("CONSOLE_RESEND_WEBHOOK_SECRET", "").strip()

    def store_email_event(key, created_at, data):
        """One `email_event` entry per webhook call, upserted by the Svix message id (Resend's retries cannot duplicate it); created_at = the real event time."""
        ts = now_iso()
        found = db().execute("SELECT id FROM entries WHERE type='email_event' AND key=? AND deleted_at IS NULL", (key,)).fetchone()
        if found:
            db().execute("UPDATE entries SET data=?, updated_at=? WHERE id=?", (json.dumps(data, ensure_ascii=False), ts, found["id"]))
            eid = found["id"]
        else:
            cur = db().execute("INSERT INTO entries(type,key,data,tags,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                               ("email_event", key, json.dumps(data, ensure_ascii=False), "[]", backdated(created_at) or ts, ts))
            eid = cur.lastrowid
        audit("resend", "event", eid, "email_event")
        db().commit()

    @app.post("/hooks/resend")
    def resend_webhook():
        if (request.content_length or 0) > email_hooks.MAX_BODY:
            return jsonify(ok=False, detail="body too large"), 400
        status, detail = email_hooks.handle(request.get_data(cache=False), request.headers, hook_secret(), store_email_event)
        return jsonify(ok=status == 200, detail=detail), status

    return app


app = create_app() if os.environ.get("CONSOLE_AUTOSTART", "1") == "1" else None

if __name__ == "__main__":
    (app or create_app()).run(host="127.0.0.1", port=int(os.environ.get("CONSOLE_PORT", "5010")))
