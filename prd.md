# Development Roadmap — Autonomous AI Sales Multi-Agent System (`prd.md`)

**Companion to:** *AI Sales Multi-Agent System Requirements (PRD v3)*
**Build model:** 4 phases, each with a hard gate. Do not start a phase until the previous phase's **Definition of Done** checklist is fully green.

---

## 0. How to use this roadmap

Each phase gives you three things:

1. **File & directory structure** — exactly what to create in that phase.
2. **Implementation blueprints** — the tricky/critical code written out; the routine glue described so you don't copy-paste your way into bugs.
3. **Verification steps** — concrete tests that must pass before the gate opens.

Code blocks are **blueprints**, not final line-for-line implementations — they show the shape, the non-obvious logic, and the failure-mode handling. Fill in the routine bodies (CRUD field mapping, HTML extraction selectors, UI styling) yourself.

Two schema additions vs. PRD v3 are introduced where they're first needed and flagged inline: a `jobs` table (Phase 2, durable pacing), a `suppression_list` table + `provider_message_id` column (Phase 3–4, compliance & idempotency).

---

## 1. Global project structure (final target)

```
ai-sales-agent/
├── backend/
│   ├── app.py                        # Flask app factory + entrypoint
│   ├── config.py                     # env-driven config (NO secrets in code)
│   ├── requirements.txt
│   ├── .env.example
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_config.py              # engine, session factory, PRAGMA listener
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   └── schema.sql                # raw DDL (reference / bootstrap)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── products.py               # /api/v1/products  CRUD
│   │   ├── leads.py                  # /api/v1/leads
│   │   ├── scoring.py                # /api/v1/score
│   │   ├── outreach.py               # /api/v1/outreach (enqueue only)
│   │   ├── inbound.py                # /api/v1/inbound/webhook
│   │   └── reports.py                # /api/v1/reports
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_service.py           # atomic claim + state transitions
│   │   ├── ai_scoring_service.py     # Gemini scoring
│   │   ├── intent_service.py         # inbound intent classification
│   │   ├── reporting_service.py
│   │   ├── data_acquisition/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # LeadSourceProvider interface
│   │   │   ├── places_provider.py    # Google Places API (official) — DEFAULT
│   │   │   ├── serp_provider.py      # SerpAPI / Serper — DEFAULT
│   │   │   ├── b2b_provider.py       # Apollo / PDL / Hunter enrichment
│   │   │   └── playwright_fallback.py# generic render+extract (no evasion)
│   │   └── outreach/
│   │       ├── __init__.py
│   │       ├── email_service.py      # Resend + compliance headers
│   │       ├── whatsapp_service.py   # WhatsApp Cloud API (official)
│   │       └── suppression.py        # unsubscribe / suppression checks
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── job_queue.py              # enqueue + atomic claim on jobs table
│   │   └── worker.py                 # background poller loop (pacing, retries)
│   ├── scraper_worker/
│   │   ├── __init__.py
│   │   └── async_runner.py           # dedicated asyncio process
│   └── tests/
│       ├── conftest.py
│       ├── test_db_pragmas.py
│       ├── test_atomic_claim.py
│       ├── test_job_queue.py
│       ├── test_scoring_schema.py
│       ├── test_scraper_memory.py
│       ├── test_suppression.py
│       └── test_inbound_edge_cases.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/client.js
│       ├── pages/{Dashboard.jsx, Products.jsx}
│       └── components/{ProductForm.jsx, LeadPipeline.jsx, LeadCard.jsx, AlertsPanel.jsx}
├── n8n/
│   ├── docker-compose.yml
│   └── workflows/                    # exported JSON (described in Phase 3–4)
└── README.md
```

---

## 2. A note on the data-acquisition layer (read once)

The system's reliability ceiling is set here, not in the Flask/SQLite plumbing. The roadmap wires discovery/enrichment behind a **provider interface** so the *what* (a lead source) is decoupled from the *how* (API vs. rendered page):

- **Default & recommended:** Google **Places API** (business discovery), **SerpAPI/Serper** (search results, scraped legally on their side), a **B2B provider** (Apollo / People Data Labs / Hunter) for firmographics + contacts. These give you SLAs, stable schemas, and no ToS/legal overhang.
- **Fallback only:** `playwright_fallback.py` is a *generic* render-and-extract helper for the long tail of sites that have no API. It contains no proxy rotation, fingerprint spoofing, or CAPTCHA handling — pointing it at heavily-defended surfaces (Google Maps at volume, logged-in LinkedIn) will decay into a maintenance tax and risks IP/domain blocklisting. Treat it as a last resort, not the engine.

If you later decide to point the fallback at a defended surface anyway, that's your call to make — just keep it behind the same interface so the rest of the system never depends on it working.

---

# PHASE 1 — Foundation & Database

**Goal:** A running Flask app with a WAL-mode SQLite DB, correct pragmas on every connection, ORM models, and Product + Lead CRUD endpoints. No scraping, no LLM yet.

### 1.1 Files created this phase

```
backend/app.py, config.py, requirements.txt, .env.example
backend/database/{db_config.py, models.py, schema.sql}
backend/api/{__init__.py, products.py, leads.py}
backend/tests/{conftest.py, test_db_pragmas.py}
```

### 1.2 Setup

1. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
2. `requirements.txt` (Phase 1 subset): `flask`, `sqlalchemy`, `python-dotenv`, `pytest`.
3. Copy `.env.example` → `.env`. Never hardcode keys (your v3 sample had the Gemini key inline — kill that pattern now).

### 1.3 Blueprints

**`config.py`** — env-driven, no secrets in source:

```python
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DB_PATH = os.getenv("DB_PATH", "sales_system.db")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")        # loaded, never printed
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    ENV = os.getenv("ENV", "development")
```

**`database/db_config.py`** — the pragma listener is the most important 15 lines in Phase 1:

```python
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

Base = declarative_base()
engine = create_engine(
    f"sqlite:///{Config.DB_PATH}",
    connect_args={"check_same_thread": False},  # we open sessions per-thread
    future=True,
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")     # persistent; harmless to repeat
        cur.execute("PRAGMA foreign_keys=ON;")      # MUST be per-connection
        cur.execute("PRAGMA synchronous=NORMAL;")   # safe + fast under WAL
        cur.execute("PRAGMA busy_timeout=10000;")   # 10s lock wait
        cur.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
```

> **Why this matters:** `foreign_keys` and `busy_timeout` are *per-connection* — set them anywhere else and your `ON DELETE CASCADE` silently no-ops and you get spurious "database is locked". `journal_mode=WAL` is persistent once set but re-running it per-connect is cheap and keeps the guarantee local.

**`database/models.py`** — ORM mirror of the v3 DDL. Store JSON columns as `Text` and (de)serialize in the service layer, or use SQLAlchemy's `JSON` type. Add the two indexes from v3. Skeleton for one model:

```python
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, func
from database.db_config import Base

class Lead(Base):
    __tablename__ = "leads"
    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String, nullable=False)
    status = Column(String, default="DISCOVERED")  # see PRD v3 state list
    # ...remaining columns per DDL...
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
```

**`api/products.py`** — standard CRUD blueprint (`GET/POST/PUT/DELETE /api/v1/products`). Validate `target_keywords` / `pain_point_mappings` are valid JSON on write. Return 422 on bad JSON, not 500.

**`app.py`** — app factory: create tables on boot (`Base.metadata.create_all(engine)`), register blueprints, add a `/health` route returning `{"status":"ok"}`.

### 1.4 Verification (gate)

- `test_db_pragmas.py`: open a session, assert `PRAGMA journal_mode` returns `wal`, `PRAGMA foreign_keys` returns `1`.
- **FK cascade test:** insert a product + lead, delete the product, assert the lead is gone (proves `foreign_keys=ON` is actually live on the connection).
- Product CRUD round-trips via `curl`/pytest client; bad JSON in `target_keywords` returns 422.
- `/health` returns 200. App boots with an empty DB and creates `sales_system.db`, `-wal`, `-shm` files.

**✅ Phase 1 DoD:** pragmas verified live, cascade delete works, Product+Lead CRUD green, secrets only in `.env`.

---

# PHASE 2 — Async Scraper Process & Gemini Scoring

**Goal:** A dedicated async data-acquisition worker (providers-first), a durable job queue for pacing/retries, and a Gemini 2.5 Flash scoring service that returns validated JSON.

### 2.1 Files created this phase

```
backend/services/data_acquisition/{base.py, places_provider.py, serp_provider.py, b2b_provider.py, playwright_fallback.py}
backend/services/ai_scoring_service.py
backend/jobs/{job_queue.py, worker.py}
backend/scraper_worker/async_runner.py
backend/tests/{test_job_queue.py, test_scoring_schema.py, test_scraper_memory.py}
```

Add `google-genai`, `httpx`, `playwright` to `requirements.txt`; run `playwright install chromium`.

### 2.2 Schema addition — `jobs` table (durable pacing + retries)

Add to `schema.sql` and `models.py`:

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id            TEXT PRIMARY KEY,
    job_type      TEXT NOT NULL,      -- DISCOVER, ENRICH, SCORE, OUTREACH_EMAIL, OUTREACH_WA
    payload       TEXT NOT NULL,      -- JSON
    status        TEXT DEFAULT 'PENDING', -- PENDING, CLAIMED, DONE, FAILED, DEAD
    run_after     TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- pacing: don't run before this
    attempts      INTEGER DEFAULT 0,
    max_attempts  INTEGER DEFAULT 3,
    last_error    TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_jobs_due ON jobs (status, run_after);
```

This is what makes pacing **non-blocking and crash-safe**: instead of `time.sleep()` in a thread, you enqueue a job with `run_after = now + delay`. A poller drains due jobs. Restart the process and nothing is lost.

### 2.3 Blueprints

**`data_acquisition/base.py`** — the interface everything else depends on:

```python
from abc import ABC, abstractmethod
from typing import Iterable

class LeadSourceProvider(ABC):
    @abstractmethod
    async def discover(self, query: str, region: str, limit: int) -> Iterable[dict]:
        """Return raw lead dicts: {company_name, website_url, phone, source, ...}."""
```

**`places_provider.py`** (default discovery) — call the Places API `searchText` / nearby endpoints with `httpx`, map results to the lead dict shape. This is the path you should actually run in production.

**`serp_provider.py`** — hit SerpAPI/Serper for query-based discovery where Places doesn't fit; JSON in, lead dicts out.

**`playwright_fallback.py`** — generic, no evasion:

```python
from playwright.async_api import async_playwright

async def fetch_rendered(url: str, wait_selector: str | None = None, timeout=30000) -> str:
    """Render a page and return HTML. Generic fallback for sites with no API."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            await page.goto(url, timeout=timeout)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=10000)
            return await page.content()
        finally:                      # STRICT cleanup — the anti-leak guarantee
            await page.close()
            await context.close()
            await browser.close()
```

Parse the returned HTML with `selectolax`/`BeautifulSoup` in a separate extractor function. Keep rendering and parsing separate so parsing is unit-testable without a browser.

**`scraper_worker/async_runner.py`** — a dedicated process (not a Flask thread) that owns one asyncio loop, pulls `DISCOVER`/`ENRICH` jobs, calls the provider chain (Places → Serp → fallback), writes results, and re-enqueues `SCORE` jobs. Cap concurrency with `asyncio.Semaphore(N)` so you never have more than N browsers/requests in flight.

**`ai_scoring_service.py`** — Gemini 2.5 Flash with JSON mode + validation + guardrails:

```python
from google import genai
from google.genai import types
import json
from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)

SCORING_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "tier": {"type": "string", "enum": ["HOT", "WARM", "COLD"]},
        "justification": {"type": "string"},
    },
    "required": ["score", "tier", "justification"],
}

def score_lead(product, lead, reviews) -> dict:
    prompt = f"""You are a B2B lead-scoring agent.
PRODUCT: {product['title']} — {product['description']}
VALUE PROP: {product.get('value_proposition','')}
LEAD: {lead['company_name']}
REVIEW COMPLAINTS: {reviews.get('pain_points_extracted', [])}
Return a fit score 0-100, a tier, and a one-line justification."""
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCORING_SCHEMA,     # structured output = no fence-stripping
            temperature=0.2,
        ),
    )
    data = json.loads(resp.text)
    data["score"] = max(0, min(100, int(data["score"])))   # clamp — never trust the model
    if data["tier"] not in {"HOT", "WARM", "COLD"}:
        data["tier"] = "COLD"
    return data
```

> Notes: use the current **`google-genai`** SDK (`from google import genai`), not the legacy `google.generativeai` from your v3 draft — verify exact param names against current docs. JSON mode + a `response_schema` removes the markdown-fence parsing fragility. Always clamp/validate — an LLM will occasionally return `score: 105` or a novel tier. Wrap the call in retry-with-backoff (2–3 attempts) for transient 429/500s, and on final failure mark the job `FAILED` rather than crashing the worker.

**`jobs/job_queue.py`** — enqueue + **atomic claim** (same pattern you'll reuse for leads in Phase 3):

```python
from sqlalchemy import text
import uuid, json

def enqueue(db, job_type, payload, run_after_sql="CURRENT_TIMESTAMP"):
    db.execute(text(
        f"INSERT INTO jobs (id, job_type, payload, run_after) "
        f"VALUES (:id, :t, :p, {run_after_sql})"),
        {"id": str(uuid.uuid4()), "t": job_type, "p": json.dumps(payload)})
    db.commit()

def claim_next(db, job_type):
    """Atomically claim one due job. Returns the row or None."""
    row = db.execute(text(
        "SELECT id FROM jobs WHERE status='PENDING' AND job_type=:t "
        "AND run_after <= CURRENT_TIMESTAMP ORDER BY run_after LIMIT 1"),
        {"t": job_type}).fetchone()
    if not row:
        return None
    claimed = db.execute(text(
        "UPDATE jobs SET status='CLAIMED', attempts=attempts+1, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=:id AND status='PENDING'"),
        {"id": row.id})
    db.commit()
    return row.id if claimed.rowcount > 0 else None   # lost the race → skip
```

**`jobs/worker.py`** — poll loop: `claim_next` → run handler → mark `DONE`, or on error either re-enqueue with `run_after = now + backoff` (if `attempts < max_attempts`) or set `DEAD`. This loop is where pacing lives; no `time.sleep()` for rate-limiting, only a short poll interval.

### 2.4 Verification (gate)

- `test_job_queue.py`: **concurrency test** — spawn 10 threads all calling `claim_next` on 1 due job; assert exactly one wins (proves atomic claim). Test `run_after` in the future is **not** claimed. Test retry increments `attempts` and flips to `DEAD` at `max_attempts`.
- `test_scoring_schema.py`: run scoring on a fixture lead; assert output validates against `SCORING_SCHEMA`, `0 <= score <= 100`, tier ∈ enum. Feed a deliberately malformed model response (mock) and assert it's coerced, not crashed.
- `test_scraper_memory.py`: call `fetch_rendered` in a loop 50× against a local test page; assert no lingering `chromium` processes afterward (`pgrep`/`psutil`) and RSS is flat between iterations. This is your **memory-leak gate** — if it fails, a `finally` isn't firing.

**✅ Phase 2 DoD:** atomic job claim proven under contention, scoring returns validated JSON, scraper loop leaves zero orphan browsers and flat memory, providers-first chain returns leads end-to-end.

---

# PHASE 3 — n8n, Atomic Lead Claiming & Multi-Channel Outreach

**Goal:** Paced, compliant, race-proof outreach. n8n owns scheduling/triggering; Flask owns state + enqueue; providers do the actual send.

### 3.1 Files created this phase

```
backend/services/lead_service.py
backend/services/outreach/{email_service.py, whatsapp_service.py, suppression.py}
backend/api/outreach.py
n8n/{docker-compose.yml, workflows/*}
backend/tests/{test_atomic_claim.py, test_suppression.py}
```

### 3.2 Schema addition — suppression & compliance

```sql
CREATE TABLE IF NOT EXISTS suppression_list (
    id           TEXT PRIMARY KEY,
    channel      TEXT NOT NULL,     -- EMAIL, WHATSAPP
    identifier   TEXT NOT NULL,     -- email address or phone
    reason       TEXT,              -- UNSUBSCRIBE, BOUNCE, STOP, MANUAL
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (channel, identifier)
);
```

### 3.3 Blueprints

**`lead_service.py`** — atomic claim (your v3 logic, hardened):

```python
from sqlalchemy import text

def claim_lead_for_outreach(db, lead_id) -> bool:
    res = db.execute(text(
        "UPDATE leads SET status='OUTREACHING', updated_at=CURRENT_TIMESTAMP "
        "WHERE id=:id AND status='SCORED'"), {"id": lead_id})
    db.commit()
    return res.rowcount > 0     # False = another worker already claimed it
```

Only dispatch if this returns `True`. On successful send → `OUTREACHED`; on hard failure → back to `SCORED` (or `REJECTED` after N tries) so it's not stuck in `OUTREACHING` forever. Add a **stale-claim sweeper** job: any lead in `OUTREACHING` older than X minutes gets reset — protects against a worker dying mid-dispatch.

**`outreach/suppression.py`** — checked **before every send, unconditionally**:

```python
from sqlalchemy import text

def is_suppressed(db, channel, identifier) -> bool:
    return db.execute(text(
        "SELECT 1 FROM suppression_list WHERE channel=:c AND identifier=:i LIMIT 1"),
        {"c": channel, "i": identifier}).fetchone() is not None
```

**`email_service.py`** — Resend send with required compliance headers:

```python
import httpx, uuid
from config import Config

def send_email(db, to_addr, subject, html_body):
    if is_suppressed(db, "EMAIL", to_addr):
        return {"status": "SKIPPED_SUPPRESSED"}
    unsub_url = f"https://yourdomain.com/u/{uuid.uuid4()}"   # store token→lead mapping
    headers = {
        "List-Unsubscribe": f"<{unsub_url}>, <mailto:unsub@yourdomain.com>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",   # RFC 8058
    }
    # html_body MUST include a visible unsubscribe link + your physical postal address
    resp = httpx.post("https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {Config.RESEND_API_KEY}"},
        json={"from": "you@yourdomain.com", "to": to_addr,
              "subject": subject, "html": html_body, "headers": headers})
    return {"status": "SENT" if resp.is_success else "FAILED"}
```

> **Deliverability is infrastructure, not code:** SPF, DKIM, and DMARC are DNS records on your sending domain; set them before sending a single email. Use a dedicated sending subdomain, warm it up gradually, and honor the one-click unsubscribe by inserting into `suppression_list` the instant it's hit. Check Resend's AUP on cold outreach before you commit to it as the sender.

**`whatsapp_service.py`** — official **WhatsApp Cloud API** (Meta Graph API), template message for first contact:

```python
import httpx
from config import Config

def send_whatsapp_template(db, to_phone, template_name, variables: list[str]):
    if is_suppressed(db, "WHATSAPP", to_phone):
        return {"status": "SKIPPED_SUPPRESSED"}
    url = f"https://graph.facebook.com/v20.0/{Config.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp", "to": to_phone, "type": "template",
        "template": {"name": template_name, "language": {"code": "en"},
                     "components": [{"type": "body",
                        "parameters": [{"type": "text", "text": v} for v in variables]}]},
    }
    resp = httpx.post(url, headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}"},
                      json=payload)
    return {"status": "SENT" if resp.is_success else "FAILED", "raw": resp.json()}
```

> First contact **must** use a pre-approved template; free-form messages are only allowed inside a 24-hour customer-service window after the lead replies. Treat "STOP"/opt-out replies as an immediate `suppression_list` insert. This is the path your enhancements section already chose — make it *the* path and drop Evolution/Baileys for first-touch (unofficial clients get numbers banned exactly on this cold-send pattern).

**n8n role (`n8n/`)** — n8n is the **scheduler and trigger**, not the brain:

- **Cron: daily discovery** (09:00) → HTTP node → `POST /api/v1/leads/discover` (Flask enqueues `DISCOVER` jobs).
- **Cron: outreach pacer** (e.g. hourly) → `POST /api/v1/outreach/tick` → Flask enqueues a paced batch (each job gets a staggered `run_after`), and the Phase-2 worker drains them respecting per-channel daily caps.
- Keep the actual provider send in Flask services (above) so compliance/suppression is enforced in one place; use n8n HTTP nodes to trigger, not to bypass the guardrails.
- `docker-compose.yml`: self-hosted n8n with a persistent volume + basic auth.

### 3.4 Verification (gate)

- `test_atomic_claim.py`: 10 concurrent threads claim the same `SCORED` lead → exactly one `True`. Stale-claim sweeper resets an old `OUTREACHING` lead.
- `test_suppression.py`: suppressed email/phone → `SKIPPED_SUPPRESSED`, no provider call. Hitting the unsubscribe endpoint inserts into `suppression_list` and a subsequent send is skipped.
- **Pacing test:** enqueue 40 email jobs; assert the worker respects the daily cap and staggered `run_after` (no burst).
- **Header test:** captured outgoing email contains `List-Unsubscribe` + `List-Unsubscribe-Post` and a visible unsubscribe link.
- WhatsApp: template send succeeds against a Meta test number; a "STOP" reply lands the number in suppression.

**✅ Phase 3 DoD:** no double-sends under contention, suppression enforced on every channel, one-click unsubscribe working, pacing caps honored, WhatsApp on official Cloud API.

---

# PHASE 4 — Inbound, Alerting, React Dashboard & Nightly Reporting

**Goal:** Robust inbound handling with idempotency and human-in-the-loop, a live React pipeline, and an automated EOD report.

### 4.1 Files created this phase

```
backend/services/intent_service.py, backend/services/reporting_service.py
backend/api/{inbound.py, reports.py}
frontend/** (Vite + Tailwind app)
n8n/workflows/{inbound_webhook, eod_report}
backend/tests/test_inbound_edge_cases.py
```

### 4.2 Schema addition — inbound idempotency

Add to `inbound_conversations`: `provider_message_id TEXT` with `UNIQUE (channel, provider_message_id)`. This is your dedup key — webhooks get **re-delivered**, and without this you double-process replies.

### 4.3 Blueprints

**`api/inbound.py`** — order of operations matters; guardrails run *before* the LLM:

```python
@bp.route("/api/v1/inbound/webhook", methods=["POST"])
def inbound_webhook():
    evt = request.get_json()
    msg_id = extract_provider_message_id(evt)
    text_body = extract_body(evt); sender = extract_sender(evt); channel = extract_channel(evt)

    # 1) IDEMPOTENCY: dedup on (channel, provider_message_id)
    if already_processed(db, channel, msg_id):
        return jsonify({"status": "duplicate_ignored"}), 200

    # 2) HARD RULES before any AI:
    if is_optout(text_body):                     # STOP / unsubscribe / "remove me"
        add_to_suppression(db, channel, sender, "STOP")
        record_inbound(db, ..., intent="NOT_INTERESTED")
        return jsonify({"status": "suppressed"}), 200
    if is_autoreply(evt, text_body):             # OOO / vacation auto-responders
        record_inbound(db, ..., intent="SPAM")   # never score as INTERESTED
        return jsonify({"status": "autoreply_ignored"}), 200

    # 3) LLM intent classification (with confidence)
    result = classify_intent(text_body)          # intent_service.py
    record_inbound(db, ..., intent=result["intent"], ai_suggested_response=result["reply"])

    # 4) ESCALATION / human-in-the-loop
    if result["intent"] in {"DEMO_REQUESTED", "INTERESTED"} or result["confidence"] < 0.6 \
       or looks_legal_or_angry(text_body):
        fire_high_intent_alert(db, ...)          # notify human, DO NOT auto-reply
    else:
        # only low-risk, high-confidence replies may auto-respond
        enqueue_auto_reply(db, ...)
    return jsonify({"status": "processed"}), 200
```

> The edge cases that break naive inbound handlers, all handled above: **re-delivered webhooks** (dedup), **out-of-office autoreplies** (never "interested"), **STOP/unsubscribe** (suppress first, ahead of AI), **angry/legal replies** (escalate, don't auto-respond), **low-confidence** classifications (route to human), and **LLM over-promising** (HOT leads go to a human, the model never closes). `intent_service.classify_intent` reuses the Phase-2 Gemini pattern with a JSON schema returning `{intent, confidence, reply}`; clamp confidence and default to escalation on parse failure.

**High-intent alerting** — `fire_high_intent_alert` posts to an n8n webhook → Slack/email/WhatsApp to the human rep, including lead, score, and the inbound message. Keep it idempotent (don't alert twice for the same message).

**`reporting_service.py` + nightly report** — aggregate the day's metrics (discovered, scored by tier, outreached per channel, replies, high-intent count) into `daily_reports.metrics_summary`, generate a short executive summary (Gemini, optional), and let an **n8n cron (23:50)** call `POST /api/v1/reports/generate` then email it.

**React dashboard (`frontend/`)** — Vite + React + Tailwind:

- `api/client.js`: thin fetch wrapper to `/api/v1`.
- `ProductForm.jsx`: dynamic product registration (title, description, value prop, keywords, pain-point map) — no code changes needed to add products.
- `LeadPipeline.jsx`: kanban columns by `status` (DISCOVERED → … → CONVERTED); `LeadCard.jsx` shows score/tier/justification.
- `AlertsPanel.jsx`: polls (or subscribes to) high-intent alerts; a rep can claim/respond.
- Keep it read-mostly in v1; the AI owns state transitions, humans act on HOT leads.

### 4.4 Verification (gate)

- `test_inbound_edge_cases.py`: duplicate `provider_message_id` → `duplicate_ignored` (processed once). "STOP" → suppressed + no LLM call. An OOO autoreply → not classified INTERESTED. A simulated angry/legal reply → escalated, no auto-reply. Low-confidence result → escalated.
- Alerting: a `DEMO_REQUESTED` reply fires exactly one alert to the human channel.
- Dashboard: create a product in the UI → it appears via API; leads render in the correct pipeline column; HOT leads surface in AlertsPanel.
- Nightly report: trigger `generate` → `daily_reports` row written, email delivered with correct counts.

**✅ Phase 4 DoD:** inbound is idempotent and guardrailed, no auto-reply on high-intent/uncertain/hostile messages, dashboard reflects live pipeline, EOD report generates and sends.

---

## 5. Cross-cutting (apply across all phases)

- **Secrets:** only in `.env` / a secrets manager; `.env` in `.gitignore`; `.env.example` committed with blank values.
- **Observability:** structured JSON logging with a request/job id; count sends, failures, suppression hits, claim contention; alert on `DEAD` jobs piling up and on scraper OOM.
- **DB hygiene:** run `PRAGMA wal_checkpoint(TRUNCATE)` on a timer (a long-lived n8n read connection can pin the WAL and let it grow); keep write transactions short and **never hold a write txn open across an LLM or network call**.
- **Process topology:** run Flask (API) and the scraper/job worker as **separate processes**. If you scale Flask behind gunicorn, keep the job worker as a single dedicated process so pacing/caps stay consistent (multiple workers = multiple executors = inconsistent counters).
- **Model note:** `gemini-2.5-flash` is a valid current choice; the Flash lineup moves fast, so pin the exact model string from Google's current model page and keep it in config so a swap is one line.

## 6. Phase-gate checklist (tape this to the wall)

| Gate | Must be green before next phase |
| :-- | :-- |
| **P1** | Pragmas live per-connection · FK cascade works · Product/Lead CRUD · secrets in `.env` |
| **P2** | Atomic job claim under contention · validated scoring JSON · zero orphan browsers / flat RSS |
| **P3** | No double-send · suppression on every channel · one-click unsubscribe · pacing caps · official WhatsApp |
| **P4** | Idempotent inbound · guardrails before LLM · human-in-loop on HOT/uncertain/hostile · dashboard live · EOD report |

Build in order. Each gate exists because skipping it produces a bug that's invisible in dev and expensive in production.
