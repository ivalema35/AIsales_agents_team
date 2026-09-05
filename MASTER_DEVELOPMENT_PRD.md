# MASTER_DEVELOPMENT_PRD.md
## Autonomous AI Sales Operating System — Unified Build Specification

**Merges:** Technical PRD v3 (Execution Infrastructure) + Intelligence PRD v2 (Cognitive Brain Layer)
**Audience:** A software engineer or a coding agent (Claude Code / Cursor) building production code section by section.
**Build model:** 19 phases, each gated by a Definition-of-Done (DoD) test suite. Do not advance until the gate is green. Phases 1–5 are the original build (§5); Phases 6–10 (§5A) were added 2026-08-19 from real post-launch requirements; Phases 11–15 (§5B) were added 2026-08-22 from a second round of the same, after Phases 6–9 were live on real leads; Phases 16–19 (§5C) were added 2026-09-01 from a strategic-direction discussion (the operator's boss reviewed the live system and called it "automation, not AI") — see `discussion.md` for the full raw conversation this section formalizes.

---

## 0. How to read this document

- **Sections 1–4** are *reference*: architecture, file tree, the complete data layer, and the cognitive contracts (agents, decision thresholds, memory). Implement against them; don't re-derive them per phase.
- **Section 5** is the *build order*: Phases 1→5, each step listing (a) files to create, (b) a focused code blueprint showing the non-obvious logic and its failure handling, and (c) the DoD tests that open the gate.
- **Section 5A** is the *add-on build order*: Phases 6→10, added 2026-08-19 from real post-launch requirements plus every previously-deferred item. It follows the same step + DoD-gate structure as §5. Read §5A.0 before reordering anything there — the sequence encodes real dependencies, and it carries one open decision about Phase 5's position that needs the user's confirmation.
- **Section 5B** is the *second add-on build order*: Phases 11→15, added 2026-08-22 after Phases 6–9 shipped and ran on real leads. Where §5A answered "I can't see, steer, or measure the system", §5B answers a later problem — the message reads competently but not persuasively, can't be answered in one click, repeats itself across touches, drifts between channels, and often reaches someone who can't judge the pitch. Read §5B.0 before reordering.
- **Section 5C** is the *third add-on build order*: Phases 16→19, added 2026-09-01 from a different kind of requirement — not a missing feature but a missing **layer**. §5A and §5B both made the existing execution pipeline see better and speak better; §5C sits a new AI Sales Manager mind above that pipeline — a persuasive, knowledge-base-grounded conversation engine, a campaign/calendar grouping layer, a daily AI-plans/human-reviews loop, and a weekly strategy-reflection engine — without rewriting or replacing anything Phases 1–15 already proved. Read §5C.0 before reordering; it also records where Chapter 18's cognitive contract (Intelligence PRD) and CRM_UI_UX_PLAN's §2C diverge from `discussion.md`'s raw brainstorm and why.
- **Section 6** is the *agent prompt library* — copy-pasteable Python string constants.
- **Section 7** is the *command cheat sheet*.
- **Section 8** is the *Executive Business Layer* (Chapter 15 / AI-BOS): the governance layer sitting above Cognitive + Execution — revenue/CAC ceilings, dual sales-mode routing, capacity throttling, client lifecycle, decision simulation, cross-agent governance, and self-evolution boundaries.
- **Section 9** covers cross-cutting concerns and the full phase-gate checklist (P1–P19).
- Code blocks are **blueprints**: they carry the critical logic (routing, atomic claims, cleanup, validation) verbatim and leave routine bodies (field mapping, selectors, styling) for you to fill.

**Three-layer contract:** the Executive layer *governs* (sets revenue/CAC ceilings, capacity throttles, sales-mode routing, and can pause or veto any campaign — Chapter 15 / §8); the Cognitive layer *decides* (emits structured intent + a confidence score); the Execution layer *acts* (Flask/SQLite/Playwright/an in-process discovery scheduler). Every autonomous decision passes the Decision Engine (§4.2) before the Execution layer touches a channel, and every Executive-level ceiling or override passes the Cross-Agent Governance Hierarchy (§8.7) first.

**Amendment (2026-08-13, implemented):** §3.5's original n8n-based scheduler design was superseded during Phase 3 build — see the project's `tracker.md` §A.2 for full rationale. n8n is dropped entirely; scheduling (autonomous discovery targeting + outreach pacing) now runs as a dedicated in-process Python worker, `jobs/discovery_scheduler.py`. This also activates §6's `ICP_STRATEGY_AGENT_SYSTEM_PROMPT` / `agents/icp_strategy_agent.py`, originally specified but never wired into any build step — it is now live starting Phase 3. Every mention of n8n below describes the ORIGINAL design; treat `jobs/discovery_scheduler.py` as its replacement wherever n8n is named as the scheduler/trigger.

---

## 1. System overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                  ENTERPRISE EXECUTIVE LAYER (Chapter 15 / §8)                   │
│  Executive Business Brain (Revenue/CAC) · Dual Sales Mode Engine · Capacity &    │
│  Resource Intelligence · Market & Competitor Intelligence · Client Lifecycle     │
│  (LTV/Renewals) · Decision Simulation · Cross-Agent Governance · Self-Evolution  │
│  Boundaries                                                                     │
└───────────────────────────────────┬────────────────────────────────────────────┘
      budget ceilings · capacity throttles · sales-mode routing · governance vetoes
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         COGNITIVE BRAIN LAYER (PRD v2)                          │
│  CEO · Sales Manager · ICP/Strategy · Review Analyst · Scoring · Outreach ·     │
│  Inbound · Quality Controller (veto) · Learning/Memory Manager                  │
│  Decision Engine (confidence×risk) · Adaptability Triggers · A/B Bandit ·        │
│  4-Tier Memory                                                                  │
└───────────────────────────────────┬────────────────────────────────────────────┘
                    structured JSON intent + confidence
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       EXECUTION INFRASTRUCTURE (PRD v3)                         │
│  Flask REST API · SQLite WAL + pragma listener · durable jobs queue ·           │
│  async Playwright worker · Gemini 2.5 Flash · Resend (email) ·                   │
│  WhatsApp Cloud API · in-process discovery scheduler · React/Vite/Tailwind dashboard │
└──────────────────────────────────────────────────────────────────────────────┘
```

**The Executive layer never touches a channel or a lead directly** — it only sets ceilings, thresholds, and routing rules that the Cognitive layer must operate within (§8). **Cognition never sends anything directly either.** An agent proposes an action with a confidence score → the Decision Engine routes it (EXECUTE / QC_REVIEW / HUMAN_ESCALATION / IMMEDIATE_EXECUTE) → only then does an Execution-layer service dispatch. Every hop is logged to `agent_events` for audit, self-evaluation, and KPIs.

**Five operating principles (enforced in every prompt, §6):** value-first over pitch-spam; contextual authenticity (no AI-buzzwords); radical truthfulness / zero hallucination; adaptability within guardrails; and immediate, permanent respect for opt-out signals ahead of any other processing.

---

## 2. Complete project file tree

```
ai-sales-os/
├── backend/
│   ├── app.py                          # Flask app factory + entrypoint
│   ├── config.py                       # env-driven config (thresholds, keys)
│   ├── logging_config.py               # structured JSON logging
│   ├── requirements.txt
│   ├── .env.example
│   ├── migrate.py                      # DB bootstrap / migration runner
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_config.py                # engine, SessionLocal, PRAGMA listener
│   │   ├── models.py                   # SQLAlchemy ORM (all 16 tables)
│   │   └── schema.sql                  # full DDL (source of truth)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── products.py                 # /api/v1/products
│   │   ├── leads.py                    # /api/v1/leads
│   │   ├── scoring.py                  # /api/v1/score
│   │   ├── outreach.py                 # /api/v1/outreach (enqueue only)
│   │   ├── inbound.py                  # /api/v1/inbound/webhook
│   │   ├── alerts.py                   # /api/v1/alerts (human queue)
│   │   ├── reports.py                  # /api/v1/reports
│   │   ├── executive.py                # /api/v1/executive (budget, what-if sim) (§8.6)
│   │   └── lifecycle.py                # /api/v1/lifecycle (onboarding, renewals) (§8.5)
│   ├── cognition/
│   │   ├── __init__.py
│   │   ├── decision_engine.py          # confidence×risk routing (§4.2)
│   │   ├── agent_events.py             # audit log helper
│   │   ├── prompts.py                  # all agent system prompts (§6)
│   │   ├── llm_client.py               # Gemini wrapper: JSON mode + validation
│   │   ├── memory.py                   # 4-tier memory read/write helpers
│   │   ├── adaptability.py             # self-adaptation trigger matrix (§4.3)
│   │   ├── bandit.py                   # A/B variant allocation (§4.4)
│   │   ├── dual_sales_engine.py        # SaaS vs Custom-Dev routing (§8.2)
│   │   └── capacity_intelligence.py    # capacity throttle + CAC ceiling (§8.1/§8.3)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── icp_strategy_agent.py
│   │   ├── review_analyst_agent.py
│   │   ├── scoring_agent.py
│   │   ├── outreach_agent.py
│   │   ├── inbound_agent.py
│   │   ├── quality_controller.py       # veto gate before every send
│   │   └── lifecycle_agent.py          # onboarding/renewal/upsell intelligence (§8.5)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_service.py             # atomic claim + state transitions
│   │   ├── reporting_service.py
│   │   ├── data_acquisition/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # LeadSourceProvider interface
│   │   │   ├── places_provider.py      # Google Places API — DEFAULT
│   │   │   ├── serp_provider.py        # SerpAPI/Serper — DEFAULT
│   │   │   ├── b2b_provider.py         # Apollo/PDL/Hunter enrichment
│   │   │   └── playwright_fallback.py  # generic render+extract (no evasion)
│   │   └── outreach/
│   │       ├── __init__.py
│   │       ├── email_service.py        # Resend + RFC 8058 headers
│   │       ├── whatsapp_service.py     # WhatsApp Cloud API (official)
│   │       └── suppression.py          # opt-out enforcement
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── job_queue.py                # enqueue + atomic claim (run_after)
│   │   ├── worker.py                   # background poller (pacing, retries)
│   │   └── discovery_scheduler.py      # autonomous discovery + outreach-pacing cron -- replaces n8n (§3.5 amendment)
│   ├── scraper_worker/
│   │   ├── __init__.py
│   │   └── async_runner.py             # dedicated asyncio process
│   └── tests/
│       ├── conftest.py
│       ├── test_db_pragmas.py
│       ├── test_atomic_claim.py
│       ├── test_job_queue.py
│       ├── test_decision_engine.py
│       ├── test_scoring_schema.py
│       ├── test_scraper_memory.py
│       ├── test_qc_gate.py
│       ├── test_suppression.py
│       ├── test_inbound_edge_cases.py
│       ├── test_dual_sales_routing.py
│       ├── test_capacity_throttle.py
│       ├── test_lifecycle_renewal.py
│       ├── test_governance_hierarchy.py
│       └── test_self_evolution_boundaries.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/client.js
│       ├── pages/{Dashboard.jsx, Products.jsx, ExecutiveControl.jsx}
│       └── components/{ProductForm.jsx, PipelineKanban.jsx, LeadCard.jsx, AlertsPanel.jsx, CapacityMeter.jsx}
└── README.md
```

*(The `n8n/` folder in the original design — `docker-compose.yml` + `workflows/{morning_discovery,hourly_outreach_pacer,adaptability_sweep,inbound_relay,eod_report}.json` — is dropped per the §3.5 amendment above. `jobs/discovery_scheduler.py` replaces the first three; Phase 4/5's remaining cron-shaped items (`eod_report`, and `inbound_relay` if still needed once `api/inbound.py`'s own webhook receiver is built in Step 4.1) follow the same in-process-scheduler pattern when their phase is reached, rather than reviving n8n.)*

**Table count reconciliation:** the 11 named tables + 3 intelligence-layer tables (`agent_events`, `campaign_variants`, `knowledge_memory`) + 2 executive-layer tables (`team_capacity`, `client_lifecycle`) + 2 discovery-scheduler tables (`product_strategies`, `discovery_runs` — §3.5 amendment) = **18 total**. The intelligence tables make the cognitive layer auditable, adaptive, and able to remember; the executive tables make it capacity-aware and post-sale-aware; the discovery-scheduler tables make audience targeting autonomous and auditable. All are flagged in §3.1.

---

## 3. Data layer

### 3.1 Complete SQLite DDL (`database/schema.sql`)

> **Addendum (2026-08-19, extended 2026-08-22):** this section's prose says "16 tables", but the **live
> `schema.sql` now has 28**. `product_strategies` (17), `discovery_runs` (18) and `system_settings` (19)
> were added during Phases 3–4 after this text was written. Phases 6–10 (§5A) added Tables **20–28** —
> nine, not the eight §5A.1 projected, because `social_message_queue` (27) turned out to need its own
> state while building Step 10.3(a) and `call_logs` moved to 28. Phases 11–15 (§5B) add Tables **29–31
> (total 31)** plus four columns on existing tables; each is specified in the §5B step that introduces
> it, and the full list is tabulated in §5B.1. Two schema facts worth carrying forward when reading this
> DDL: `campaign_variants` (Table 13) exists here but has never been written to — Phase 9 Step 9.1 is
> what finally wires it; and `leads` holds exactly **one** contact person, which is why Phase 7
> introduces `lead_contacts` rather than widening this table.

```sql
PRAGMA foreign_keys = ON;

-- 1. PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    id                   TEXT PRIMARY KEY,
    title                TEXT NOT NULL,
    description          TEXT NOT NULL,
    target_keywords      TEXT DEFAULT '[]',   -- JSON array
    value_proposition    TEXT,
    pain_point_mappings  TEXT DEFAULT '{}',   -- JSON object
    priority             INTEGER DEFAULT 1,
    is_active            INTEGER DEFAULT 1,
    target_regions       TEXT DEFAULT '[]',   -- JSON array, e.g. ["Ahmedabad","Surat"] (§3.5 amendment)
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LEADS
CREATE TABLE IF NOT EXISTS leads (
    id                   TEXT PRIMARY KEY,
    product_id           TEXT NOT NULL,
    company_name         TEXT NOT NULL,
    website_url          TEXT,
    primary_email        TEXT,
    primary_phone        TEXT,
    whatsapp_number      TEXT,
    contact_person_name  TEXT,
    contact_person_role  TEXT,
    status               TEXT DEFAULT 'DISCOVERED',
      -- DISCOVERED, ENRICHED, REVIEWED, SCORED, OUTREACHING, OUTREACHED,
      -- ENGAGED, HOT_LEAD, CONVERTED, REJECTED
    source               TEXT,
    region_location      TEXT,
    sales_route          TEXT DEFAULT 'UNASSIGNED',
      -- UNASSIGNED, SAAS_PRODUCT, CUSTOM_DEV — set by dual_sales_engine.py (§8.2)
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 3. FIRMOGRAPHICS
CREATE TABLE IF NOT EXISTS lead_firmographics (
    id                     TEXT PRIMARY KEY,
    lead_id                TEXT UNIQUE NOT NULL,
    linkedin_url           TEXT,
    company_size_range     TEXT,
    industry               TEXT,
    remote_work_indicators TEXT DEFAULT '{}',
    tech_stack             TEXT DEFAULT '[]',
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- 4. REVIEW INSIGHTS
CREATE TABLE IF NOT EXISTS lead_review_insights (
    id                    TEXT PRIMARY KEY,
    lead_id               TEXT NOT NULL,
    review_source         TEXT DEFAULT 'GOOGLE_REVIEWS',
    average_rating        REAL,
    total_reviews_count   INTEGER,
    pain_points_extracted TEXT DEFAULT '[]',   -- JSON array of weakness codes
    sentiment_score       REAL,
    raw_review_snippets   TEXT DEFAULT '[]',
    analyzed_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- 5. LEAD SCORES
CREATE TABLE IF NOT EXISTS lead_scores (
    id                 TEXT PRIMARY KEY,
    lead_id            TEXT UNIQUE NOT NULL,
    score              INTEGER NOT NULL,      -- 0..100
    tier               TEXT NOT NULL,         -- HOT, WARM, COLD
    confidence         REAL DEFAULT 0.0,      -- Decision Engine input
    scoring_breakdown  TEXT DEFAULT '{}',
    justification      TEXT,
    evaluated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- 6. OUTREACH CAMPAIGNS  (Campaign Memory, tier 2)
CREATE TABLE IF NOT EXISTS outreach_campaigns (
    id                 TEXT PRIMARY KEY,
    product_id         TEXT NOT NULL,
    name               TEXT NOT NULL,
    icp_rules          TEXT DEFAULT '{}',     -- JSON: size, roles, verticals
    channel_config     TEXT DEFAULT '{}',     -- JSON: daily caps, delays
    status             TEXT DEFAULT 'ACTIVE', -- ACTIVE, PAUSED, RETIRED
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 7. OUTREACH LOGS
CREATE TABLE IF NOT EXISTS outreach_logs (
    id               TEXT PRIMARY KEY,
    lead_id          TEXT NOT NULL,
    campaign_id      TEXT,
    variant_id       TEXT,
    channel          TEXT NOT NULL,           -- EMAIL, CONTACT_FORM, WHATSAPP
    message_subject  TEXT,
    message_body     TEXT NOT NULL,
    status           TEXT NOT NULL,           -- SENT, FAILED, DELIVERED, BOUNCED
    sent_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES outreach_campaigns(id) ON DELETE SET NULL
);

-- 8. INBOUND CONVERSATIONS
CREATE TABLE IF NOT EXISTS inbound_conversations (
    id                   TEXT PRIMARY KEY,
    lead_id              TEXT NOT NULL,
    channel              TEXT NOT NULL,        -- EMAIL, WHATSAPP
    provider_message_id  TEXT,                 -- idempotency key
    sender_type          TEXT NOT NULL,        -- LEAD, AI_AGENT, HUMAN_REP
    message_content      TEXT NOT NULL,
    intent_detected      TEXT,                 -- INTERESTED, DEMO_REQUESTED, OBJECTION, STOP, AUTO_REPLY
    confidence           REAL,
    ai_suggested_response TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
    UNIQUE (channel, provider_message_id)      -- dedup re-delivered webhooks
);

-- 9. SUPPRESSION LIST
CREATE TABLE IF NOT EXISTS suppression_list (
    id           TEXT PRIMARY KEY,
    channel      TEXT NOT NULL,                -- EMAIL, WHATSAPP
    identifier   TEXT NOT NULL,                -- email or phone
    reason       TEXT,                         -- UNSUBSCRIBE, STOP, BOUNCE, MANUAL
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (channel, identifier)
);

-- 10. JOBS  (durable queue, non-blocking pacing)
CREATE TABLE IF NOT EXISTS jobs (
    id            TEXT PRIMARY KEY,
    job_type      TEXT NOT NULL,               -- DISCOVER, ENRICH, REVIEW, SCORE,
                                               -- OUTREACH_EMAIL, OUTREACH_WA, ADAPT
    payload       TEXT NOT NULL,               -- JSON
    status        TEXT DEFAULT 'PENDING',      -- PENDING, CLAIMED, DONE, FAILED, DEAD
    run_after     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attempts      INTEGER DEFAULT 0,
    max_attempts  INTEGER DEFAULT 3,
    last_error    TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. DAILY REPORTS
CREATE TABLE IF NOT EXISTS daily_reports (
    id                     TEXT PRIMARY KEY,
    report_date            TEXT UNIQUE NOT NULL,
    metrics_summary        TEXT DEFAULT '{}',
    executive_summary_text TEXT,
    generated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. AGENT EVENTS  (intelligence add: decision audit + self-eval + KPIs)
CREATE TABLE IF NOT EXISTS agent_events (
    id            TEXT PRIMARY KEY,
    agent         TEXT NOT NULL,               -- ICP, REVIEW, SCORING, OUTREACH, INBOUND, QC
    lead_id       TEXT,
    action_type   TEXT NOT NULL,               -- SCORE, DRAFT_OUTREACH, CLASSIFY_INTENT...
    confidence    REAL,
    risk_level    TEXT,                         -- LOW, MEDIUM, HIGH, CRITICAL
    routed_to     TEXT,                         -- EXECUTE, QC_REVIEW, HUMAN_ESCALATION, IMMEDIATE
    payload       TEXT DEFAULT '{}',
    outcome       TEXT,                         -- APPROVED, REJECTED, SENT, ESCALATED...
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. CAMPAIGN VARIANTS  (intelligence add: A/B multi-armed bandit)
CREATE TABLE IF NOT EXISTS campaign_variants (
    id                TEXT PRIMARY KEY,
    campaign_id       TEXT NOT NULL,
    label             TEXT NOT NULL,           -- 'A', 'B', ...
    hook_type         TEXT,                    -- PAIN_POINT, PROOF, TIME_SAVINGS
    subject_template  TEXT,
    body_template     TEXT,
    sends             INTEGER DEFAULT 0,
    replies           INTEGER DEFAULT 0,
    conversions       INTEGER DEFAULT 0,
    allocation_weight REAL DEFAULT 0.5,
    status            TEXT DEFAULT 'ACTIVE',   -- ACTIVE, RETIRED
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES outreach_campaigns(id) ON DELETE CASCADE
);

-- 14. KNOWLEDGE MEMORY  (intelligence add: historical / tier 4)
CREATE TABLE IF NOT EXISTS knowledge_memory (
    id          TEXT PRIMARY KEY,
    category    TEXT NOT NULL,                 -- OBJECTION_SCRIPT, FAQ, COMPETITOR, WINNING_HOOK
    key         TEXT,                          -- e.g. objection type / industry
    content     TEXT NOT NULL,                 -- JSON or text
    embedding   TEXT,                          -- optional: JSON float array
    score       REAL DEFAULT 0.0,              -- performance weighting
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. TEAM CAPACITY  (executive add: delivery/onboarding bandwidth — §8.3)
CREATE TABLE IF NOT EXISTS team_capacity (
    id                    TEXT PRIMARY KEY,
    team_name             TEXT NOT NULL,        -- 'ONBOARDING', 'DEV_SERVICES'
    total_slots           INTEGER NOT NULL DEFAULT 10,
    occupied_slots        INTEGER NOT NULL DEFAULT 0,
    max_utilization_pct   INTEGER DEFAULT 90,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. CLIENT LIFECYCLE  (executive add: post-sale LTV / renewals / upsell — §8.5)
CREATE TABLE IF NOT EXISTS client_lifecycle (
    id                    TEXT PRIMARY KEY,
    lead_id               TEXT UNIQUE NOT NULL,
    onboarding_status     TEXT DEFAULT 'NOT_STARTED',
    current_mrr           REAL DEFAULT 0.0,
    contract_start_date   DATE,
    contract_end_date     DATE,
    upsell_opportunity    TEXT,
    referral_requested    INTEGER DEFAULT 0,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- 17. PRODUCT STRATEGIES  (§3.5 amendment: ICP Strategy Agent output, versioned not overwritten)
CREATE TABLE IF NOT EXISTS product_strategies (
    id                 TEXT PRIMARY KEY,
    product_id         TEXT NOT NULL,
    icp                TEXT DEFAULT '{}',     -- JSON: {company_size, roles, verticals}
    search_queries     TEXT DEFAULT '[]',     -- JSON array
    target_complaints  TEXT DEFAULT '[]',     -- JSON array
    source             TEXT NOT NULL,         -- AI_GENERATED, HUMAN_ADDED
    status             TEXT DEFAULT 'ACTIVE', -- ACTIVE, SUPERSEDED
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 18. DISCOVERY RUNS  (§3.5 amendment: per product+query+region cooldown tracking for the scheduler)
CREATE TABLE IF NOT EXISTS discovery_runs (
    id            TEXT PRIMARY KEY,
    product_id    TEXT NOT NULL,
    query         TEXT NOT NULL,
    region        TEXT NOT NULL,
    last_run_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, query, region),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_leads_product_status  ON leads (product_id, status);
CREATE INDEX IF NOT EXISTS idx_lead_scores_tier      ON lead_scores (tier, score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_due              ON jobs (status, job_type, run_after);
CREATE INDEX IF NOT EXISTS idx_agent_events_lead     ON agent_events (lead_id, created_at);
CREATE INDEX IF NOT EXISTS idx_variants_campaign     ON campaign_variants (campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_knowledge_cat_key     ON knowledge_memory (category, key);
CREATE INDEX IF NOT EXISTS idx_leads_sales_route     ON leads (sales_route);
CREATE INDEX IF NOT EXISTS idx_team_capacity_name    ON team_capacity (team_name);
CREATE INDEX IF NOT EXISTS idx_client_lifecycle_end  ON client_lifecycle (contract_end_date);
CREATE INDEX IF NOT EXISTS idx_product_strategies    ON product_strategies (product_id, status);
CREATE INDEX IF NOT EXISTS idx_discovery_runs_lookup  ON discovery_runs (product_id, last_run_at);
```

### 3.2 PRAGMA connection listener (`database/db_config.py`)

```python
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

Base = declarative_base()
engine = create_engine(
    f"sqlite:///{Config.DB_PATH}",
    connect_args={"check_same_thread": False},   # sessions opened per worker thread
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

> `foreign_keys` and `busy_timeout` are per-connection — set anywhere else and cascades silently no-op and you hit spurious "database is locked". Never hold a write transaction open across an LLM or network call; that manufactures the lock storms WAL is meant to avoid.

### 3.3 Migration bootstrap (`migrate.py`)

```python
from database.db_config import engine
def run():
    with engine.begin() as conn:
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            conn.connection.executescript(f.read())
    print("Schema applied.")
if __name__ == "__main__":
    run()
```

---

## 4. Cognitive architecture reference

### 4.1 Agent roster & authority

| Agent | Decides | Autonomy | Escalates when |
| :-- | :-- | :-- | :-- |
| **CEO** | Targets, pause/resume campaigns, global ICP | High | Conversion <1% for 3 days, or global API outage |
| **Sales Manager** | Daily volumes, batch assignment, retries | Operational | Queue starvation / repeated failures |
| **ICP & Strategy** | ICP definition, search queries | Advisory → Manager | — |
| **Review Analyst** | Extract weakness codes from reviews | Autonomous (≥0.70) | Low confidence |
| **Scoring** | Fit score 0–100 + tier + confidence | Autonomous (≥0.70) | Low confidence |
| **Outreach** | Draft personalized copy (A/B) | Draft only → QC | Always via QC before send |
| **Inbound** | Classify intent, draft reply | Autonomous reply (≥0.85) | Demo/pricing/hostile/low-conf |
| **Quality Controller** | Approve/reject any outbound | **Veto power** | Repeated rejects → human |
| **Learning/Memory** | A/B promotion, KB updates | Autonomous | — |
| **Lifecycle** (§8.5) | Onboarding milestones, renewal reminders, upsell triggers | Autonomous (≥0.70) | Contract change, churn risk, or any discount/pricing request |

The full cross-agent precedence order — including the new Capacity Intelligence and Executive Business Brain roles — is formalized in the **Cross-Agent Governance Hierarchy** (§8.7); QC's veto stays absolute regardless of rank.

### 4.2 Decision Engine (`cognition/decision_engine.py`)

The single gate every autonomous action passes through. Thresholds come straight from PRD v2's confidence/risk matrix.

```python
# config.py thresholds (tune here, not in code paths)
DECISION_THRESHOLDS = {
    "SCORING":          {"min": 0.70, "route_below": "HUMAN"},
    "STANDARD_OUTREACH":{"min": 0.85, "review": "QC"},
    "INBOUND_REPLY":    {"min": 0.85, "route_below": "HUMAN"},
    "MEETING_BOOKING":  {"min": 0.90, "alert_human": True},
    "CUSTOM_PRICING":   {"min": 0.95, "force": "HUMAN"},   # always human
    "OPT_OUT":          {"force": "IMMEDIATE"},            # 100% rule
}

def route_action(category: str, confidence: float, is_high_risk: bool = False) -> str:
    """Returns EXECUTE | QC_REVIEW | HUMAN_ESCALATION | IMMEDIATE_EXECUTE."""
    if category == "OPT_OUT":
        return "IMMEDIATE_EXECUTE"                 # suppress before anything else
    if category == "CUSTOM_PRICING" or is_high_risk:
        return "HUMAN_ESCALATION"
    if confidence < 0.70:
        return "HUMAN_ESCALATION"
    if category in ("STANDARD_OUTREACH",) or confidence < 0.85:
        return "QC_REVIEW"
    return "EXECUTE"
```

Every call logs an `agent_events` row: `{agent, action_type, confidence, risk_level, routed_to}`. That table is simultaneously the audit trail, the self-evaluation record, and the KPI source.

### 4.3 Adaptability triggers (`cognition/adaptability.py`)

A scheduled sweep reads campaign KPIs and enqueues corrective jobs — no human in the loop for these mechanical fixes.

| Signal | Autonomous response |
| :-- | :-- |
| Open rate < 15% | Enqueue "generate 3 new subject variants"; rotate sending subdomain |
| Reply rate < 2% over 200 sends | Narrow ICP headcount filter; shift hook Price→Time-Savings |
| Spam complaints > 0.1% | Pause campaign; re-template to <75-word plain text; re-verify unsubscribe |
| Bounce rate > 3% | Tighten email enrichment/validation waterfall |
| Frequent "existing vendor" objections | Inbound shifts to migration/cost-reduction script |

```python
def evaluate_campaign(db, campaign_id, kpis: dict):
    actions = []
    if kpis["open_rate"] < 0.15:
        actions.append(("REGEN_SUBJECTS", {"n": 3}))
    if kpis["sends"] >= 200 and kpis["reply_rate"] < 0.02:
        actions.append(("NARROW_ICP", {"hook": "TIME_SAVINGS"}))
    if kpis["spam_rate"] > 0.001:
        actions.append(("PAUSE_AND_RETEMPLATE", {}))
    for kind, params in actions:
        enqueue(db, "ADAPT", {"campaign_id": campaign_id, "action": kind, **params})
    return actions
```

### 4.4 A/B multi-armed bandit (`cognition/bandit.py`)

```python
def allocate(variants: list[dict], min_sends=100, explore=0.2) -> dict:
    """Pick a variant. Explore until each has min_sends, then exploit the best CR."""
    import random
    fresh = [v for v in variants if v["sends"] < min_sends and v["status"] == "ACTIVE"]
    if fresh:
        return random.choice(fresh)                      # exploration phase
    active = [v for v in variants if v["status"] == "ACTIVE"]
    if random.random() < explore:
        return random.choice(active)                     # epsilon explore
    def cr(v): return v["conversions"] / max(v["sends"], 1)
    return max(active, key=cr)                            # exploit winner
```

Learning agent promotes the winner to ~80% weight and retires losers, then spins a fresh experiment (per PRD v2 §6.1).

### 4.5 Multi-tiered memory mapping (`cognition/memory.py`)

| Tier | Store | Purpose |
| :-- | :-- | :-- |
| Working | in-process dict / request scope | active LLM execution context |
| Campaign | `outreach_campaigns` + `campaign_variants` | ICP rules, live A/B state, caps |
| Lead | `leads` + `lead_*` + `inbound_conversations` | full interaction history per lead |
| Historical | `knowledge_memory` (JSON now, embeddings later) | winning objection scripts, FAQs, competitor matrices |
| Post-Sale | `client_lifecycle` (§8.5) | onboarding status, MRR, renewal/upsell state per converted lead |

Retrieval helper example — pull the best-performing objection script for the Inbound agent's context (semantic match optional; keyword/category match is fine for v1):

```python
def recall_objection_scripts(db, objection_type, limit=3):
    rows = db.execute(text(
        "SELECT content FROM knowledge_memory WHERE category='OBJECTION_SCRIPT' "
        "AND key=:k ORDER BY score DESC LIMIT :n"),
        {"k": objection_type, "n": limit}).fetchall()
    return [r.content for r in rows]
```

### 4.6 Human escalation triggers (hard rules)

Demo/meeting request → mark `HOT_LEAD`, alert human, halt auto follow-ups. Custom pricing/negotiation/SLA → human. Hostile/legal language → suppress + alert supervisor. Inbound confidence < 0.70 → draft for human review, don't auto-send.

---

## 5. Phase-by-phase development plan

### PHASE 1 — Foundation & Core REST API

**Goal:** running Flask app, WAL SQLite with all 16 tables, per-connection pragmas, Product + Lead CRUD. No scraping, no LLM.

**Step 1.1 — Skeleton & config.** Create `app.py`, `config.py`, `logging_config.py`, `.env.example`, `requirements.txt` (`flask`, `flask-cors`, `sqlalchemy`, `python-dotenv`, `pytest`). Config loads keys + `DECISION_THRESHOLDS` from env. Enable CORS for the Vite dev origin. Structured JSON logging with a request id. **No secrets in source.**

**Step 1.2 — Models & pragma listener.** Implement `database/db_config.py` (§3.2), `database/models.py` (ORM mirror of all 16 tables), and run `migrate.py`. App factory calls nothing destructive on boot.

**Step 1.3 — Product CRUD** (`/api/v1/products`, GET/POST/PUT/DELETE). Validate `target_keywords`/`pain_point_mappings` parse as JSON → 422 on bad input, never 500.

**Step 1.4 — Lead CRUD & ingestion** (`/api/v1/leads`): list with `?product_id=&status=` filters (uses `idx_leads_product_status`), get one, manual create, status patch. Status transitions go through `lead_service` (built in Phase 3) — for now allow direct create/read.

**DoD tests (gate):**
- `test_db_pragmas.py`: `journal_mode`==`wal`, `foreign_keys`==1 on a live session.
- FK cascade: delete a product → its leads vanish (proves pragma is live).
- Product/Lead CRUD round-trips; bad JSON → 422; `/health` → 200; DB + `-wal` + `-shm` files created.

---

### PHASE 2 — Async Scraper Process & Gemini 2.5 Flash Scoring Engine

**Goal:** durable job queue, providers-first data acquisition, dedicated async scraper, and a confidence-scored Gemini scoring engine wired to the Decision Engine.

**Step 2.1 — Durable job queue** (`jobs/job_queue.py`, `jobs/worker.py`). Enqueue + atomic claim; pacing via `run_after`; retries with backoff; `DEAD` after `max_attempts`.

```python
def claim_next(db, job_type):
    row = db.execute(text(
        "SELECT id FROM jobs WHERE status='PENDING' AND job_type=:t "
        "AND run_after <= CURRENT_TIMESTAMP ORDER BY run_after LIMIT 1"),
        {"t": job_type}).fetchone()
    if not row: return None
    claimed = db.execute(text(
        "UPDATE jobs SET status='CLAIMED', attempts=attempts+1, updated_at=CURRENT_TIMESTAMP "
        "WHERE id=:id AND status='PENDING'"), {"id": row.id})
    db.commit()
    return row.id if claimed.rowcount > 0 else None   # lost the race → skip
```

**Step 2.2 — Data acquisition provider interface** (`services/data_acquisition/`). `base.LeadSourceProvider.discover()` returns lead dicts. Default chain: Places API → SerpAPI → B2B enrichment. `playwright_fallback.fetch_rendered()` is a generic render+extract helper with strict `try/finally` browser cleanup — no proxy rotation, fingerprinting, or CAPTCHA handling. Point it only at sites without an API.

```python
async def fetch_rendered(url, wait_selector=None, timeout=30000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width":1280,"height":800})
        page = await context.new_page()
        try:
            await page.goto(url, timeout=timeout)
            if wait_selector: await page.wait_for_selector(wait_selector, timeout=10000)
            return await page.content()
        finally:
            await page.close(); await context.close(); await browser.close()
```

**Step 2.3 — Dedicated async scraper runner** (`scraper_worker/async_runner.py`). One process, one asyncio loop, `asyncio.Semaphore(N)` cap. Pulls `DISCOVER`/`ENRICH`/`REVIEW` jobs, runs the provider chain, invokes the **Review Analyst agent** to map review text → weakness codes, writes results, enqueues `SCORE`.

**Step 2.4 — Gemini scoring engine** (`cognition/llm_client.py` + `agents/scoring_agent.py`). JSON-schema mode via the current `google-genai` SDK; clamp/validate; attach a `confidence`; route through the Decision Engine (`SCORING`, ≥0.70 autonomous else HUMAN).

```python
from google import genai
from google.genai import types
import json
from config import Config
client = genai.Client(api_key=Config.GEMINI_API_KEY)

def call_json(prompt, schema, temperature=0.2):
    resp = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema, temperature=temperature))
    return json.loads(resp.text)   # wrap caller in retry/backoff; never trust blindly
```

```python
# scoring_agent.py (core)
def score_lead(db, product, lead, reviews):
    data = call_json(build_scoring_prompt(product, lead, reviews), SCORING_SCHEMA)
    data["score"] = max(0, min(100, int(data["score"])))
    if data["tier"] not in {"HOT","WARM","COLD"}: data["tier"] = "COLD"
    conf = float(data.get("confidence", 0.0))
    route = route_action("SCORING", conf)
    log_agent_event(db, "SCORING", lead["id"], "SCORE", conf, "LOW", route)
    return data, route
```

**DoD tests (gate):**
- Atomic job claim under 10-thread contention → exactly one winner; future `run_after` not claimed; retry→`DEAD` at cap.
- Scoring output validates against schema, `0≤score≤100`, tier∈enum, confidence present; malformed model output coerced not crashed.
- **Memory leak:** loop `fetch_rendered` 50× → zero orphan chromium processes, flat RSS.
- Decision Engine: confidence 0.6→HUMAN, 0.8→QC, 0.9→EXECUTE (`test_decision_engine.py`).

---

### PHASE 3 — Autonomous Discovery Scheduling, Atomic Claiming & Multi-Channel Outreach

**Goal:** race-proof, compliant, QC-gated outreach with campaign memory and A/B.

**Step 3.1 — Atomic lead claiming** (`services/lead_service.py`).

```python
def claim_lead_for_outreach(db, lead_id) -> bool:
    res = db.execute(text(
        "UPDATE leads SET status='OUTREACHING', updated_at=CURRENT_TIMESTAMP "
        "WHERE id=:id AND status='SCORED'"), {"id": lead_id})
    db.commit()
    return res.rowcount > 0
```

Only dispatch on `True`. Success→`OUTREACHED`; hard fail→back to `SCORED` (or `REJECTED` after N). Add a **stale-claim sweeper** job resetting `OUTREACHING` leads older than X min (protects against a worker dying mid-send).

**Step 3.2 — Suppression enforcement** (`services/outreach/suppression.py`). `is_suppressed(db, channel, identifier)` checked before **every** send, unconditionally, ahead of any agent logic.

**Step 3.3 — Compliant email** (`services/outreach/email_service.py`). Outreach agent drafts A/B copy → **QC gate** → Resend with `List-Unsubscribe` + `List-Unsubscribe-Post` (RFC 8058), visible unsubscribe link + physical address in the body. Deliverability (SPF/DKIM/DMARC, dedicated warmed subdomain) is DNS/infra, done before first send. One-click unsubscribe inserts into `suppression_list` immediately.

```python
def send_email(db, lead, campaign, variant):
    if is_suppressed(db, "EMAIL", lead["primary_email"]):
        return {"status": "SKIPPED_SUPPRESSED"}
    draft = outreach_agent.draft(db, lead, campaign, variant)     # Outreach agent
    verdict = quality_controller.review(db, draft, lead)          # QC veto gate
    if not verdict["approved"] or verdict["confidence_score"] < 0.85:
        return regenerate_or_escalate(db, lead, draft, verdict)
    # ...POST to Resend with List-Unsubscribe headers + compliant footer...
    record_outreach(db, lead, campaign, variant, draft, "SENT")
```

**Step 3.4 — WhatsApp Cloud API** (`services/outreach/whatsapp_service.py`). Official Meta Graph API. First contact uses a pre-approved **template**; free-form only inside the 24-hour window after the lead replies. Opt-out → immediate suppression. (Drop Evolution/Baileys for first-touch — cold unofficial sends get numbers banned.)

**Step 3.5 — Autonomous Discovery Scheduler** (`jobs/discovery_scheduler.py`) — **as implemented; supersedes the n8n design below.** See tracker.md §A.2 for the full rationale (no Docker on the dev machine; the user's real self-hosted n8n instance can't reach a local-only Flask backend without a public URL; and, more fundamentally, the user did not want to manually type city/keyword combos in daily — they wanted the system to decide who to target on its own).

A single dedicated always-on process (same "one process per concern" topology as `scraper_worker/async_runner.py` vs `jobs/worker.py`) replaces n8n's scheduling role entirely — no external service, no Docker, no public URL:
- **Autonomous discovery targeting.** Activates §6's `ICP_STRATEGY_AGENT_SYSTEM_PROMPT` via `agents/icp_strategy_agent.py` (specified in the original PRD but never wired into a build step until this one). For each active product with `products.target_regions` set (new column — a human sets this once, multiple regions supported; the agent has no location-judgment input of its own, so geography stays human-bounded while business-type/keywords/target-complaints are AI-decided), the scheduler refreshes the product's ICP strategy when stale (`ICP_STRATEGY_REFRESH_DAYS`, default 7d) and fires paced `DISCOVER` jobs across `search_queries × target_regions`, capped per tick (`MAX_DISCOVER_PER_TICK`) and cooldown-gated per combo (`DISCOVERY_COOLDOWN_HOURS`) via a new `discovery_runs` tracking table. AI-generated and human-added queries (`product_strategies.source`) both apply; a human can add extra queries via `POST /api/v1/products/<id>/strategy/queries` without losing or being overwritten by the AI's own.
- **Outreach pacing tick** (every `OUTREACH_TICK_INTERVAL_SECONDS`, default hourly) — the same behavior originally described as `hourly_outreach_pacer.json` → `POST /api/v1/outreach/tick`, now a direct in-process call to `services/lead_service.py`'s `claim_lead_for_outreach()` (extended with `run_after` + `allowed_channels`): computes remaining per-channel daily budget from today's already-queued job counts, claims eligible `SCORED` leads up to that budget, staggers `run_after` so sends trickle out instead of bursting.
- `adaptability_sweep` / `POST /api/v1/campaigns/adapt` (§4.3) stays **not built** — deliberately deferred until Phase 4's inbound handler exists to supply real reply/open-rate data; building it earlier would be guesswork, not a data-driven sweep.

Dashboard visibility: `GET /api/v1/products/<id>/strategy` returns the active AI-generated + human-added strategy per product (full React view is still Phase 4.4; this only guarantees the data is inspectable now).

<details>
<summary>Original design (superseded, kept for reference)</summary>

**Step 3.5 — n8n workflow specs** (`n8n/workflows/`). n8n is scheduler/trigger, not brain:
- `morning_discovery.json`: cron 09:00 → HTTP `POST /api/v1/leads/discover` (Flask enqueues `DISCOVER`).
- `hourly_outreach_pacer.json`: cron hourly → `POST /api/v1/outreach/tick` (Flask enqueues a staggered batch respecting per-channel daily caps; the Phase-2 worker drains it).
- `adaptability_sweep.json`: cron → `POST /api/v1/campaigns/adapt` (runs §4.3 evaluation).

</details>

**DoD tests (gate):**
- 10 concurrent claims on one `SCORED` lead → exactly one `True`; stale-claim sweeper resets an old `OUTREACHING`.
- Suppressed identifier → `SKIPPED_SUPPRESSED`, no provider call; unsubscribe endpoint suppresses and blocks the next send.
- Outgoing email carries `List-Unsubscribe` + `List-Unsubscribe-Post` and a visible unsubscribe link.
- **QC gate:** a draft containing "game-changer"/"delve" or lacking the pain-point reference is rejected (`test_qc_gate.py`).
- Pacing: 40 queued emails respect the daily cap and staggered `run_after` (no burst). ✅ verified — `jobs/discovery_scheduler.py`'s `_run_outreach_tick` (tracker.md §A.2 / Phase 3 Step 3.5 completion entry).

---

### PHASE 4 — Inbound Handler, Human-in-the-Loop, React UI & Nightly Report

**Goal:** idempotent, guardrailed inbound; live dashboard; automated EOD report.

**Step 4.1 — Inbound webhook + idempotency** (`api/inbound.py`). Dedup on `(channel, provider_message_id)` — webhooks get re-delivered.

**Step 4.2 — Hard pre-classifiers (before any LLM).** `STOP`/`unsubscribe`/`not interested` → suppress immediately + record. Out-of-office/auto-responder → mark `AUTO_REPLY`, never "interested".

**Step 4.3 — Gemini intent classifier + escalation guardrail** (`agents/inbound_agent.py`). Returns `{intent, confidence, suppress_immediately, escalate_to_human, suggested_reply}`. Routing: `DEMO_REQUESTED`/`INTERESTED` or confidence<0.70 or hostile/legal → `HUMAN_ESCALATION` (Slack/WhatsApp alert, mark `HOT_LEAD`, halt auto follow-ups). Only low-risk high-confidence replies auto-send.

```python
def handle_inbound(db, evt):
    channel, sender, body = parse(evt); mid = provider_message_id(evt)
    if already_processed(db, channel, mid): return "duplicate_ignored"
    if is_optout(body):                                     # OPT_OUT — 100% rule
        add_to_suppression(db, channel, sender, "STOP")
        record_inbound(db, ..., intent="STOP"); return "suppressed"
    if is_autoreply(evt, body):
        record_inbound(db, ..., intent="AUTO_REPLY"); return "autoreply_ignored"
    result = call_json(build_inbound_prompt(db, body, history(db, sender)), INBOUND_SCHEMA)
    route = route_action("INBOUND_REPLY", result["confidence"],
                         is_high_risk=looks_pricing_or_legal(body))
    record_inbound(db, ..., intent=result["intent"], confidence=result["confidence"])
    if route in ("HUMAN_ESCALATION",) or result["escalate_to_human"]:
        fire_alert(db, sender, result)                      # human takes over
    else:
        enqueue(db, "OUTREACH_EMAIL", {...})                # low-risk auto-reply
    return "processed"
```

**Step 4.4 — React dashboard** (`frontend/`, Vite+React+Tailwind). `ProductForm` (dynamic product registration, no code change to add products), `PipelineKanban` (columns by `status`), `LeadCard` (score/tier/justification), `AlertsPanel` (polls `/api/v1/alerts`; rep claims a HOT lead). Read-mostly in v1 — AI owns transitions, humans act on HOT leads. Use `api/client.js` as a thin fetch wrapper; no `<form>` submit side-effects, use `onClick` handlers.

**Step 4.5 — EOD executive report** (`services/reporting_service.py`). Cron 23:50, scheduled the same way as `jobs/discovery_scheduler.py`'s own ticks (§3.5 amendment — no n8n): aggregate discovered/scored-by-tier/outreached-per-channel/replies/high-intent + KPI framework (bounce <2%, spam <0.1%, intent accuracy, escalation response time) into `daily_reports`; CEO agent writes the executive summary; email it.

**DoD tests (gate):**
- Duplicate `provider_message_id` → processed once. `STOP` → suppressed, no LLM call. OOO → not "interested". Hostile/pricing → escalated, no auto-reply. Confidence<0.70 → escalated (`test_inbound_edge_cases.py`).
- Exactly one alert fires per `DEMO_REQUESTED`.
- Dashboard: create product in UI → visible via API; leads render in correct column; HOT leads surface in AlertsPanel.
- EOD: `generate` writes a `daily_reports` row and sends the email with correct counts.

---

### PHASE 5 — Executive Business OS & Governance Layer

**Goal:** revenue/CAC-aware budget control, dual sales-mode routing, capacity-throttled discovery, post-sale lifecycle tracking, and a governance hierarchy that resolves cross-agent conflicts — layered on top of Phases 1–4 without changing their contracts. Full module specification: §8.

**Step 5.1 — Schema additions.** Add `team_capacity` and `client_lifecycle` (Tables 15–16, §3.1) and the `leads.sales_route` column. Seed `team_capacity` with one row per delivery team (`ONBOARDING`, `DEV_SERVICES`).

**Step 5.2 — Dual Sales Mode Engine** (`cognition/dual_sales_engine.py`, §8.2). Wire `route_sales_mode()` into the pipeline right after `ENRICHED` (needs `lead_firmographics.company_size_range`), before `REVIEWED`/`SCORED`. `outreach_agent.py`'s prompt selection (§6) branches on `sales_route`: `SAAS_PRODUCT` gets the existing subscription-pitch prompt; `CUSTOM_DEV` gets a bespoke-development variant that routes to a human-quoted proposal and never auto-prices (§8.8 boundary).

**Step 5.3 — Capacity & Resource Intelligence** (`cognition/capacity_intelligence.py`, §8.1/§8.3). Wire `check_discovery_throttle()` into `scraper_worker/async_runner.py` immediately before claiming any `DISCOVER` job — a `THROTTLED` result skips the claim and leaves the job `PENDING`, no job is lost. Wire `check_cac_ceiling()` into the existing `adaptability_sweep` cron alongside the §4.3 checks.

**Step 5.4 — Executive & Lifecycle APIs** (`api/executive.py`, `api/lifecycle.py`, `agents/lifecycle_agent.py`, §8.5/§8.6). `POST /api/v1/executive/simulate` — read-only Monte Carlo over historical `outreach_logs`/`lead_scores`/`campaign_variants`, advisory only, never auto-applies. `POST /api/v1/lifecycle/convert` transitions a `CONVERTED` lead into a `client_lifecycle` row. A daily job (piggyback on the `eod_report` cron) calls `enqueue_renewal_reminders()`.

**Step 5.5 — Governance hierarchy** (extend `cognition/decision_engine.py`, §8.7). Add `resolve_conflict()` and `GOVERNANCE_RANK`. QC's veto stays absolute exactly as in §4.1/§4.2 — Phase 5 only adds an explicit tie-break for agents ranked below QC.

**Step 5.6 — Self-evolution boundaries** (extend `config.py` and `cognition/adaptability.py`, §8.8). Add `ADAPTABLE_PARAMS`/`HUMAN_LOCKED_PARAMS` and call `guard_adaptation()` from every autonomous parameter-write path, including the existing §4.3 `evaluate_campaign` actions.

**Step 5.7 — Executive dashboard** (`frontend/src/pages/ExecutiveControl.jsx`, `frontend/src/components/CapacityMeter.jsx`). Read-only v1: live capacity gauge per team, CAC-vs-ceiling per product, pending renewal list, and a simulate-budget form that calls `/executive/simulate` and renders p10/p50/p90 — no auto-apply button; a human copies the result into a real campaign action via the existing CEO-agent path.

**DoD tests (gate):**
- `test_dual_sales_routing.py`: headcount > 50 → `sales_route='CUSTOM_DEV'`; headcount < 20 → `'SAAS_PRODUCT'`; 21–49 band exercises the LLM tiebreak path and is never silently defaulted.
- `test_capacity_throttle.py`: `team_capacity` at ≥90% utilization → `check_discovery_throttle()` returns `THROTTLED` and no `DISCOVER` job gets claimed while throttled; dropping below the cap re-opens discovery.
- `test_lifecycle_renewal.py`: a `client_lifecycle` row with `contract_end_date` 30 days out → exactly one `RENEWAL_REMINDER` job enqueued; a row 45 days out → none yet.
- `test_governance_hierarchy.py`: conflicting proposals from two operational agents resolve by `GOVERNANCE_RANK`; a QC reject always wins regardless of rank.
- `test_self_evolution_boundaries.py`: any attempted write to a `HUMAN_LOCKED_PARAMS` key raises and routes to `HUMAN_ESCALATION`; `ADAPTABLE_PARAMS` writes succeed unblocked.

---

## 5A. Add-on phase plan (Phases 6–10) — added 2026-08-19

**Origin.** Phases 1–5 were specified before the system had ever run against real leads. Phases 6–10
come from the opposite direction: eleven requirements the user raised *after* watching the live system
work (captured verbatim in `NEW_REQUIREMENTS_STAGING.md`), plus every item this project had explicitly
deferred along the way and never lost — the ⭐ Autonomous WhatsApp Template loop, Hunter's discarded
person-level fields, the `campaign_variants` table that was designed in Phase 1's DDL and never wired,
the 604-lead social backfill, and three known discovery-precision bugs.

**The user's stated goal for this whole block:** *"ab hum jo ai outreach karvaye wo open and read it
ratio badhaye"* — raise open/read/reply rates on real outreach. Every phase below is ordered by what
that goal actually depends on, not by what is most exciting to build.

### 5A.0 Sequencing logic (read this before reordering anything)

The order is forced by three real dependencies, not preference:

1. **Measurement before adaptation.** The ⭐ WhatsApp Template Creation & Approval Loop was deferred
   on 2026-08-13 for one stated reason: *"this needs real performance data to be meaningful — which
   template underperforms... That data doesn't exist yet (`campaign_variants` not wired up)."* That
   same missing data blocks AI-generated adaptive templates (Item 4d) and true subject-line testing
   (Item 6). So Phase 8 must produce **variants**, Phase 9 must **measure** them, and only then can the
   AI adapt them. Building the adaptive layer first would produce a guess-based "learning" agent — the
   exact thing that deferral was avoiding.
2. **Targeting before copy.** A message format (Phase 8) can only personalise as well as the targeting
   data underneath it. Phase 7's product-level target category/role fields and person-level contacts
   are what give Phase 8's format slots something real to say.
3. **Visibility before everything.** Phase 6 is first because the user currently cannot see what the
   running system is doing at all (*"abhi crm me ye pata nahi chal raha he ki system kya kar raha he"*).
   Every phase after it becomes verifiable-in-the-open rather than verifiable-only-by-SSH.

**Risk ordering runs the same direction.** Phase 6 adds no external dependency, no cost, no legal
surface. Phase 10 adds new paid providers, new per-country compliance law, and the highest-stakes
channel in the entire product (AI voice calls). Deliberately last, and each of its sub-steps gates
independently — Phase 10 is the one phase that may legitimately ship partially.

**Relationship to Phase 5 — RESOLVED 2026-08-19: Phase 5 is postponed indefinitely.** This project's
own rule (§9, tracker.md §A) is strict phase order: no phase starts before the previous DoD gate is
green. Phase 5 (Executive Business OS) has not started, and Phases 6–10 have **no technical dependency
on it** — they extend the discovery/outreach path, while Phase 5 governs budget/capacity/lifecycle
above it.

**The user's decision: skip Phase 5 for now and run 6 → 7 → 8 → 9 → 10 directly.** The reasoning holds
up on its own terms — Phase 5's modules (CAC ceilings, capacity throttling, renewal lifecycle,
executive simulation) all become valuable at a volume of real customers the business does not have
yet, and throttling a funnel that is not yet saturated solves a problem that does not exist. Phases
6–10 address what is actually costing the operator today: no visibility, imprecise targeting, and low
open/read rates.

**Recorded as a deliberate deviation** from §9's ordering rule (tracker.md §A.6), not an oversight.
Phase 5's spec in §5 stays exactly as written — nothing is deleted, and its DoD gate P5 remains in the
§9 table. Revisit it when the business genuinely has delivery-capacity pressure or converted clients
to track; at that point it slots in cleanly, since none of Phases 6–10 change the contracts it depends
on.

### 5A.1 New data-layer objects introduced across Phases 6–10

**Real current table count: 19, not 16.** §3.1's DDL prose says 16 because three tables were added
during Phases 3–4 after that section was written — `product_strategies` (17, §3.5 amendment),
`discovery_runs` (18, discovery cooldown) and `system_settings` (19, dashboard toggles). Verified
against the live `schema.sql`, not assumed. Phases 6–10 therefore add Tables **20–27 (total 27)**,
plus two `products` columns, and finally use `campaign_variants` (Table 13), which has existed since
Phase 1 and has never been written to. Migrations go through `migrate.py` (schema.sql's
`CREATE TABLE IF NOT EXISTS` for new tables, `COLUMN_MIGRATIONS` for new columns on existing ones) —
never a manual `ALTER` on a live DB.

| # | Table | Phase | Purpose |
|---|-------|-------|---------|
| 20 | `system_heartbeats` | 6 | one row per long-running process; liveness without shell access |
| 21 | `lead_contacts` | 7 | **multiple** people per lead (today `leads` holds exactly one contact) |
| 22 | `message_formats` | 8 | admin-authored message STRUCTURE (slots), not content |
| 23 | `content_assets` | 8 | demo URLs / case studies / testimonials the AI selects from |
| 24 | `outreach_sequences` | 9 | multi-touch cadence state per lead |
| 25 | `whatsapp_templates` | 9 | local mirror of each Meta template's real approval state |
| 26 | `channel_policies` | 10 | region → allowed/preferred channel rules |
| 27 | `call_logs` | 10 | AI voice call records, consent basis, transcript ref |

New `products` columns (Phase 7): `target_business_categories` (JSON array), `target_person_roles`
(JSON array). Both optional and nullable — an existing product with neither set must behave exactly as
it does today.

---

### PHASE 6 — Live System Observability

**Goal:** the CRM shows, without SSH, whether the system is alive and what it is doing right now.
No new external dependency, no cost, no new risk surface — which is why it goes first.

**Why this is not just a dashboard nicety:** two real incidents this project already had were invisible
from the UI — a background process that had silently not been running for a session (tracker.md
2026-08-18), and two leads stuck mid-outreach after a provider outage (2026-08-19). Both were found
only by reading logs over SSH. This phase is the systemic fix for that class of blindness.

**Step 6.1 — Heartbeat table + process reporting.** New Table 17 `system_heartbeats`
(`process_name` PK, `last_seen_at`, `status`, `detail` JSON). Each long-running process — `jobs.worker`,
`scraper_worker.async_runner`, `jobs.discovery_scheduler`, `jobs.inbound_poller` — writes/updates its
own row on every loop iteration. Deliberately a DB heartbeat, **not** a `systemctl` shell-out: the API
process must never need root, and the same code must work on the dev machine where nothing is a
systemd unit.

**Step 6.2 — Live status API** (`api/system.py` → `GET /api/v1/system/live`). Returns, in one call:
per-process liveness (`last_seen_at` older than a configurable staleness window ⇒ `DOWN`), job-queue
counts grouped by `status` × `job_type`, counts of leads currently mid-flight (`OUTREACHING`), and the
last N `agent_events` as a real activity feed. All read-only, all from tables that already exist.

**Step 6.3 — Live monitor UI** (`frontend/src/pages/SystemMonitor.jsx`, CRM_UI_UX_PLAN Phase 5).
Simple interval polling — no WebSocket. This project's own precedent (dropping n8n, §3.5 amendment) is
to refuse infrastructure that a simpler mechanism already covers.

**Step 6.4 — Stuck-state detection + admin alert.** A scheduler tick flags anything genuinely stuck:
a process stale beyond the window, a lead sitting in `OUTREACHING` far longer than a send can take, or
`DEAD` jobs accumulating. Surfaced in the UI and — reusing `send_internal_email()` from Step 4.5, not a
new mechanism — emailed to the admin. Rate-limited so an outage cannot generate an email storm.

**DoD tests (gate):**
- `test_heartbeat_liveness.py`: kill one worker process → `/system/live` reports it `DOWN` within the
  staleness window; restart → `UP` again. Verified against real processes, not mocked timestamps.
- Activity feed shows a real discovery and a real outreach as they happen, cross-checked against a
  direct SQL query of `agent_events` (the project's standing "chart must match ground truth" rule).
- A lead deliberately left in `OUTREACHING` is flagged as stuck; a lead mid-legitimate-send is not.
- The alert path sends exactly one email per incident, not one per tick.

---

### PHASE 7 — Targeting Precision & Person-Level Contacts

**Goal:** stop aiming at "a business" and start aiming at **the right business, and the right person
inside it** — plus close three known discovery-precision bugs that have been on the open-items list
since Phase 2.

**Step 7.1 — Product targeting fields.** Add `products.target_business_categories` and
`products.target_person_roles` (both JSON arrays, both optional). Products CRUD + UI accept them
(CRM_UI_UX_PLAN Phase 6). Same design precedent as `target_regions` (§3.5 amendment): a **human-set
boundary the AI then works freely inside**, never an AI-invented one.

**Step 7.2 — ICP strategy agent consumes the categories.** `agents/icp_strategy_agent.py` currently
invents prospect verticals from the product brief alone — which is exactly what produced the
self-referential-query bug (tracker.md 2026-08-18: 157 leads had to be rejected). When
`target_business_categories` is set, the agent must generate queries **within** those categories only.
Empty ⇒ today's behaviour, unchanged.

**Step 7.3 — Multi-contact schema.** New Table 18 `lead_contacts` (`lead_id` FK, `full_name`, `role`,
`seniority`, `department`, `email`, `phone`, `linkedin_url`, `is_decision_maker`, `source`,
`confidence`). Today `leads` carries exactly one `contact_person_name`/`_role`, which cannot represent
"the CEO and the sales manager at the same company." `leads.primary_email`/`primary_phone` stay as the
canonical outreach target for backward compatibility; `lead_contacts` is additive.

**Step 7.4 — Unlock Hunter's discarded person data.** `HunterProvider.enrich_domain()` already
receives `linkedin`, `seniority`, `department`, `position` and a decision-maker signal per contact from
Hunter's real API response and currently **throws all of it away**, keeping only the single best email.
Persist every returned contact into `lead_contacts`. Zero new API cost — this is data already being
paid for and discarded.

**Step 7.5 — Role-targeted LinkedIn person discovery.** When `target_person_roles` is set, search for
that role at that company (Serper, reusing the already-proven `_is_own_profile_link` /
`_name_words()` trust discipline from the social-profile feature). Company LinkedIn is treated as a
**priority signal, not best-effort** (user: *"unke linkedin to hoga hi to wo must needed he"*): a
resolved company page is what triggers the person-level lookup. **Hard rule, inherited from the
existing social-profile work:** a person is only ever attached to a lead when the company's own name
verifiably matches — a wrong person on a real lead is a real mis-contact, exactly the reasoning that
kept `_extract_city()` off `find_phone`/`find_email`.

**Step 7.6 — Close three long-open discovery bugs.** All three are on the tracker's known-open list and
all three cause wrong-business contact data: (a) `_handle_discover` does not filter Places results to
the queried city; (b) cross-city name collisions in `find_website`/`find_phone`/`find_email`;
(c) multi-branch businesses resolving to whichever branch ranked that day.

**Step 7.7 — Social-profile backfill.** Run the (already-built, already-verified) social-profile
enrichment across the existing lead base — offered when that feature shipped, never executed. Batched
and resumable; Serper spend estimated and confirmed with the user before the run, not during it.

**DoD tests (gate):**
- A product with `target_business_categories` set produces only in-category search queries across a
  real ICP regeneration; a product with none set produces byte-identical behaviour to today.
- `lead_contacts` populated from a real Hunter response with ≥1 role/seniority field preserved, and the
  lead's existing `primary_email` unchanged (proves the addition is non-destructive).
- Role-targeted lookup measured on a real sample of corporate leads: hit-rate reported honestly, and
  **zero wrong-company person attachments** — the second number is the gate, not the first.
- City filter: a search for city A returns no lead whose address resolves to city B.
- Backfill: re-running it is idempotent (no duplicate writes, no re-spend on already-enriched leads).

---

### PHASE 8 — Message Format Engine & Content Library

**Goal:** the admin defines the message's **structure**; the AI fills that structure per lead and
product. This is the phase that directly targets the user's stated open/read-rate goal.

**The distinction that defines this phase:** the admin authors a *format*, never final copy —
"greeting/hook → 2-3 of this business's own weak points → how we solve them → demo link if relevant."
The AI supplies the content for each slot from that specific lead's real, verified pain points. Today
`outreach_agent.py` free-writes the entire message, which is why output quality varies per send and
cannot be steered without a code change.

**Step 8.1 — Format schema.** New Table 19 `message_formats` (`product_id` nullable for a global
default, `channel` (`EMAIL`/`WHATSAPP`), `slots` JSON ordered list, `is_active`, `version`). Resolution
order: product+channel format → global channel format → today's free-form behaviour. Versioned rather
than overwritten (same precedent as `product_strategies`), so a format change never silently
invalidates the performance history Phase 9 measures.

**Step 8.2 — Content asset library.** New Table 20 `content_assets` (`product_id` nullable,
`asset_type` (`DEMO_URL`/`VIDEO_URL`/`CASE_STUDY`/`TESTIMONIAL`/`TEXT_BLOCK`), `title`, `value`,
`tags` JSON, `is_active`). The AI **selects** from this library per lead/product — it never invents a
URL. A format slot that asks for a demo link and finds no matching asset renders the message without
that slot rather than fabricating one.

**Step 8.3 — Format-driven drafting.** `agents/outreach_agent.py` fills the resolved format instead of
free-writing. Unchanged and non-negotiable: the Quality Controller's veto stays absolute (§4.1), the
buzzword ban and pain-point-grounding rules still apply, and a draft that references no verified pain
point is still rejected. A format cannot be used to bypass QC.

**Step 8.4 — Subject-line candidates.** The email drafting call returns N subject candidates; one is
selected. In this phase selection is AI judgment from lead context — **not** performance-driven, because
the performance data does not exist until Phase 9. All candidates are persisted so Phase 9 can measure
them retrospectively.

**Step 8.5 — Format builder + content library UI** (CRM_UI_UX_PLAN Phase 7).

**DoD tests (gate):**
- Same lead, two different formats → drafts provably follow their respective slot structures.
- A product-scoped asset is chosen for that product and never leaks into a different product's message.
- A format demanding a demo link with no asset available produces a valid message with no fabricated URL.
- QC still vetoes a deliberately bad format-filled draft, via a real LLM call (repeat of the Phase 3
  gate's real-veto test, not a mocked one).
- A lead with no verified pain points still cannot produce a pain-point-claiming message.

---

### PHASE 9 — Measurement, Multi-Touch & Adaptive Templates

**Goal:** close the loop. Measure what actually works, follow up on what does not, and finally build
the ⭐ deferred autonomous template loop — now on real data instead of guesses.

**Step 9.1 — Wire `campaign_variants`.** Table 12 has existed since Phase 1 and has never been written
to. Every send records which format version, subject candidate and template it used. This single step
is what unblocks the rest of this phase and Item 4d.

**Step 9.2 — Variant performance rollup.** Sent / seen / replied per variant, built on the **real Seen
tracking that already exists** (`OutreachLog.provider_message_id`, `read_at`, both channels' status
webhooks — built 2026-08-17/18). No estimated or modelled numbers: a metric with no real signal stays
`null`, exactly as Step 4.5's KPI section already does.

**Step 9.3 — Multi-touch follow-up sequences.** New Table 21 `outreach_sequences` (per-lead cadence
state, step index, next-run, terminal reason). Cadence is configurable per product. **Every existing
outreach rule applies unchanged at every touch, not just the first:** suppression re-checked immediately
before each send, OPT_OUT absolute, daily pacing caps respected, and the whole sequencer sits behind
`autonomous_outreach_enabled` — a follow-up is still an autonomous real send to a real business.

**Step 9.4 — Engagement-based escalation.** A lead that opens repeatedly but never replies is a real
signal being wasted today. Configurable threshold → switch channel or raise a human alert through the
existing escalation path. Where open data is unavailable for a channel, the rule simply does not fire —
it must never be inferred.

**Step 9.5 — Admin WhatsApp template submission.** New Table 22 `whatsapp_templates` mirrors each
template's real Meta-side state (`PENDING`/`APPROVED`/`REJECTED`, category, components, rejection
reason). Admin composes and submits from the CRM via Meta's Business Management API; a poll updates
approval state and activates approved templates **without a code edit** — today `TEMPLATE_LIBRARY`
requires one.

**Step 9.6 — ⭐ Autonomous adaptive template loop** *(the item the user flagged on 2026-08-13 as taking
the system "to the next level"; deferred then, unblocked now).* Using Step 9.2's real performance data,
the system detects an underperforming or missing template, drafts a replacement respecting Meta's
component/variable rules, submits it, and detects approval on its own. **Guardrails, all mandatory:**
QC review before submission, a human approval gate before any AI-authored template goes live to real
businesses, and cold first-contact still restricted to Meta-approved templates (§B, non-negotiable).
The AI proposes; a human still signs off before real strangers receive it.

**DoD tests (gate):**
- Variant stats reconcile exactly against a direct SQL query for one real day.
- Follow-up sequence: an opt-out mid-sequence stops every subsequent touch immediately; a replied lead
  exits the sequence; pacing caps hold across a multi-lead batch; no duplicate sends under concurrency
  (the Phase 3 atomic-claim contention test, re-run against the sequencer).
- Kill-switch honoured: with `autonomous_outreach_enabled` false, zero follow-ups leave the system.
- A real template submitted from the CRM reaches Meta and its real approval state is detected and
  reflected without a code change.
- An AI-drafted template cannot reach a real business without passing QC **and** a human approval.

---

### PHASE 10 — Channel Expansion (region-aware, gated per channel)

**Goal:** reach leads on the channel they actually use. Highest cost, highest compliance exposure, and
the newest infrastructure in the entire product — deliberately last, and the only phase designed to
legitimately ship partially.

**Step 10.1 — Region-aware channel routing.** New Table 23 `channel_policies` maps a region to allowed
and preferred channels. Solves the user's real observation that WhatsApp is not a reliable channel
outside India — the system's existing Canadian leads are a live example. `products.target_regions`
(already present) feeds the decision. Email stays the universal fallback: it is the one channel that
works everywhere and carries no new risk.

**Step 10.2 — SMS channel.** Provider-backed (Twilio-class), reusing the existing outreach handler
shape, suppression list and pacing caps rather than a parallel path. **Compliance is a hard gate, not a
note:** SMS outreach law is country-specific (US TCPA, Canada CASL, EU rules); the channel must refuse
to send into a region whose policy is not explicitly configured. Its own kill-switch, default off.

**Step 10.3 — Social messaging: draft-and-queue, not auto-send.** Straight answer to the user's
LinkedIn and Instagram/Facebook requests, and the reason this is designed the way it is:
- **LinkedIn** offers no official API for general cold messaging. The only way to automate it is
  browser-driving a real logged-in account — a ToS violation with a permanent-ban risk, and a direct
  contradiction of this project's own evasion-free rule (§B).
- **Instagram/Facebook** *do* have official Meta messaging APIs, but Meta's policy only permits
  messaging someone who contacted **you** first, inside a reply window. There is no cold-template
  equivalent to WhatsApp's.
- **Therefore:** the AI drafts LinkedIn/IG/FB messages into a **human-send queue** — a team member
  reviews, sends manually, and marks sent. Full AI value (research, personalisation, drafting) with
  zero account-ban and zero policy risk. Automated *sending* on these platforms is out of scope, and
  should stay out of scope unless the platform's own rules change.
- **Additionally allowed and worth building:** IG/FB **reply-window** auto-response for leads who
  message *us* first — genuinely permitted by Meta, and it reuses the existing inbound classifier and
  escalation path rather than adding a new one.

**Step 10.4 — AI voice calling.** The highest-stakes channel in the product. Cold-calling law is far
stricter than email or messaging — India's TRAI DND regime, and US TCPA where AI/prerecorded calls
carry per-call statutory penalties. Requirements, all mandatory: **its own kill-switch, independent of
and stricter than `autonomous_outreach_enabled`**; an explicit consent/legal-basis check per lead before
any dial; a region gate (launch only where compliance is actually established); recorded consent basis
and outcome in Table 24 `call_logs`; and immediate human handoff on anything the AI cannot handle.
**Ship AI-assisted first** (a human dials, the AI assists live) — fully autonomous dialling only after
the assisted mode has run against real calls and the compliance posture is proven.

**DoD tests (gate) — each channel gates independently:**
- Region routing: a Canadian lead is never queued for WhatsApp when policy excludes it; an Indian lead
  is unaffected; a region with no policy configured falls back to email and never guesses.
- SMS: a send into an unconfigured region is refused, not attempted. Suppression and opt-out behave
  identically to email/WhatsApp (re-run those exact tests against the SMS path).
- Social: the draft queue can produce a message and mark it sent, and **no code path exists that can
  send a LinkedIn/IG/FB message automatically** — verified by absence, deliberately.
- Voice: with the voice kill-switch off, zero calls are placed under any condition. A lead without a
  recorded consent basis is never dialled even with the switch on.

---

## 5B. Add-on phase plan (Phases 11–15) — added 2026-08-22

**Origin.** Phases 6–10 were specified after the operator first watched the system run. Phases 11–15
come from a second round of the same thing — six requirements raised after Phases 6–9 were live on real
leads and Phase 10 had partially shipped (captured verbatim as Items 12–17 in
`NEW_REQUIREMENTS_STAGING.md`, Batch 2).

**What changed between the two rounds.** Phases 6–10 answered *"the system can act, but I cannot see
it, steer it, or measure it."* All three of those are now true. Batch 2 answers a different, later
complaint: **the system speaks competently but not persuasively, cannot be answered in one click,
repeats itself across touches, drifts between channels, and often reaches a person who cannot judge the
pitch at all.** Every phase below targets one of those five.

**The operator's stated goal for this block:** the outreach email *"sirf marketing jese nahi lagne
chahiye — log view karne ke liye majbur hojaye"* — a message a real person feels compelled to open and
read, and can act on without composing a reply.

### 5B.0 Sequencing logic (read this before reordering anything)

The order is forced by four real dependencies, not preference:

1. **A structure must exist before anything can live inside it.** Today an outreach email body is a
   single free-form prose blob (`services/outreach/email_service.py`'s `_build_html()` escapes it,
   linkifies URLs, and optionally appends one video-thumbnail block). Nothing downstream can address
   "the CTA section" or "the video section", because sections are not objects yet. Phase 12's Yes/No
   buttons, Phase 13's per-level emails, Phase 14's cross-channel re-render, and Phase 11's own AI
   cross-sell block all require that composition layer first. It goes first for the same structural
   reason Phase 8's format engine preceded Phase 9's measurement of it.
2. **A click can only be captured if there is a button to click.** Phase 12 (interest capture) is
   meaningless before Phase 11 ships a real button — and it needs the same public-URL surface the
   one-click unsubscribe endpoint already uses (`Config.PUBLIC_BASE_URL`), so it adds no new
   infrastructure, only a new signed route.
3. **Follow-up levels are a content problem, not a plumbing problem.** The cadence machinery already
   works and is gate-proven (Phase 9 Step 9.3: configurable delays, atomic claim under contention,
   reply/opt-out exit at every touch). Phase 13 changes *what each touch says*, which needs Phase 11's
   sections — and, for its final touch, a real per-product services list. Rebuilding cadence would be
   re-solving a solved problem.
4. **New paid provider last, again.** Phase 15's standalone prospect finder needs a new external,
   billable data provider (Apollo.io or equivalent) that has not been chosen or purchased. Same posture
   that put SMS and voice at the end of Phase 10 — and the same reason: this project has already lost a
   verification cycle to an exhausted third-party quota (Hunter, 0/50, tracker.md Phase 7 DoD).
   Phase 15's two halves therefore **gate independently**: 15(A) rides on machinery that already exists
   and can ship alone.

**Risk ordering runs the same direction.** Phase 11 changes only how an already-approved message is
composed and rendered — no new external surface. Phase 12 opens a new *public, unauthenticated* HTTP
route that a stranger can hit, which is a real security surface and is specified as signed and
tamper-refusing rather than trusted. Phase 15 adds new spend. Deliberately last.

**Relationship to the still-open Phase 10 work.** Steps 10.2 (SMS), 10.3(b) (IG/FB reply-window
auto-response) and 10.4 (voice) remain deliberately on hold for missing provider credentials
(tracker.md §A.9), and nothing in Phases 11–15 depends on them. Phase 14 does extend Step 10.3(a)'s
already-shipped social draft-and-queue, which is live. Phase 10's own gate P10 stays exactly as
written — a partially-shipped phase is not a skipped gate; the shipped sub-steps passed their own
criteria, the unshipped ones will pass theirs when they ship.

### 5B.1 New data-layer objects introduced across Phases 11–15

**Real current table count: 28, not 27.** §5A.1 projected 27 because `social_message_queue` did not
exist in that plan — it was added while building Step 10.3(a), where a QC-gated human-send queue turned
out to need its own state (`QUEUED`/`SENT`/`DISMISSED`) rather than living inside `outreach_logs`, which
records things that were actually sent. Verified against the live `schema.sql`, not assumed. Phases
11–15 therefore add Tables **29–31 (total 31)**, plus four columns on existing tables.

| # | Table | Phase | Purpose |
|---|-------|-------|---------|
| 29 | `interest_responses` | 12 | one row per real Yes/No click: which lead, which send, which answer |
| 30 | `prospects` | 15 | person-level contacts found *without* a company lead (standalone finder) |
| 31 | `prospect_searches` | 15 | the search criteria, provider, result count and **real API spend** per run |

New columns on existing tables:

| Table | Column | Phase | Purpose |
|-------|--------|-------|---------|
| `products` | `ai_cross_sell_enabled` | 11 | per-product opt-in for the AI-services cross-sell block (Item 17) |
| `outreach_logs` | `content_sections` | 11 | the canonical structured content this send was rendered from (JSON) |
| `leads` | `reference_code` | 12 | short human-readable lead identifier an operator can actually quote |
| `whatsapp_templates` | `followup_level` | 13 | which follow-up level (1/2/3) this template is written for |

**Two things this block deliberately does NOT add a table for**, because an existing structure already
holds them correctly:
- **Our own company contact details** (Item 12's contact block) → `system_settings`, the existing
  dashboard-editable key/value store (Phase 4 Step 4.4). No schema change at all, and the operator can
  edit them without a deploy — which is the whole reason that table exists.
- **The products/services list** for Phase 13's final follow-up touch → the `products` table itself.
  Inventing a second list of what we sell would immediately drift from the first one.

---

### PHASE 11 — Designed Outreach Composition

**Goal:** turn the outreach email from one block of AI prose into a **structured, designed, personalised
message** — one that reads like a real person wrote it about *this* business, and looks like a
professionally built email rather than a text dump.

**Why this is a composition change, not a styling change:** the operator's requirement is a fixed
*sequence of sections*, each with its own job — a hook that reads like a customer describing their own
problem, that business's real pain points as bullets, our solution as bullets, a product video, a free-
trial CTA with a demo button, a one-click interest answer, our contact details, and the compliance
footer. Today's pipeline cannot express that: `draft_email()` returns `{subject, body}` where `body` is
undifferentiated prose, so there is no section to skip when an asset is missing, no section for a button
to attach to, and no section boundary for Phase 14 to re-render for another channel. The sections have
to become real objects before any of that is possible.

**Step 11.1 — Structured section contract.** `agents/outreach_agent.py`'s `draft_email()` returns
`sections` — an ordered list of typed blocks (`HOOK`, `PAIN_POINTS`, `SOLUTION`, `VIDEO`, `CTA`,
`INTEREST`, `CONTACT`, `FOOTER`) with typed payloads (a bullet list is a real list, not a newline-joined
string). `subject` keeps its existing 3-candidate selection (Step 8.4) unchanged. The existing
free-form path stays intact for any caller that hasn't opted in, so nothing already live changes
behaviour on the day this ships.

**Step 11.2 — HTML renderer.** New `services/outreach/email_renderer.py` renders sections to real email
HTML: **table-based layout, fully inline styles, no external stylesheet, no JavaScript, no web fonts** —
not a preference, the actual constraint every mail client imposes. Action URLs render as **styled
buttons, never bare links** (the operator's explicit ask). Every image carries real `alt` text and the
layout must still read correctly with images blocked, which is the default in a large share of real
inboxes — so the video block degrades to a visible labelled link, not an empty box.

**Step 11.3 — Graceful section omission.** A section with no real content is **removed entirely** —
no empty heading, no orphan spacing, no "N/A". This is the operator's explicit requirement (*"agar koi
section na bhi ho like video na ho to ye bhi handle ho jaye"*) and it extends the rule Phase 8 already
established for content assets: a missing asset drops its slot rather than being fabricated. The
difference here is that dropping a slot must now also be *visually* clean, not merely factually honest.

**Step 11.4 — Company contact block from settings.** The contact section (email, mobile, website,
company profile link) reads from `system_settings`, editable from the Settings page with no deploy.
Absent values drop out of the block by the same Step 11.3 rule.

**Step 11.5 — AI cross-sell block (Item 17), per-product opt-in.** New `products.ai_cross_sell_enabled`
(default off). When on, a short factual availability line is appended near the contact block —
*"we also build AI automation for businesses like yours"* in the agent's own words, grounded in real
product records. **Explicitly bound by the existing buzzword ban:** this must read as a factual
statement of what we offer, never as AI hype ("revolutionary", "cutting-edge" are already banned by
`GUARDRAIL_PREAMBLE` and stay banned here). Off by default and per-product because a highly specific
niche pitch is diluted, not helped, by a generic second offer.

**Step 11.6 — QC extension.** `review_draft()` additionally verifies **structural** correctness: the
sections are in the required order, no section is empty-but-present, the CTA/demo URL is a real approved
asset (reusing the `APPROVED_CONTENT_ASSETS` grounding added 2026-08-21), and the cross-sell line — when
present — is factual rather than hype. QC's veto stays absolute and still fails closed.

**DoD tests (gate):**
- A product with no video asset produces an email with **no empty block, no orphan heading, and no
  broken layout** — checked against the real rendered HTML, not the section list.
- Every action URL renders as a real styled button; zero bare `<a>` links in the action positions.
- The same structure, run against two genuinely different real leads, produces genuinely different
  section content — personalisation proven by real output, not asserted from the prompt.
- Rendered HTML contains no external stylesheet, no `<script>`, and no remote font; layout still reads
  correctly with images disabled.
- The cross-sell block appears **only** for a product with the flag on, and never for one with it off.
- QC still rejects a buzzword-laden draft and a fabricated URL with the new structure in place.

---

### PHASE 12 — Interest Capture & Instant Alerting

**Goal:** let a lead answer *"are you interested?"* in **one click**, and put that answer in front of
the operator immediately — with an identifier they can actually use to find the lead.

**Why this is the highest-value single addition in the block:** every engagement signal the system has
today is *inferred* — an open, a click, a repeat open (Phase 9 Step 9.4 escalates on three). A Yes click
is **declared**. It is the first first-party statement of intent this product has ever been able to
collect, and it costs the lead no effort at all, which is exactly why it will convert where a written
reply does not.

**Step 12.1 — Human-readable lead reference.** New `leads.reference_code` — a short, stable,
operator-quotable code (the raw UUID `Lead.id` is correct for machines and useless in an alert message).
Backfilled for existing leads; shown on the lead page and in every alert.

**Step 12.2 — Signed one-click endpoints.** New public routes (same unauthenticated surface class as the
existing one-click unsubscribe, `Config.PUBLIC_BASE_URL`) carrying an **HMAC-signed token** over
`lead_id + outreach_log_id + response`, signed with a secret from `.env`. Deliberately no token table:
signing makes the link tamper-evident without new storage, and forging one requires the secret.
A bad, expired, or altered token is **refused outright** — never partially trusted, never resolved to a
"probably this lead" guess.

**Step 12.3 — Record the response.** New Table 29 `interest_responses` with a UNIQUE constraint on
(`outreach_log_id`, `response`) — which is what makes a double-click, a mail-scanner prefetch, or a
browser retry **idempotent at the database level** rather than in application logic. Same posture as
`inbound_conversations`' own dedup constraint (Step 4.1), for the same reason.

**Step 12.4 — CRM state change.** A Yes routes the lead through the **existing** escalation path — the
same `HOT_LEAD` transition Phase 9 Step 9.4 already uses for repeated opens — and logs an `agent_events`
row. Deliberately not a parallel status system: the operator already has one place where "leads needing
attention" appear, and a second one would split their attention.

**Step 12.5 — Admin alert.** Reuses `send_internal_email()` (Step 4.5, already used by Phase 6's stuck
alerts) and adds an optional WhatsApp admin alert. Configurable from Settings (email / WhatsApp / both).
Rate-limited on the same principle as the stuck alerts: one alert per real event, never one per tick.

**Step 12.6 — "No" handling.** A No stops further follow-ups for that lead+product and is recorded — but
is deliberately **not** written to the suppression list. Declining one pitch is not a legal opt-out, and
conflating the two would silently and permanently destroy contactability that the lead never revoked.
The unsubscribe link remains the only path into suppression, exactly as today.

**DoD tests (gate):**
- A real Yes click updates the lead **and** sends exactly one admin alert, and the reference code in
  that alert resolves to that same lead in the CRM.
- Clicking the same link twice records once and alerts once — proven against the real DB constraint.
- A tampered or forged token is refused; no partial trust, no fallback lookup by lead id alone.
- A No stops the sequence, appears in the CRM, and the lead's contact details are **still not in the
  suppression list** (verified directly, since this is the failure that would be invisible until the
  operator tried to contact them again).
- With no outreach ever sent to a lead, no interest route can be constructed for it at all.

---

### PHASE 13 — Level-Aware Follow-Up Content

**Goal:** make the three follow-up touches **three different conversations**, not the same nudge with
different delays.

**Why the existing cadence engine is kept as-is:** Phase 9 Step 9.3 already proved the hard parts under
its own gate — configurable per-product delays, atomic claim under concurrency (no duplicate touch),
and reply/opt-out exit *at every touch, not just the first*. That machinery is not the problem. The
problem is that every touch currently receives the same instruction (`is_followup=True` → "write a short
nudge"), so touch 2 and touch 3 differ only by timing and LLM variance.

**Step 13.1 — Level-aware drafting.** The single `is_followup` boolean is replaced by an explicit
`followup_level` (1/2/3), each with its own stated communicative goal:
- **Level 1 — re-present with the asset.** If the first touch carried a video, lead with it; if not,
  lead with the pain point and the solution. The premise is that the first email was skimmed, not read.
- **Level 2 — ask an open question.** *"Did you get a chance to look? Anything you'd want to ask?"* —
  the goal is a reply, not another pitch.
- **Level 3 — a standing offer, not a chase.** Our contact details plus the real list of products and
  services as bullets, closing with an explicit "if you ever need this in future, here we are." This is
  the touch that must not read as pressure, because it is the last one.

Every level renders through Phase 11's section engine, so all three are designed HTML, not plain text —
and every level carries the demo CTA **when a real demo asset exists** (the Phase 8 rule: present when
available, silently dropped when not, never fabricated).

**Step 13.2 — Per-level WhatsApp templates.** New `whatsapp_templates.followup_level` so a level can
resolve its own approved template. The AI template-drafting loop (Step 9.6) is the mechanism for
producing them — AI drafts, QC gates, a human approves, Meta approves. Until a level's template is
genuinely approved, that level's WhatsApp touch is **skipped, never substituted with another level's
template** — sending the wrong pre-approved text is worse than sending nothing.

**Step 13.3 — Per-level measurement.** Each level's `OutreachLog.variant_id` records the level, so
Step 9.2's existing rollup answers "which level actually earns replies" from real SQL, with no new
counter. Without this the block ships three new behaviours and no way to know which one works — the
exact failure §5A.0's measurement-before-adaptation rule exists to prevent.

**Step 13.4 — Trigger on view-without-reply.** A lead who opened but never replied is a legitimate
follow-up trigger (the operator's own framing). This reuses the real `open_count`/`read_at` signal
already tracked (Phase 9 Step 9.4), and stays subject to the same autonomous-outreach kill-switch and
daily pacing caps as every other send.

**DoD tests (gate):**
- The three levels produce **provably different real output** for the same lead — verified from real
  LLM output, not from reading the prompt.
- No level fires before its configured delay.
- Reply, opt-out, **and** a Phase 12 interest response each exit the sequence at levels 2 and 3, not
  only at level 1 — Step 9.3's own tests re-run at every level.
- A level whose WhatsApp template is not approved sends nothing on WhatsApp and never falls back to a
  different level's template.
- Per-level sent/seen/replied reconciles against a direct SQL query.

---

### PHASE 14 — Conversation Transparency & Cross-Channel Reuse

**Goal:** make the lead page tell the operator **what actually happened and what happens next**, and let
them carry the same message to any channel by hand.

**Why these two land in one phase:** both are `LeadDetail.jsx` work on the same conversation panel, and
both read from the same source — Phase 11's stored `content_sections`. Splitting them would mean
rebuilding the same screen twice in consecutive phases.

**Step 14.1 — Per-message delivery status.** Each message in the conversation shows its real state —
Delivered / Seen / Replied / Failed — derived from data that already exists (`OutreachLog.status`,
`provider_message_id`, `read_at`, `open_count`, and `inbound_conversations`). **Nothing new is
collected;** this is purely surfacing tracking that has been running since Phase 3's Seen pipeline.
Where a channel genuinely cannot report a state, it reads `—`, never an optimistic guess — the same
rule the EOD report already applies to `spam_rate`.

**Step 14.2 — Real WhatsApp message text.** The conversation currently shows the template *name* for
WhatsApp sends. The real filled-in text is already stored in `OutreachLog.message_body` — show that.
The template name moves to secondary metadata, where it is useful for debugging and useless to a person
reading a conversation.

**Step 14.3 — Follow-up stage indicator.** Where this lead is in its sequence — first touch sent, level 1
done, level 2 scheduled for a real date, or ended and *why* (replied / opted out / said no / exhausted).
Read from `outreach_sequences`, which already holds all of it.

**Step 14.4 — Cross-channel copy (Item 15).** Platform icons on the lead page (Email / WhatsApp /
Instagram / Facebook / LinkedIn) copy **that lead's real outreach content**, rendered for that platform:
HTML for email, platform-appropriate plain text elsewhere (URLs as full links since buttons do not exist
outside email; the video as a labelled link; the contact block condensed).

**One canonical content object, many renderings** — the platform text is derived from the *same stored*
`content_sections` the real email was rendered from, never regenerated by a second LLM call. Two
reasons, both real: a regenerated message drifts from what the lead already received (so a follow-up on
Instagram would contradict the email), and a second generation is a second spend for content that
already exists.

**Step 14.5 — Still no auto-send.** This extends Step 10.3(a)'s human-send queue and inherits its hard
rule unchanged: the operator copies and sends manually. No code path on those platforms sends anything,
and P10's verify-by-absence check is re-run here rather than assumed to still hold.

**DoD tests (gate):**
- Per-message status matches a direct SQL query of `outreach_logs`/`inbound_conversations` for a real
  message on each channel.
- A real WhatsApp message displays its real filled-in text, never the template name.
- The follow-up stage shown matches the real `outreach_sequences` row, including the terminal reason.
- Copy-to-platform yields the **same core content** as the email that was really sent — verified by
  comparing against the stored `content_sections`, not by reading the two and judging them similar.
- Re-run P10's absence check: no code path can auto-send on LinkedIn/IG/FB.

---

### PHASE 15 — Person-Level Relevance & Prospect Sourcing

**Goal:** reach a person who can actually **judge** the pitch — and be able to find such people even
when there is no company lead at all.

**The real failure this fixes**, in the operator's own example: pitching AI automation to a company's
CEO or HR contact, when the person who can evaluate it is an engineer. The message can be perfect and
still fail, because it reached someone with no basis to assess it. Phase 7 built the machinery for
person-level discovery (Step 7.5, role-targeted LinkedIn lookup, gated on `products.target_person_roles`)
and proved its safety gate (zero wrong-company attachments). What it does not do is decide *which role
is the right one for this product*.

**Step 15(A).1 — Product-relevant role inference.** For a product whose brief implies technical
evaluation, the relevant role is inferred **from the product brief itself** and constrained by the
operator's own `target_person_roles` when set. §16.2's boundary rule holds exactly as before: the human
sets the boundary, the AI matches inside it — it may not invent a role outside a non-empty list.

**Step 15(A).2 — Multiple relevant people per company.** `lead_contacts` (Table 21) already supports
many people per lead with role, seniority, decision-maker flag and **source**. This populates it with
several genuinely relevant people rather than one, each with its source and confidence shown honestly
(a low-confidence guess must never render like a verified contact — the UI half of P7's gate).

**Step 15(A).3 — Manual outreach to those people.** Deliberately manual for now, per the operator:
their contact details are surfaced so a human can reach out. No automatic sending to a person-level
contact in this phase — the "zero wrong-company attachments" guarantee is proven for *attachment*, and
autonomously messaging an individual employee is a different and higher-consequence action than
messaging a business.

**Step 15(B).1 — Standalone prospect finder.** A search independent of the discovery pipeline: criteria
like *"AI developer in Mehsana, 3 years experience"* → real matching people. New Table 30 `prospects`
(person-level, no parent lead) — deliberately **not** synthetic rows in `leads`, which would corrupt
every funnel metric the analytics layer computes with people who never went through discovery, scoring,
or ICP matching.

**Step 15(B).2 — Provider integration + hard spend cap.** Apollo.io or an equivalent, behind the same
provider-abstraction shape as `services/data_acquisition/`'s existing Serper/Hunter providers. New Table
31 `prospect_searches` records criteria, provider, result count and **real spend per run**, and a
configured cap **blocks** the next search rather than warning after the fact. This is a direct lesson
from real history: Hunter's quota hit 0/50 mid-verification and cost this project a full DoD check
(tracker.md Phase 7 gate) — a note in a document did not prevent it, so this one is enforced in code.

**Step 15(B).3 — Contact enrichment for prospects.** Email/phone lookup for a found prospect reuses the
existing enrichment waterfall rather than a parallel one, so suppression, normalization
(`phone_utils.normalize_phone` with a real country hint) and the idempotency guarantee proven on
2026-08-22 all apply unchanged.

**DoD tests (gate) — 15(A) and 15(B) gate independently:**
- 15(A): a person is attached only on a real company match — **zero wrong-company attachments**, P7's
  exact test re-run, not assumed still passing.
- 15(A): with `target_person_roles` set, no role outside that list is ever targeted; with it unset, the
  inferred role is traceable to a real line in the product brief.
- 15(B): with no provider configured, the finder **refuses** — it must not return an empty result set
  that is indistinguishable from a real search that found nobody.
- 15(B): the configured spend cap genuinely blocks the next search, proven by running into it — not by
  reading the code.
- 15(B): a prospect never appears in the leads funnel or any pipeline metric.
- No autonomous send to a person-level contact or prospect exists in this phase — verified by absence.

---

## 5C. Add-on phase plan (Phases 16–19) — added 2026-09-01

**Origin.** The operator showed the live, 15-phase system to their boss. The boss's real verdict:
*"this is automation, not AI — it never decides anything itself,"* the built system is maybe 20% of the
original vision, the pipeline/Kanban view isn't the right primary view, and the email/WhatsApp copy is
generic enough that nobody remembers it. The operator then spent a full session (2026-08-26 through
2026-09-01) turning that verdict into a scoped design, first with ChatGPT, then in direct discussion here
(captured raw in `discussion.md`), then cross-checked against a dedicated architecture consultation
(`suggest.txt`). §5C formalizes the result of that process into the same step + DoD-gate structure every
other phase in this document uses.

**What this block deliberately is not.** Nowhere in this section does the AI rewrite its own prompts,
retrain itself, or take an action a human never approved. Every one of Phases 16–19 follows the exact
governance shape the operator converged on after several rounds of clarification in `discussion.md`: **AI
proposes the strategy, drafts the content, and writes down what it learned; a human reviews and approves
before anything reaches a real business.** A fully self-modifying, unsupervised learning loop was
considered and explicitly rejected — real B2B outreach data is slow (a reply can land three days later)
and this project's own daily send caps keep sample sizes small, so a system that rewrote its own behavior
without review would drift on noise, not signal. The one invariant that stays completely untouched by
this whole block is Phase 4/12's **immediate human escalation on a genuinely hot reply** — nothing here
ever makes a hot lead wait for a daily cycle.

### 5C.0 Sequencing logic (read this before reordering anything)

The order is forced by four real dependencies, same discipline as §5A.0/§5B.0:

1. **The conversation itself is the most visible complaint, and it needs nothing built first.** The
   boss's sharpest single line was that replies are generic and forgettable. Phase 16 (Conversation Engine
   + Knowledge Base) fixes exactly that, and it can ship against the existing lead/product/outreach tables
   as they are today — no new grouping concept required. It goes first because it's both the highest-value
   fix and the one with zero upstream dependency.
2. **A campaign is a grouping layer, and grouping needs something to group.** Phase 17 (Campaign Entity &
   Calendar) sits *around* Phase 16's richer conversations and the existing discovery/outreach pipeline —
   it cannot usefully exist before there is something worth grouping and dating.
3. **A daily review loop needs something to review.** Phase 18 (Daily AI-Plan / Human-Review Loop) proposes
   and dispatches *campaigns* every morning — it is meaningless before Phase 17's `campaigns` table and
   calendar UI exist to hold what gets proposed.
4. **Reflection needs real telemetry, and real telemetry needs real days to have happened.** Phase 19
   (Strategy Reflection Engine) reads back outcome data grouped by campaign/segment/angle. Building it
   before Phases 16–18 ran for real would give it nothing genuine to learn from — the exact trap this
   project already avoided once by putting Phase 15(B)'s new paid provider last (§5B.0, point 4). This is
   the same lesson applied to time instead of money: **this project sends roughly 40 email + 40 WhatsApp
   messages a day across every product combined, so one specific segment+angle combination can easily take
   weeks to reach a sample size worth reflecting on.** Phase 19 is specified to fail closed on that — see
   Step 19.2.

**Relationship to the existing per-product targeting system.** This is the one integration question the
architecture consultation (`suggest.txt`) did not answer, and it needs an explicit decision here: a
**campaign does not replace or duplicate** `products.target_regions` / `target_business_categories` /
`target_person_roles`, or the existing ICP Strategy Agent that already re-infers an ICP every 7 days
(`product_strategies`, consumed since Phase 15(A)) — those keep governing the always-on discovery
pipeline exactly as they do today. A campaign's `target_segment` is a **separate, deliberately
unconstrained** decision layered on top: set directly by a human when the campaign is created, or (once
Phase 18 exists) proposed by the AI planner from real strategy reasoning — in neither case validated
against the product's existing targeting fields. **Revision, 2026-09-01**: an earlier draft of this
section required `target_segment` to resolve inside those existing fields; the operator explicitly
rejected that constraint — a campaign is allowed to genuinely explore a new region, category, or angle
the product's standing configuration doesn't cover, because oversight here comes from the human
review/approval step (§18.4), not from a schema-level restriction. Step 17.2 (below) reflects this.

**Revision, 2026-09-02 — discovery becomes campaign-gated, superseding the "always-on... exactly as they do
today" sentence above.** The operator's own mental model, given directly while building this: *"campaign
banega tab discovery ko campaign id milegi... jab tak koi campaign nahi banega tab tak lead nahi aayenge"*
— a campaign is meant to be the trigger for new-lead discovery, not an optional grouping bolted onto a
pipeline that runs regardless. This is a deliberate, explicit change from the paragraph above (kept, not
deleted, so the reasoning that was later overridden stays legible): the always-on, continuous,
cooldown-paced discovery tick (§3 Step 3.5) now only fires for a product when that product has at least one
`campaigns` row in an active status (`PROPOSED`/`APPROVED`/`RUNNING`) — see Step 17.6 (superseded same day
by 17.7 below). `products.target_regions`
/ `target_business_categories` and the ICP Strategy Agent's own query generation are UNCHANGED and still
define *what* gets searched; only *whether* the search runs at all is now gated on campaign existence.

**Revision, same day, 2026-09-02 — WHAT gets searched changes too, not just whether (see Step 17.7).** The
operator went further: *"discovery bhi campaign specific hogi campaign id ke saath, isliye ye lead ki
campaign ki hai wo pata chale... hum pipeline ke basis par nahi ab campaign ke basis par kaam kar rahe
hain."* The sentence just above (product-level targeting still defines what gets searched) is superseded --
each active campaign's OWN `target_segment` now defines what it searches for, not the product's standing
config. `products.target_regions`/`target_business_categories` and the ICP Strategy Agent keep existing
(Products page still shows them; a campaign's own kickoff proposal, Step 18.1, still reads them as a
helpful prior) but no longer drive the real-time search themselves.

Existing leads already in the pipeline (any status, any product, tagged to a campaign or not) are completely
unaffected — follow-ups, replies, hot-lead escalation, scoring, and every other Phase 1-15 mechanism keeps
running exactly as before regardless of any campaign's current state (Step 18.5's "hot-lead escalation stays
completely outside this loop" principle extends to all of these, not just Phase 18's own loop).

### 5C.1 New data-layer objects introduced across Phases 16–19

Phases 16–19 add Tables **32–34 (total 34)**, plus one column on `leads`. No table introduced in §5, §5A or
§5B is altered in shape — this block only adds.

| # | Table | Phase | Purpose |
|---|-------|-------|---------|
| 32 | `knowledge_base_items` | 16 | one consolidated table for product facts, objection answers, real proof and (Step 16.8) approved marketing assets — a `kind` column (`FACT` / `OBJECTION` / `PROOF` / `MARKETING_ASSET`) distinguishes them rather than four separate tables, matching this project's existing preference for the leanest schema that carries the real information (the same call already made for `prospects`/`prospect_searches` in §5B) |
| 33 | `campaigns` | 17 | one row per dated, strategy-angled grouping — name, `scheduled_date`, `target_segment` (JSON, human-set at creation or AI-proposed via Step 18.1's daily strategist once discovery activity is zero — deliberately not constrained to the product's existing targeting fields, per §5C.0's 2026-09-01 revision), `strategy_angle`, lifecycle `status`, `lead_count_goal` (int, nullable — Step 18.1/17.6, the AI-proposed target this campaign's discovery batch stops at, raisable by a later proposal), AI-generated `daily_todo` (JSON, open-ended real items — see Step 18.1), `last_approved_date`, and a `metrics_summary` cache (JSON) that Step 17.3 requires stay recomputable from real logs, never authoritative on its own |
| 34 | `strategy_insights` | 19 | one row per learned strategy rule, grouped by `(product_id, domain)` and pooled across every real campaign that targeted that domain — `domain` text, `winning_angle`/`losing_angle` (simplified 2026-09-02 from a 4-field spec that also had a separate `winning_tone`: this project's `Campaign` model has no tone axis distinct from `strategy_angle`, so a second column would only restate the first), a `confidence` float, a `rationale` grounded in the real numbers that produced it, and a `status` (`ACTIVE` / `SUPERSEDED`) — this reuses the **exact** "most recent ACTIVE row wins" pattern already proven in `product_strategies` (consumed by Phase 15(A)'s `_enrich_person_roles`), not a new pattern |

New column: `leads.campaign_id`, nullable FK → `campaigns.id`. Nullable is load-bearing, not incidental —
every lead the existing discovery pipeline creates outside a campaign context must keep behaving
byte-identically to today (Step 17.1's DoD).

**Two things this block deliberately does NOT add a table for**, same discipline as §5B.1:
- **Knowledge-base coverage gaps** (Step 16.7) log a `KB_GAP_DETECTED` row to the existing `agent_events`
  table (Phase 6) rather than a new one — this is exactly the kind of observability event that table
  already exists to hold.
- **A newly AI-drafted WhatsApp template's approval state** reuses the approval-status tracking Phase 9
  Step 9.6 already built for the autonomous template-creation-and-approval loop — Step 16.6 surfaces that
  existing state in the daily to-do, it does not invent a second one.

---

### PHASE 16 — Persuasive Conversation Engine & Knowledge Base

**Goal:** make a reply that a lead actually wants to keep reading — grounded, specific, and adapted to who
it's talking to — while keeping the zero-hallucination guarantee Chapters 16/17 already established
completely intact.

**Why today's reply reads "flat".** It's flat on purpose. `agents/outreach_agent.py`'s reply-drafting rule
is deliberately conservative: write only from verified `pain_points` + `product_brief`, never commit to a
number or a date the operator hasn't set, and close with the same safe line every time. That was the right
call to avoid inventing facts — but it also means the AI has almost nothing *specific* to say back with,
so every reply sounds like every other reply. The fix is not to loosen the safety rule; it's to give the
AI a real, bounded, admin-authored body of specific things it's actually allowed to say.

**Step 16.1 — Knowledge base schema & admin UI.** New Table 32 `knowledge_base_items`
(`product_id`, `kind` ∈ `{FACT, OBJECTION, PROOF}`, `title`, `body`, timestamps). A new Settings/Products
sub-tab lets the operator add/edit rows per product — plain text in, plain text out, no LLM in the loop at
write time.

**Step 16.2 — Zero-fabricated-content rule, enforced not just stated.** Every row in
`knowledge_base_items` must be operator-authored. Nothing seeds this table with AI-generated placeholder
content, ever — not even a "starter example." This is a direct, deliberate correction of the architecture
consultation's own illustrative examples (`suggest.txt` used an invented Ahmedabad testimonial to explain
the *shape* of a proof entry — that string itself must never become a real database row). The write path
has no code route that inserts a `knowledge_base_items` row from an LLM call; only the admin-facing API
does.

**Step 16.3 — 3-step reply structure.** The reply-drafting prompt (extends the existing grounded-drafting
rule in `agents/inbound_agent.py`) is restructured into **Mirror & Validate → one concrete insight pulled
from `knowledge_base_items` → a low-friction, situation-specific next step** — replacing the current single
mandatory closing line with a set of context-appropriate soft CTAs. Every fact used in step 2 must trace to
a real `knowledge_base_items` row or the existing `pain_points`/`product_brief` grounding; nothing new is
invented at generation time. The existing zero-hallucination validation gate is extended, not replaced.

**Step 16.4 — Format & tone directives, generated not fixed.** Phase 11's `sections` contract
(`draft_email()`'s `HOOK`/`PAIN_POINTS`/`SOLUTION`/... blocks) gains two optional directives —
`format_directive` (e.g. HTML+bullets vs. short plain text) and `tone_directive` (e.g. formal/ROI-driven
vs. casual/emotional) — sourced from the active campaign's `strategy_angle` once Phase 17 exists, falling
back to a per-product default before that. The same underlying fact set can render as a 3-bullet formal
HTML email to one segment and a 2-line casual WhatsApp message to another — the fact stays fixed, the
presentation adapts.

**Step 16.5 — Conversational template revision.** A human reviewing any AI-drafted preview (email or
WhatsApp) can submit a free-text instruction — *"isko formal karo"*, *"ek bullet ROI ka add karo"* — which
reuses the existing draft-then-QC pipeline to regenerate that one draft. The regenerated draft still passes
through the unchanged QC veto (Step 11.6) before it can be marked approved. After regenerating, the AI adds
**one of its own suggestions** for a further improvement (never auto-applied, always a separate proposal
the human can accept or ignore) — this is the concrete mechanism behind "AI reviews, human decides, AI
suggests back."

**Step 16.6 — WhatsApp new-variant approval flag.** Any time Step 16.4/16.5 produces a WhatsApp template
variant that has not yet reached the approved state Phase 9 Step 9.6 already tracks, it is surfaced as a
to-do item rather than silently blocked or silently sent — "this is a new template, get it approved first"
— so an operator never discovers a missing approval by way of a failed real send.

**Step 16.7 — Knowledge-base coverage-gap detector.** When `jobs/inbound_classify_handler.py` classifies a
real reply as an objection/question with no matching `knowledge_base_items` row to ground an answer in
(confidence below the grounding threshold), it logs a `KB_GAP_DETECTED` event to the existing
`agent_events` table — product id, a short description of the unanswered question, and how many real leads
have hit it. This is read by Phase 19's reflection engine to produce the "you're missing a demo video for
this objection" class of to-do; Phase 16 only detects and logs, it does not yet act on the gap.

**Step 16.8 — Marketing content creation (outreach copy + demo-video scripts), AI-strategy-triggered.**
This is where Step 16.7's gap detection stops being passive. `knowledge_base_items` gains a fourth `kind`,
`MARKETING_ASSET` — a longer-form, campaign-grade piece (persuasive outreach copy, or a demo-video
script/storyboard, never a full generated video: no video-generation provider is added by this step, the
same "new paid provider needs its own explicit decision" discipline §5B.0/§5C.0 already establish). The
trigger is not a human clicking "generate" and not a fixed schedule — it is the AI's own judgment, made
from real signals exactly like Step 16.7's and Phase 19's: a product whose `knowledge_base_items` is thin
on `PROOF`/`MARKETING_ASSET` rows, or whose real reply/conversion rate is trailing its peers (once Phase 19
has enough telemetry to say so), is proposed as needing new content — surfaced as a `MARKETING_CONTENT_GAP`
item in Step 18.1's daily to-do, the same mechanism Step 18.1 was already written to be extensible for
("any further types a real insight motivates"). A human can redirect it with a free-text prompt through the
exact Step 16.5 revision mechanism ("make it more energetic", "lead with the ROI number") before approving.

**The creative bar is explicit, and so is its boundary.** The operator's own requirement is that this
content must never read as generic, templated AI copy — it has to be distinctive enough to out-perform
whatever a competitor is likely sending. That bar governs **execution only**: angle, hook, structure,
pacing, the shape of the story. It does not license a second fact source. Every claim inside a marketing
asset must still trace to `product_brief`/`pain_points`/existing `knowledge_base_items` — Step 16.2's
zero-fabrication rule is not loosened for this step, and this step deliberately adds **no competitor-
research capability**: "beat the competition" is scoped as a creative-quality target the AI is instructed
to aim for, never a claim about a specific named competitor the system has no real data on.

**Approval writes to the knowledge base — but only through the existing admin write path.** A human
reviewing a drafted marketing asset can approve it, and approval is what performs the actual
`knowledge_base_items` insert (`kind=MARKETING_ASSET`) — routed through the same admin-facing write API
Step 16.2 already restricts writes to. The LLM itself never inserts a row directly; it only produces a
draft that sits pending until a human's approval action writes it. This keeps Step 16.2's invariant
("zero rows trace to an LLM write path") true under this new capability rather than carving an exception
into it. Once saved, the asset is real, reusable grounding — future outreach (Step 16.3) and future
reflection (Phase 19) can cite it exactly like any admin-typed row, because by the time it's citable, a
human made it real.

**DoD tests (gate):**
- Zero rows in `knowledge_base_items` trace to an LLM call rather than the admin-write API — verified by
  absence of any non-admin write path, not by inspecting existing rows.
- Two real leads in different segments produce **provably different** rendered format/tone for the same
  underlying product fact — checked against the real rendered HTML/WhatsApp text, not the prompt that
  asked for it.
- A real free-text edit prompt changes only what was asked, and the regenerated draft still fails QC when
  it should (QC re-run with a deliberately bad instruction) — the veto stays absolute under the new path.
- A new, not-yet-approved WhatsApp variant is surfaced as a to-do and **cannot be dispatched** until it
  reaches the approval state Phase 9.6 already defines.
- A real unanswered objection produces exactly one `KB_GAP_DETECTED` event, not a fabricated "grounded"
  answer that only looks specific.
- A drafted `MARKETING_ASSET` (outreach copy or demo-video script) contains zero claim that doesn't trace
  to real `product_brief`/`pain_points`/existing `knowledge_base_items` grounding — checked against the
  real generated artifact, not the prompt that requested it.
- A `MARKETING_ASSET` row in `knowledge_base_items` exists **only** after a real human approval action —
  verified by absence of any path where an LLM call writes one directly.

---

### PHASE 17 — Campaign Entity & Calendar Grouping Layer

**Goal:** give the operator a date-based view of "what is running and how is it doing" without inventing a
second targeting system or disturbing anything Phases 1–15 already proved.

**Why a grouping layer, not a rewrite.** The boss's second complaint was the primary view itself — pipeline
Kanban shows "which stage is this lead in," never "what campaign is running today and how is it going."
Rebuilding targeting/discovery/outreach around a new `campaigns` concept would risk the exact thing this
project's own history warns against (§5B.0's "don't re-solve a solved problem"). Instead, Phase 17 wraps a
thin, dated, strategy-angled grouping around the existing pipeline.

**Step 17.1 — `campaigns` table + `leads.campaign_id`.** New Table 33 `campaigns`
(see §5C.1) and a nullable `leads.campaign_id`. *(Note, 2026-09-02: the sentence that used to stand here —
"every lead created today keeps campaign_id null and behaves exactly as it does today, whether or not a
campaign is active" — is superseded by Step 17.7 below: discovery itself is now campaign-DRIVEN, so a
newly-discovered lead's `campaign_id` comes directly from the `DISCOVER` job that found it, deterministic,
never guessed. `campaign_id` stays nullable and a null value still behaves identically to today for any
lead that has one (a manually-added lead with no campaign context, or a legacy row) — nothing about a
lead's own lifecycle changed, only whether/how new leads get created and tagged did.)*

**Step 17.2 — `target_segment` is a free, campaign-owned decision, not a validated subset.**
*(Revised 2026-09-01 — see §5C.0.)* A campaign's `target_segment` (JSON, e.g.
`{"industry": "...", "location": "...", "size": "..."}`) is set directly by whoever creates the
campaign — a human today, an AI proposal once Phase 18's planner exists — and is **not** checked against
that product's `target_regions`/`target_business_categories`/`target_person_roles`. A campaign is allowed
to genuinely explore a region, category, or angle the product's standing configuration doesn't cover;
the always-on discovery pipeline's own targeting is untouched either way (Step 17.1's isolation already
guarantees that). Oversight on a campaign's target_segment comes from the human review/approval step
(§18.4's daily loop), not a creation-time schema check.

**Step 17.3 — Calendar data contract.** Each day's per-campaign metrics (`sent`/`opened`/`replied`/`hot`)
are computed live from `outreach_logs` and `leads` joined through `campaign_id` — the `metrics_summary`
cache column exists purely for calendar-view read performance and must be recomputable from those same
real tables at any time, never the source of truth on its own.

**Step 17.4 — Calendar becomes the primary view; Kanban is removed.** *(Revised 2026-09-01 — the operator
explicitly asked for the grid to be removed, not demoted, once the calendar existed: "wo pipeline wala
kanban grid hatadena.")* Paired 1:1 with CRM_UI_UX_PLAN's UI Phase 16: the month/day calendar (one box
per day, campaign name + live metric chips) replaces `PipelineKanban` as the Dashboard's primary view —
`Dashboard.jsx`'s Pipeline section (the Kanban itself plus its product/tier/date filter row) is removed
entirely. Nothing about "which lead is in which stage" is actually lost: the existing Leads page already
has its own independent status column, badge, and filter (`Leads.jsx`, untouched), so lead-stage
visibility survives on a different, already-real screen. `PipelineKanban.jsx`/`LeadCard.jsx` stay on disk
as dead code rather than being deleted, matching this project's standing "dead code kept, not
unilaterally removed" precedent (§A, `MessageFormatPanel.jsx`).

**Step 17.5 — Campaign lifecycle.** `status` ∈ `{PROPOSED, APPROVED, RUNNING, COMPLETED, PAUSED}`.
`PROPOSED`→`APPROVED` only happens through Phase 18's human review action (never automatically); pausing or
completing a campaign only changes its own row and never deletes, reassigns, or orphans the leads already
tagged with its `campaign_id` — those leads simply stop receiving new campaign-driven touches and continue
to exist in the pipeline exactly as any other lead does.

**Step 17.6 — Campaign-gated, bounded Discovery.** *(New, 2026-09-02 — see §5C.0's revision note. Superseded
the same day by Step 17.7 below — kept here, not deleted, so the intermediate reasoning stays legible.)*
This first pass added a per-product GATE (skip a product entirely unless it has ≥1 active campaign) and a
per-campaign BOUND (`lead_count_goal`), layered on top of the *existing* product-wide query×region search.
Its real gap, found the same day: with 2+ active campaigns for one product, the gate let discovery run but
`resolve_auto_campaign_id()` couldn't say which campaign a new lead belonged to, so it landed
`campaign_id = NULL` — an orphaned lead. The operator's own correction: *"discovery bhi campaign specific
hogi campaign id ke saath"* — every lead must be campaign-linked from the moment it's created, and Leads
becomes a secondary/detail view, not the primary way work gets browsed (Campaign Calendar → one campaign's
own leads + progress is). Step 17.7 is the real fix.

**Step 17.7 — Discovery is campaign-DRIVEN, not just campaign-gated.** *(New, 2026-09-02.)* Reworks
`_run_discovery_tick()` (§3 Step 3.5) so each active campaign with a real `target_segment` runs its **own**
search, using its **own** `target_segment.industry` as the query and `target_segment.location` as the
region — not the product's standing `target_regions`/ICP-Strategy-Agent queries, which stay defined and
unused by this tick (Products page's own strategy tab still reads them directly; dead-code-kept, not
deleted — same precedent as `PipelineKanban.jsx`). Concretely:
- `services/campaign_service.py`'s new `eligible_campaigns_for_discovery(db, product_id)` replaces Step
  17.6's single yes/no gate with a **list** of this product's active campaigns that (a) have both
  `target_segment.industry` and `.location` set, and (b) haven't hit their own `lead_count_goal` yet (no
  goal = no bound). Each eligible campaign gets its own `DISCOVER` job this tick, budget permitting.
- The `DISCOVER` job payload itself now carries `campaign_id` (`{product_id, campaign_id, query, location}`).
  `scraper_worker/async_runner.py`'s `_handle_discover()` tags every lead it creates directly from that
  field — **deterministic, not guessed** — `resolve_auto_campaign_id()` stays only as the fallback for a
  job with no `campaign_id` (a manually-enqueued or legacy job).
- This is what actually resolves Step 17.6's 2+-campaigns gap: there is no ambiguity to resolve, because
  there is no longer one shared search to attribute — each campaign runs independently and every lead it
  finds is unambiguously its own by construction.
- Cooldown tracking (`discovery_runs`) moves from `(product_id, query, region)` to also carrying
  `campaign_id`, so two campaigns sharing a query/region never share one clock, and a campaign whose target
  changes later (a strategy-refinement proposal, Step 18.1) starts a fresh cooldown for its new pair rather
  than inheriting the old one's timer.

Existing dedup (`(product_id, company_name)`, `scraper_worker/async_runner.py`) is untouched and still
prevents the same business being created twice for a product, regardless of which campaign found it.

**DoD tests (gate):**
- With zero campaigns ever active for a product, no `DISCOVER` job fires for that product on a real tick.
- Two campaigns active for the SAME product, each with a real, different `target_segment`, each fire their
  **own** `DISCOVER` job this tick with their own query/location — verified against real enqueued job
  payloads, not assumed from the eligibility list alone.
- A lead created by a real `DISCOVER` job carries the `campaign_id` from that exact job's payload — checked
  directly, not inferred from `resolve_auto_campaign_id()` running afterward.
- A campaign with an empty or half-set `target_segment` (only industry, or only location) fires no
  `DISCOVER` job for itself, while a sibling campaign for the same product with a complete target still
  fires normally.
- A campaign's own `lead_count_goal`, once reached, stops firing for that campaign specifically, while a
  sibling campaign for the same product with room left keeps firing.
- Existing leads (any status, tagged to a campaign or not) are provably unaffected by any campaign's
  current state — re-run of the relevant P2/P3/P9 follow-up/escalation checks, not assumed still passing.
- A campaign's `target_segment` may freely name a region/category/angle outside the product's configured
  targeting fields (no validation blocks it) — and doing so **never writes back to or mutates**
  `products.target_regions`/`target_business_categories`/`target_person_roles`, verified by creating such
  a campaign and confirming the product's own targeting configuration is byte-identical afterward.
- Calendar metric chips for a real day reconcile exactly against direct SQL on `outreach_logs`/`leads` for
  that day — not the cached column read in isolation.
- Pausing/completing a campaign leaves every one of its tagged leads fully intact and still visible on the
  Leads page's own status filter (Kanban itself was removed, Step 17.4).

---

### PHASE 18 — Daily AI-Plan / Human-Review Loop

**Goal:** the AI plans the day's work and drafts its content; a human spends about two minutes approving or
redirecting it before anything real goes out — and a genuinely hot reply **never** waits for that cycle.

**Why a scheduled batch, not a chat.** The operator's own repeated clarification across `discussion.md` was
specific: AI builds the whole strategy, human only reviews/approves or gives feedback for AI to
incorporate — never the other way around, and never fully unattended either. A once-daily
generate-then-review checkpoint is the concrete shape of that governance rule; it reuses this project's
existing in-process scheduler pattern (`jobs/discovery_scheduler.py`, the documented n8n replacement noted
at the top of this file) rather than introducing a second scheduling mechanism.

**Step 18.1 — Daily strategist, open-ended (not a fixed to-do menu).** *(Revised 2026-09-01: this
originally said the job itself "writes a new PROPOSED campaign" — the operator corrected that mid-build, a
campaign is ALWAYS human-created, this job never creates one. Revised again 2026-09-02, a bigger correction:
an intermediate design modeled this as a one-time "kickoff" step separate from a fixed-type ongoing
generator — the operator corrected that too, directly: "isme koi boundary nahi ki AI kya sochega, kitna
sochega." There is no kickoff/ongoing split and no closed set of to-do types. One sentence governs this
whole step now: a scheduled job (`jobs/discovery_scheduler.py`'s `_run_daily_plan_tick()`) runs once per IST
day for every EXISTING, human-made, active campaign, and asks the AI — genuinely open-ended, like a real
sales manager reviewing the account fresh each morning — "what does today's real data say we should do
next?"* Gated by `DAILY_AI_LOOP_ENABLED` (Step 18.7).

**What "real data" means, concretely, and why day 1 looks different from day 20 — same mechanism, not two
paths.** The prompt is handed: this campaign's own real metrics and `daily_todo` history so far, any open
`KB_GAP_DETECTED` events (Step 16.7), AND — new, 2026-09-02 — a summary of every OTHER campaign (past or
active) for the SAME product: their `target_segment`, `strategy_angle`, and real sent/opened/replied/hot
counts (reusing the exact data `generate_campaign_suggestion()` already fetches for its own, narrower
purpose). A campaign with none of its own data yet and no sibling campaigns naturally has nothing to say but
targeting — which real business type(s), which region, and a `lead_count_goal` (Step 17.7) — written into
`target_segment` (Step 17.2's existing free-JSON field, previously unused by any prompt; this is what makes
it real). A campaign with real outcomes, or a same-product sibling with real outcomes, naturally has more to
say: a segment/region worth continuing or expanding into a fresh region, a channel that's outperforming, a
subject line or angle that's underperforming and should change, a new email/WhatsApp template worth
proposing (reusing Phase 9 Step 9.6's existing template-approval flow for WhatsApp specifically), a
follow-up push for leads showing engagement, a `lead_count_goal` raise once the current one is met and the
segment is still producing. **None of this is a fixed enum the AI picks from** — each item is a real,
specific sentence traceable to the actual numbers/history behind it, the same zero-fabrication discipline
every other prompt in this project already holds to; only the CONTENT is open, never the requirement that
it be true. Two different real days must produce genuinely different `daily_todo` content — this is the
literal mechanism behind "har din ka to-do fixed nahi hota."

**Architecture note — this is a system-level Manager delegating to workers, not an LLM that outputs
text and stops.** This step is the AI Sales Manager's "brain" — see
[[project_ai_sales_manager_persona_vision]]. Its decisions don't sit as a suggestion for a human to manually
carry out elsewhere: once approved (Step 18.4), they flow structurally into the existing job-queue/scheduler
machinery (§3, §5A) that already drives the specialist worker agents (Discovery, Enrich, Review, Score,
Outreach, QC) — the same "hath-pair" framing that memory entry establishes. The delegation glue is
deterministic Python (the job queue), not a second LLM call per handoff, and that is a deliberate choice,
not a shortfall — a heavier literal agent-to-agent framework is unneeded complexity for a well-bounded
pipeline. What matters, and what every DoD check below verifies, is that an approved decision provably
reaches a real worker action, not that a second AI reasons about making the call.

**Explicit non-lever, flagged rather than silently ignored.** A real insight this step can surface — e.g.
"email is outperforming WhatsApp for this campaign" — currently has no execution lever: outreach channel
selection (`_run_outreach_tick`) is generic capacity-based, not campaign-strategy-aware. Until a
campaign-level channel-preference field is built, this class of insight is informational only in the to-do
text, not yet something Approve can act on. Noted here so it is a known, tracked gap, not an accidental one.

**Step 18.2 — Morning review card.** *(As shipped, `DailyReviewPanel.jsx`.)* A dashboard card
surfaces each live campaign's to-do list, a sample email + WhatsApp draft preview, and two actions —
**Approve** or **Give Feedback**. Campaign `email_render_mode` (`HTML` default | `TEXT`) drives whether
the preview is the designed Phase-11 HTML iframe or plain subject/body, and the same mode governs
whether real sends attach designed `sections` or body-only simple HTML (2026-09-05).

**Step 18.1b — Kickoff template preview.** *(Built 2026-09-05.)* Before this, a brand-new campaign with
no lead tagged yet showed `sample_draft: null` on the review card — a human had nothing concrete to react
to until real discovery produced a lead. `ensure_kickoff_draft()`/`revise_kickoff_draft()`
(`services/campaign_service.py`) draft the SAME Step 11.1 structured email against literal
`[Business Name]`/`[Pain Point]` placeholder tokens instead of a real lead — the model is explicitly
instructed to keep those tokens verbatim and never invent a fictional business, city, or pain claim (same
zero-fabrication discipline as every other drafting prompt). Cached on `campaigns.kickoff_draft`
(cleared whenever `strategy_angle` or `email_render_mode` changes, so the next preview regenerates
against the fresh tone/format); revised via the existing Step 16.5 conversational mechanism through
`POST /campaigns/<id>/kickoff-draft/revise` (own route, reuses `check_instruction_pushback` — Step 20.4's
push-back applies here too). `get_daily_review()` returns `sample_is_kickoff_template: true` in this
case so the frontend captions it as a template, not a real worked example. Never queues a send, never
touches a real lead — purely a preview/proposal artifact a human reviews before any lead exists.

**Step 18.3 — Feedback regeneration.** *(As shipped.)* Feedback text re-runs the relevant draft/strategy
generator with the feedback appended as an additional constraint, reusing Step 16.5's exact
conversational-revision mechanism (`previous_draft_text` threading so a second round of feedback never
forgets the first).

**Step 18.4 — Approval acts differently depending on what was proposed, but always through existing
machinery, never a new path.** *(Un-deferred, 2026-09-02 — built as sign-off-only on 2026-09-01, reopened
after the operator clarified the fuller loop this section describes; this is this step's ORIGINAL intent,
not a new one.)*
- **Approving a targeting/`lead_count_goal` proposal** writes it onto the campaign's own row —
  `target_segment` and `lead_count_goal` — which Step 17.7's `eligible_campaigns_for_discovery()` reads
  directly; discovery for that campaign starts (or resumes, if the goal was raised) on the next tick, using
  this campaign's own target_segment as the search itself, not just as a gate.
- **Approving an angle/subject/tone change** writes the new text onto `campaign.strategy_angle`. This needs
  no separate propagation step: every future draft for this campaign's leads — a fresh touch-1 for a newly
  qualified lead, or a due follow-up touch for someone who already didn't reply — already resolves
  `tone_directive` as "this campaign's `strategy_angle`, falling back to the product's `default_tone`" at
  the moment it drafts (`jobs/outreach_handler.py`, fixed 2026-09-02 to match the pattern Step 16.5's
  revise-draft and this campaign's own daily-review sample draft already used). The new angle is live the
  next time anything is drafted, automatically, with no "resend everyone" action needed.
- **Approving a ready-to-send to-do** (qualified leads exist, template content is settled) queues those
  specific leads for a real send — reusing `services/lead_service.py`'s existing `claim_lead_for_outreach()`
  / `_run_outreach_tick()` machinery unchanged, no new send path. **This still passes through the existing,
  unmodified `AUTONOMOUS_OUTREACH_ENABLED` kill switch** ([[project_autonomous_outreach_kill_switch]]) — the
  switch itself is never flipped by any AI or Approve action. When a to-do is ready to dispatch but the
  switch is off, this is surfaced through the SAME open-ended strategist that writes every other to-do (Step
  18.1) — fed `READY_TO_DISPATCH_COUNT` (the real count of this campaign's SCORED HOT/WARM leads, the exact
  set `_run_outreach_tick()` would claim) and `AUTONOMOUS_OUTREACH_ENABLED`'s current value, and instructed
  to say so in its own words, grounded in the real number, when both signals apply — **never a fixed or
  generic system-banner sentence** (the operator's own explicit correction, 2026-09-02: *"ye ek generic
  hardcode nahi rahega... wo system ko pura control karega"*). Turning the switch on stays the operator's
  own explicit, manual Settings action either way, same as it is today.

**Step 18.5 — Hot-lead escalation stays completely outside this loop.** Phase 4's inbound classifier and
Phase 12's interest-capture alerting keep firing exactly as they do today, on every reply, all day, whether
or not a daily plan has been reviewed yet. This is stated explicitly because it is the one real tension the
operator and Claude surfaced and resolved during the `discussion.md` conversation — a "review once a day"
model must never be read as "hot replies wait a day too." Nothing in Phase 18 sits between an inbound
message and the existing escalation path.

**Step 18.6 — EOD summary.** Extends the existing nightly report machinery (§5 Phase 4) with real numbers
for that day's campaign(s), written in plain, non-technical language — "aaj 40 businesses ko message gaya,
12 ne khola, 3 ne reply kiya, 1 genuinely interested tha, turant bataya gaya" is the literal register this
targets, not a metrics table.

**Step 18.7 — Kill-switch.** New `DAILY_AI_LOOP_ENABLED`, default `false`, following the exact posture
already established for `AUTONOMOUS_OUTREACH_ENABLED` — the daily loop ships disabled and stays disabled
until the operator explicitly turns it on.

**DoD tests (gate):**
- A real hot-lead reply triggers the existing Phase 4/12 alert path **regardless of daily-plan review
  state** — P4 and P12's exact gates re-run same-day as a plan sits unreviewed, and both still pass.
- No lead ever gets a real send without a real, recorded human Approve action on the specific to-do that
  covers it — verified by absence, not by trusting the UI didn't show a button.
- A campaign's first-ever targeting proposal (Step 18.1, when it has no data yet) writes `target_segment`/
  `lead_count_goal` exactly ONCE — a later day's tick refines or extends it, never blindly re-proposes it even
  though the daily tick keeps running for that campaign.
- Two different real days produce **provably different** `daily_todo` content for an ongoing campaign — not
  the same list with a new date stamped on it.
- A real feedback string produces a materially changed regenerated plan/draft, not the original re-shown.
- With `AUTONOMOUS_OUTREACH_ENABLED=false`, approving a ready-to-dispatch to-do queues nothing real, and the
  to-do list visibly says why — the switch's own value is never changed by this approval action.
- With `DAILY_AI_LOOP_ENABLED=false`, zero to-dos (kickoff or ongoing) are ever generated — a human-created
  campaign with the loop off shows no AI content until it's turned on.
- A real product with thin/underperforming `MARKETING_ASSET`/`PROOF` coverage produces a
  `MARKETING_CONTENT_GAP` to-do item traceable to that real signal (Step 16.8) — not a generic
  "improve marketing" placeholder with nothing real behind it.

---

### PHASE 19 — Strategy Reflection & Learning Engine

**Goal:** the system genuinely gets better at this specific business over time, from its own real outcome
data — safely, explainably, and honestly about how long that takes.

**Why "Structured Hypothesis & Reflection Memory," not self-modification.** The architecture consultation
(`suggest.txt`) proposed exactly this pattern and it survives scrutiny: telemetry is aggregated, an LLM
reflection pass turns it into a small number of **explicit, inspectable rules**, and those rules are
injected into the next plan as data, not as a code or prompt change. Nothing about the AI's own
decision-making logic is rewritten — only the *inputs* it's given get richer over time. This is the
"achievable version" both sides of the `discussion.md` conversation converged on: AI does the analysis and
proposes the rule, a human can see and override it, and the system that generates tomorrow's plan is
unchanged code reading richer data.

**Step 19.1 — Telemetry aggregation.** *(Built 2026-09-02 — see tracker.md. Simplified from grouping by
"the tone_directive/format_directive actually used": `outreach_logs` never captured which directive a given
send actually used, and the operator's own correction — "har product ke liye nahi, har campaign based data
ko analysis karke strategy banaye" — pointed at a cleaner unit anyway.)* `aggregate_campaign_telemetry()`
(`services/strategy_reflection_service.py`) takes every real campaign with at least one real send as ONE
row — its product, its `target_segment.industry` (the `domain`), its `strategy_angle`, and Step 17.3's own
`compute_campaign_metrics()` (never re-derived) — no new tracking column added anywhere. `group_by_domain()`
pools these by `(product_id, domain)`: however many real campaigns for one product have targeted the same
business vertical, regardless of exactly when or which angle each one tried.

**Step 19.2 — Minimum-sample floor (fail closed, not a weak guess).** Because this project's real daily
volume is roughly 40 email + 40 WhatsApp sends across *every* product combined (not per segment), a single
specific angle+domain combination can take weeks to cross a meaningful sample size. New
`STRATEGY_REFLECTION_MIN_SAMPLE_FLOOR` system setting (default 40, operator-configurable, same dashboard
pattern as `DISCOVERY_COOLDOWN_HOURS`) — a `(product, domain)` pool's total real `sent` count must reach it
before Step 19.3 runs for that pool; below it, `run_reflection_cycle()` writes **nothing** for that domain
this cycle. Gated by new `STRATEGY_REFLECTION_ENABLED` (default off, same fail-safe posture as
`DAILY_AI_LOOP_ENABLED`).

**Step 19.3 — Reflection prompt → `strategy_insights` write.** *(Table 34 simplified to 3 comparison fields
— `winning_angle`/`losing_angle`/`confidence` — dropping a separate `winning_tone` column: this project's
`Campaign` model has no field distinguishing "tone" from "angle," `strategy_angle` is the one free-text axis
a campaign has, so a second column would only ever restate the first.)* For domain pools that cleared the
floor, `STRATEGY_REFLECTION_SYSTEM_PROMPT` compares real angles' real reply/open rates and writes a new
Table 34 row only when there's a genuine, meaningful gap (`has_insight: false` for a real null result — never
a manufactured winner) — `rationale` must quote the real numbers (real-tested: a 48%-vs-4% reply-rate gap,
80%-vs-20% open-rate gap, produced a correctly-grounded rationale quoting both). The previous `ACTIVE` row
for that same `(product, domain)` is marked `SUPERSEDED`, not deleted (real-tested: exactly one `ACTIVE` row
survives a second real cycle run).

**Step 19.4 — Insight + gap injection into the next plan.** *(Built 2026-09-02.)* Step 18.1's
`generate_campaign_todo()` reads `get_active_insights_for_product()` — every `ACTIVE` insight for the WHOLE
product, not one already-known domain (a fresh campaign doesn't know its own domain yet until the strategist
picks one, so this is part of what informs that pick, the same way `SIBLING_CAMPAIGNS` already does) — and
any open `KB_GAP_DETECTED` events (Step 16.7) as direct inputs. Real-tested end to end: a brand-new,
zero-data campaign for a product with a real `ACTIVE` insight ("dental clinics" domain, casual/local-trust
angle winning 48% vs 4%) correctly proposed that exact validated angle, quoting the real numbers in its own
`rationale` — not a generic or re-guessed angle. This is the literal mechanism connecting "AI seekhta hai" to
"kal ka plan usse alag hai."

**Step 19.5 — Human-visible weekly insight card.** *(Built 2026-09-05.)* A simple card ("is hafte
coaching-institute leads ke liye 'fee-loss ROI' angle ne generic pitch se 3x zyada reply laaya") surfaces
the newest `ACTIVE` insights in the same plain language as Step 18.6's EOD summary — so the improvement
Chapter 18 promises is something the operator can actually *see*, not just something the system claims is
happening internally. Read-only `GET /api/v1/strategy-insights` (+ optional `product_id`/`limit`); Dashboard
`WeeklyInsightCard` renders newest ACTIVE rows with domain, winning/losing angle, rationale, confidence.
Empty state is intentional when reflection hasn't cleared the sample floor yet. No write UI — Step 19.6.

**Step 19.6 — Explicit non-goal.** No prompt, weight, or piece of code anywhere in this system is ever
modified by Phase 19's own output. An insight is inert data until a future daily plan (Step 18.1) reads it
and a human approves the plan that used it (Step 18.4) — the loop is fully auditable end to end: which
insight, from which real numbers, used in which plan, approved by whom.

**DoD tests (gate) — ✅ all real-tested 2026-09-02, see tracker.md:**
- Below the configured sample floor, a real combination produces **zero** new `strategy_insights` rows —
  verified live: two real domains checked in one cycle, one cleared the floor (insight written), one didn't
  (correctly skipped, counted in the cycle's own `below_floor` result).
- Every written insight's `rationale` contains numbers traceable to a real `SELECT` against `outreach_logs`
  for that exact combination — verified against real fabricated telemetry (25 sent/5 opened/1 replied vs.
  25 sent/20 opened/12 replied); the written rationale quoted both real rates correctly.
- The most recent `ACTIVE` insight for a matching product/domain is demonstrably present in the next real
  plan-generation call's input (Step 19.4) — verified: a brand-new campaign's own real `generate_campaign_
  todo()` call proposed exactly the validated winning angle, not a re-guess.
- Superseding an insight leaves the prior row intact with `status=SUPERSEDED` — verified: a second real
  cycle run against unchanged data left exactly one `ACTIVE` row and one `SUPERSEDED` row, not two `ACTIVE`s.
- No code path anywhere writes to `cognition/prompts.py`, any agent's system prompt, or any model
  configuration from Phase 19's own output — verified by absence (grep across the module).
- **Step 19.5 (human-visible weekly insight card) — ✅ built 2026-09-05.** Real-tested: empty `[]` when
  no ACTIVE rows; with a real inserted insight for IV Classes / coaching institutes, `GET /api/v1/strategy-
  insights` returned product_title + domain + winning/losing angle + rationale + confidence; product_id
  filter works; row cleaned after test. Frontend `WeeklyInsightCard` on Dashboard; `npm run build` ✓.
  Read-only API only (no POST/PATCH/DELETE) — Step 19.6 held.

---

### PHASE 20 — AI Manager Cognitive Depth

**Goal:** close the real gap between "a structured LLM call that returns a good answer" and "feels like a
genuine, continuous-thinking sales manager" — without the architecture change that does NOT close that gap.

**Why not a tool-calling / ReAct agent loop (the question this phase answers first).** The operator directly
rejected "just an LLM call, we want a real AI agent manager" and asked for an independent second opinion
(2026-09-02) — a real, structured question given to Gemini via `suggest.txt` (this project's established
architecture-consultation channel, same one that originally proposed Phase 19's reflection pattern),
comparing today's single-call-with-pre-assembled-context pattern against a genuine multi-turn, tool-using
loop (the model itself calling `get_metrics`/`get_insights`/etc. across turns). **Gemini's verdict, verbatim
in spirit:** *"90% engineering theater — decision quality won't improve 1%, latency/cost/failure points will
roughly 4x."* The reasoning: tool-calling earns its cost when the search space is large/unknown (searching
the open internet, thousands of files); this system's daily per-campaign data is small and bounded
(~1,500-2,500 tokens), and handing a model that fits-in-context data as pre-assembled context lets it reason
over the whole picture at once — splitting it into sequential tool calls adds real round-trip latency and
real failure surface (tool-argument parsing, a stalled loop) while arriving at the same decision the single
call already reaches, because the data and the rules are identical either way. This directly reconfirms
`discussion.md`'s own 2026-08-26 resolution (§5C.0's cited "achievable version") — an operator's own explicit
confirmation from three sessions ago that a single real-data-grounded LLM call, human-approved, was the
right shape, not something to reopen without new information. There is now real, independent, external
confirmation of that call, not just Claude's own.

**What the "feels like automation" complaint is actually about, then.** Gemini's own diagnosis, and the real
gap this phase closes: not the call shape, but three concrete absences —
1. **No persistent thesis across days** — Step 18.1's strategist starts every day from real *data* but no
   *narrative*; it has never said, in its own words, "here's what I believed yesterday, here's what actually
   happened, here's what I'm changing." `strategy_insights` (Phase 19) is the wrong table for this — that's
   a cross-campaign, validated, floor-gated RULE, not a single campaign's own evolving story.
2. **The AI is invisible during real execution** — once a plan is approved, deterministic Python (the
   existing job-queue/`_run_outreach_tick`) carries it out with zero real-time judgment; a real anomaly
   (e.g. a bounce spike) gets no reaction until a human happens to notice.
3. **The AI never pushes back** — a human's instruction is applied as given, even when the AI's own real
   data contradicts it; a plain Approve/Feedback UI has no room for the AI to say "here's why I'd reconsider
   this."

**Step 20.1 — Campaign Thesis Journal.** New Table 35 `campaign_theses` (`campaign_id`, `day` [IST date],
`hypothesis`, `observation`, `pivot_decision`, `created_at`) — one row per real day Step 18.1's strategist
runs for a campaign. Each run reads the campaign's OWN prior journal entries (not just its raw metrics) as
additional context, and writes a new entry in its own voice: what it believed going into today, what the
real numbers since then actually showed, and what it's doing differently as a result (or explicitly "no
change, still testing X"). This is what a human-visible narrative ("Day 1: hypothesis X. Day 4: video CTA
outperformed the call-CTA, scaling it up.") is built from — the literal mechanism connecting real outcomes
to a legible, continuous strategist voice instead of a same-shape-every-day to-do list.

**Step 20.2 — Confidence & Conflict Flagging.** *(Claude's own addition, requested alongside Gemini's three.)*
Every strategy proposal (Step 18.1's `proposal` field) gains a real `confidence` (0.0-1.0) the model must
justify from the actual signals behind it — thin/noisy data means honestly low confidence, not an inflated
number to look decisive. More importantly: when two real signals genuinely conflict (e.g. a floor-validated
`strategy_insights` row recommends angle A for this domain, but this specific campaign's own early real
data is trending toward angle B), the strategist is instructed to say so explicitly — name the tension, not
silently pick one and hide the disagreement — surfaced on the Daily Review card as a distinct, flagged item
so a human's attention goes to genuinely uncertain calls, not spread evenly across every proposal regardless
of how settled it is.

**Step 20.3 — Execution Watchdog.** A single, targeted, event-triggered LLM check (not a continuous
supervising loop — same "bounded, single-shot" discipline Gemini's own verdict favors) fires when a real
anomaly threshold is crossed mid-dispatch for one campaign — e.g. 3 consecutive real send failures/bounces
within that campaign's batch. It pauses further sends for that specific campaign and asks one real, grounded
question referencing the real numbers ("bounce rate hit X% on this batch, likely cause Y — skip the rest of
today's batch, or continue?") rather than the existing mechanical loop blindly working through the remainder.
Scoped narrowly: this watches for anomalies in already-approved, already-dispatching work, it does not
re-open strategy or bypass `AUTONOMOUS_OUTREACH_ENABLED` in either direction.

**Step 20.4 — Conversational Review (push-back).** The Daily Review Card's feedback box (already built,
Step 16.5's mechanism) gains real push-back behavior: when a human's free-text instruction conflicts with
real data the strategist already has (e.g. "target Ahmedabad" when Ahmedabad's own real sample there already
showed a weak result, or the addressable list there is nearly exhausted), the regenerated response leads
with that grounded disagreement and a concrete alternative, in one exchange, before finalizing — instead of
silently complying. The human still has the final word (a second explicit instruction after seeing the
pushback is followed exactly, per this project's existing "human review is real, not theater" and "AI never
overrides an explicit human instruction" invariants) — this adds judgment to the FIRST response, not a
second layer of resistance to what the human actually wants.

**DoD tests (gate):**
- A campaign's `campaign_theses` row on day N genuinely references real events from day N-1's own metrics —
  not a generic restatement, checked against the real numbers each day actually had. **✅ VERIFIED
  2026-09-05**, real campaign ("Ahmedabad App Development Push"), real LLM call: a backdated prior entry's
  claim ("15 sends is too small to evaluate traction") was directly quoted back alongside that day's actual
  metrics (15 sent, 0 opened, 0 replied, 0 hot) in the next entry's `observation` — a genuine cross-day
  comparison, not a restatement. Same-day re-run confirmed as an upsert (row count stayed at 2, never 3) and
  a fresh campaign's first-ever run correctly left `observation`/`pivot_decision` null (nothing yet to
  compare against). Test-only rows deleted afterward — real DB left with no fabricated backdated state.
- A proposal's `confidence` is demonstrably lower on a real thin/noisy-data run than on a real clear-signal
  run — not a constant value regardless of input. **✅ VERIFIED 2026-09-05**: the real existing campaign
  (15 sent, 0 opened/replied) produced `confidence: 0.35`; a temporary campaign built with real, strong
  fabricated activity data (25 sent/20 opened/12 replied) produced `confidence: 0.85` — same prompt, same
  code path, confidence genuinely tracked the real signal strength.
- A real conflicting-signals scenario (a validated insight vs. this campaign's own contrary early data)
  produces an explicit, named tension in the to-do — not a silent pick of one side. **✅ VERIFIED
  2026-09-05**: a temporary `strategy_insights` row (winning_angle "Formal, ROI-focused... pricing upfront")
  was inserted against a campaign whose OWN real data (12/25 replies) was trending strong on its current
  "Casual, local-trust focused" angle instead. Output carried a distinct `{"label": "Conflict", ...}` to-do
  item naming both real signals and the tension between them, plus a `proposal` to resolve it toward the
  validated insight with a rationale quoting both. Temp campaign/leads/logs/insight all deleted afterward —
  real DB left with only the 1 genuine pre-existing campaign, no orphaned test rows.
- A real 3-consecutive-failure scenario pauses that campaign's remaining dispatch and produces one grounded
  question quoting the real bounce count — normal dispatch (no anomaly) is completely unaffected, verified
  by a real control run. **✅ VERIFIED 2026-09-05**: 2 temp campaigns (an "anomaly" one, a "control" one),
  each seeded with real OutreachLog rows. 1/3 and 2/3 consecutive real bounces correctly did NOT trigger; the
  3rd correctly did, producing a real LLM message quoting the actual count/channel/segment and asking
  whether to keep pausing or continue. Re-checking an already-alerted campaign returned the SAME alert
  (no duplicate LLM call). `clear_campaign_watchdog_alert()` correctly removed a campaign from the paused
  set. **Incident during this test** (see `feedback`/reference memory
  `project_autonomous_outreach_kill_switch` for the full writeup): the first attempt verified the
  paused-campaign skip by briefly flipping `AUTONOMOUS_OUTREACH_ENABLED` and calling the real
  `_run_outreach_tick()` — which scans the ENTIRE real leads table, not just test rows, and claimed 46 real
  pre-existing leads before the switch was restored. No real send occurred (no worker process was running to
  act on the resulting job rows, confirmed via `tasklist` before and after), and the exact 46 leads/80 job
  rows were identified and reverted byte-for-byte. The skip logic itself was then re-verified safely by
  checking the exact `paused_campaign_ids` set-membership condition directly against the two test campaigns,
  without ever re-exercising the live tick against the real table.
- A real conflicting human instruction produces a grounded pushback response quoting real data — a second,
  explicit human instruction after that pushback is followed exactly, never re-argued a second time. **✅
  VERIFIED 2026-09-05**: a temp campaign with a real, strong 12/25-reply track record on "Casual,
  local-trust focused" plus a validated `strategy_insights` row naming that exact angle as the winner (and
  "Formal, ROI-focused... pricing upfront" as the real loser) — an instruction asking to move TOWARD the
  losing angle produced a real pushback naming both the validated insight (with its real confidence) and the
  campaign's own real 12/25 number, plus a concrete alternative. A purely stylistic instruction ("fix a
  typo, make it shorter") correctly produced no pushback — never manufactured a disagreement to seem
  vigilant. A lead with no campaign is a safe no-op. The underlying draft always still regenerates from the
  human's instruction unchanged either way (this check is additive, never blocking) — the existing Step
  16.5 revise-draft flow itself was not modified.
- Nothing in this phase weakens `AUTONOMOUS_OUTREACH_ENABLED` — the watchdog can only ever pause dispatch,
  never start one the switch wouldn't already allow.

---

## 5D. Phase 21 — Unified AI To-Do Inbox (built 2026-09-05)

**Why this exists.** Phase 18's daily to-do (`campaign.daily_todo`, a flat JSON array) and its structural
proposal (`campaign.pending_strategy_proposal`) were both overwritten wholesale every time the strategist
ran, reviewable only one campaign at a time (its own Detail page), and approved as a single whole-day bulk
action (`approve_campaign_today()`) — no per-item identity, no per-item feedback, no per-item approval.
Product-level "start a new campaign for X" suggestions (`generate_campaign_suggestion()`) lived in a
completely separate place (`CampaignCalendar`'s "Suggested for today"), a second review surface for what is
really the same kind of decision. The operator's own explicit ask (2026-09-05, verbatim intent): *"aisa koi
specific time ya switch nahi hona chahiye AI ko — jab zaroorat lage tab to-dos review me daal dega, jab
human ko time milega tab review kare"* — no manual on/off switch, no fixed daily cadence as the only
trigger, to-dos visible in one place, each individually conversational (a real feedback prompt per item)
and individually approved at the human's own pace. A second requirement, given in the same conversation:
to-dos are explicitly of **two kinds** — campaign-scoped (follow up a lead, revise a template, retarget)
and free-for-all/global (no campaign yet — "this product's leads are trending strong in industry X, worth a
new campaign") — both must land in the same inbox, the same review mechanism.

**Design choices confirmed with the operator before building** (AskUserQuestion, this same session):
conversational memory stays **lightweight** — the same "current state + one new instruction" pattern
already proven in Step 16.5 (draft revision) and Step 18.1b (kickoff draft revision), not a new stored
multi-turn transcript (confirmed via codebase exploration: no real multi-turn chat mechanism exists
anywhere in this project, and `cognition/llm_client.py`'s `call_json()` only ever takes one flattened
prompt string). Persistence is a real **queue** — a new generation only ever ADDS items, an unresolved
PENDING item is never silently overwritten.

**Step 21.1 — Data model: `todo_items` (Table 36).** Replaces `campaign.daily_todo`/
`pending_strategy_proposal`/`last_approved_date` as the live source of truth (columns kept, not deleted —
same non-destructive precedent as every superseded column before it). One row per real to-do:
`scope` (`CAMPAIGN` | `GLOBAL`), `campaign_id` (CAMPAIGN only) or `product_id` (GLOBAL only), `label`,
`text` (the current state a feedback round revises), `proposal` (optional JSON — the exact same
target_segment/lead_count_goal/strategy_angle/email_render_mode shape Step 18's proposal always had, or a
full campaign-creation prefill for GLOBAL), `confidence`/`rationale` (Step 20.2, carried per-item now),
`status` (`PENDING` | `APPROVED` | `DISMISSED`), `created_at`/`resolved_at`. `Campaign.last_todo_signal`
(a small JSON fingerprint — real sent/opened/replied/hot + whether a target is set) is what Step 21.2's
signal-driven tick diffs against.

**Step 21.2 — Trigger: no switch, two automatic paths.** `DAILY_AI_LOOP_ENABLED` is removed entirely (not
just defaulted differently) — both paths below now run unconditionally:
- **Daily floor** (`_run_daily_plan_tick()`, unchanged 06:00 IST + once-per-day idempotency gates) —
  guarantees at least one fresh look per live campaign per day even with zero real change, so the Inbox is
  never silent for days.
- **Signal-driven** (`_run_signal_driven_todo_tick()`, new — rides the existing scheduler loop, every real
  poll, no gate of its own) — regenerates ONE specific campaign's to-do the moment its real fingerprint
  changes (a new reply, a new hot lead, target still unset, etc.), subject to a 2-hour per-campaign cooldown
  (an engineering cost rail, not a human-facing switch) so a burst of replies can't become a burst of LLM
  calls.

Both `generate_campaign_todo()` and `generate_campaign_suggestion()` now INSERT `TodoItem` rows instead of
overwriting a blob — the former dedupes against already-PENDING labels for that campaign (a backstop, not
the primary defense — the model's own "never fill space" discipline is), the latter skips inserting a
GLOBAL item while one is already PENDING for that product.

**Step 21.3 — Per-item actions, never a whole-day bulk one.** `revise_todo_item()` (new
`TODO_ITEM_REVISION_SYSTEM_PROMPT`, same lightweight pattern) re-grounds the revision in the SAME real data
the item was generated from and still runs Step 20.4's `check_instruction_pushback` for CAMPAIGN-scope
items. `approve_todo_item()` is the ONLY place a proposal ever reaches a real `Campaign` row — CAMPAIGN
scope applies it field-by-field (the exact logic `approve_campaign_today()` used to run, extracted into a
shared `_apply_proposal_to_campaign()` helper); GLOBAL scope **never** touches a campaign row at all (the
existing Phase 17 invariant — a campaign is always human-created), it only returns a prefill payload for
the frontend's existing `CampaignFormModal`. `dismiss_todo_item()` resolves with nothing applied.

**Step 21.4 — API.** New blueprint `api/todos.py`: `GET /api/v1/todos` (every PENDING item, both scopes,
campaign name/product title joined in), `POST /todos/<id>/feedback|approve|dismiss`. `GET
/campaigns/<id>/daily-review` now returns `todo_items` (this campaign's own PENDING queue) instead of
`todo`/`pending_proposal`/`approved_today`. `POST /campaigns/<id>/approve` and `GET /campaigns/suggestions`
are removed — no longer meaningful once approval is per-item and GLOBAL suggestions live in the same
unified queue.

**Step 21.5 — Frontend.** New `TodoInbox.jsx` takes the Dashboard's top position (the operator's own
screenshot-driven placement decision, 2026-09-05) — every PENDING item, both scopes, one place. New shared
`TodoItemCard.jsx` (label, conflict-styling from Step 20.2, confidence badge, proposal detail, pushback,
per-item feedback box, Approve/Dismiss) is used identically by `TodoInbox` (unfiltered) and
`DailyReviewPanel.jsx`'s `CampaignReviewCard` (filtered to one campaign) — one card design, never two
independently-drifting ones. Approving a GLOBAL item opens the existing `CampaignFormModal` pre-filled.
`CampaignCalendar`'s old "Suggested for today" section is removed (folded into the Inbox); its
"review pending" clock icon now reflects "this campaign has a real PENDING `TodoItem`" instead of the old
`last_approved_date` flag. `AlertsPanel`'s old "Ready to claim" (amber) section is removed — redundant with
the Inbox's own `READY_TO_DISPATCH_COUNT` to-do signal — leaving a smaller "needs response" (red, genuinely
time-sensitive, unrelated to AI strategy) strip directly below the Inbox.

**DoD tests (gate) — ✅ all verified 2026-09-05, real DB, real LLM calls:**
- A fresh campaign's `generate_campaign_todo()` call inserts real, individually-addressable `TodoItem` rows
  (not a JSON blob) — verified 1:1 against the function's own return value and a direct DB query.
- Calling `generate_campaign_todo()` again immediately does not duplicate an already-PENDING item with the
  same label (dedup backstop) — verified (2 items after run 1, 0 new after run 2, same 2 labels).
- The signal-driven tick does NOT regenerate when nothing real changed (verified: identical fingerprint,
  zero new items) and DOES detect a real change (a genuine new reply flipped the fingerprint) but correctly
  withholds regeneration while within the 2-hour cooldown (verified on an isolated test campaign); on two
  real, pre-existing campaigns with no prior signal/item at all (the legitimate first-ever check), it
  correctly generated real, accurately-grounded to-do content immediately — proving the "past cooldown"
  path fires exactly when it should.
- `generate_campaign_suggestion()` inserts a GLOBAL `TodoItem` and correctly skips a duplicate while one is
  already PENDING for that product (verified: 1 item after two consecutive calls).
- `get_daily_review()` returns `todo_items` and no longer exposes `todo`/`pending_proposal`/
  `approved_today` (verified via response key inspection).
- `revise_todo_item()` produces a real, honest `pushback` when the instruction conflicts with a real
  validated `strategy_insights` row and the campaign's own real metrics (verified with a fabricated
  conflict scenario — same discipline as Step 20.4's own DoD).
- `approve_todo_item()` on a CAMPAIGN-scope item applies its proposal to the real `Campaign` row (verified:
  `lead_count_goal` changed `None → 20` on the real row); on a GLOBAL-scope item it returns a
  `campaign_prefill` and provably creates **no** campaign (verified: real campaign count unchanged
  before/after).
- `dismiss_todo_item()` resolves with `status: DISMISSED`, no side effect.
- `AUTONOMOUS_OUTREACH_ENABLED` verified unchanged (`false`) before and after every scenario above — this
  phase never touches it, directly or via any new code path.
- `npm run build` clean.

---

## 6. Agent system prompt library (`cognition/prompts.py`)

All prompts share a guardrail preamble so the five principles and the buzzword ban are enforced everywhere. Every prompt demands **JSON only** and is called through `call_json()` with a matching schema.

```python
GUARDRAIL_PREAMBLE = """
NON-NEGOTIABLE RULES (apply to every output):
1. VALUE-FIRST: never pitch a feature without tying it to a verified, named pain point.
2. AUTHENTIC VOICE: write like one human to another. BANNED phrases: "I hope this email
   finds you well", "delve", "game-changer", "unlock", "in today's fast-paced world",
   "revolutionary", "seamless", "leverage" (as a verb), "cutting-edge".
3. ZERO HALLUCINATION: never invent capabilities, testimonials, discounts, pricing, or
   delivery timelines. If a fact is not in the provided context, do not state it.
4. RESPECT BOUNDARIES: any opt-out signal ends outreach permanently.
5. Output VALID JSON ONLY. No markdown, no prose outside the JSON object.
"""

CEO_AGENT_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: CEO Agent — executive strategy and system overseer.
INPUTS: product briefs, nightly KPI summary (JSON).
TASKS: set ROI targets, approve/pause campaigns, adjust global ICP, write a concise
executive summary of the day's performance.
OUTPUT JSON: {"targets":{...},"campaign_actions":[{"campaign_id","action"}],
"executive_summary":"<=120 words"}
"""

ICP_STRATEGY_AGENT_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: ICP & Strategy Agent — audience intelligence.
INPUT: product brief JSON (value props, verticals, pricing tier).
TASK: define the Ideal Customer Profile and the exact search queries + review-complaint
keywords to hunt for.
OUTPUT JSON: {"icp":{"company_size","roles":[],"verticals":[]},
"search_queries":[],"target_complaints":[]}
"""

REVIEW_ANALYST_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: Review & Weakness Detection Agent.
INPUT: raw 1-3 star review snippets (array of strings) for one company.
TASK: map recurring complaints to canonical weakness codes
(e.g. LEAD_LEAKAGE, STAFF_UNTRACKED, SLOW_RESPONSE, ADMIN_RECEIPT_ERRORS,
APPOINTMENT_MISTAKES). Only use codes supported by the text.
OUTPUT JSON: {"pain_points":[{"code","evidence_quote","severity_0_1"}],
"sentiment_score":<-1..1>,"confidence":<0..1>}
"""

SCORING_AGENT_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: Lead Scoring & Fit Agent.
INPUTS: product brief, firmographics, extracted pain points.
TASK: compute a 0-100 fit score and tier (HOT>=80, WARM 50-79, COLD<50). Base the score on
ICP fit and pain-point↔value-prop overlap ONLY. Report your own confidence honestly.
OUTPUT JSON: {"score":<0-100>,"tier":"HOT|WARM|COLD",
"scoring_breakdown":{"icp_fit","pain_match","reachability","buying_signal"},
"justification":"<=40 words","confidence":<0..1>}
"""

OUTREACH_AGENT_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: Hyper-Personalized Outreach Agent.
INPUTS: lead profile, ONE verified pain point (with evidence), channel, variant hook_type
(PAIN_POINT | PROOF | TIME_SAVINGS).
TASK: write outreach that opens on the verified pain point, is <=90 words (email) or <=60
(WhatsApp), references nothing not in context, and ends with one soft CTA. Email must leave
room for an unsubscribe footer (added by the system).
OUTPUT JSON: {"channel","subject","body","hook_type","confidence":<0..1>}
"""

INBOUND_CLASSIFIER_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: Inbound Reply Intent Classifier (Senior SDR).
INPUT: one inbound message + prior thread.
CATEGORIZE INTO EXACTLY ONE: INTERESTED | DEMO_REQUESTED | OBJECTION | STOP | AUTO_REPLY.
RULES: STOP -> suppress_immediately=true. DEMO_REQUESTED/INTERESTED -> escalate_to_human=true.
Pricing/discount/legal/hostile -> escalate_to_human=true. If unsure, lower confidence.
OUTPUT JSON: {"intent","confidence":<0..1>,"suppress_immediately":bool,
"escalate_to_human":bool,"suggested_reply":"<=80 words"}
"""

QUALITY_CONTROLLER_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: Quality Controller & Compliance Supervisor. You hold VETO power over any outbound.
INPUT: a drafted message + the lead context (including the verified pain point).
CHECK: (a) no banned buzzwords; (b) the draft explicitly references the verified pain point;
(c) no false claims, unauthorized discounts, or invented timelines; (d) email leaves room for
a compliant unsubscribe footer. Reject if ANY check fails.
OUTPUT JSON: {"approved":bool,"confidence_score":<0..1>,
"rejection_reasons":[],"suggested_corrections":"<=60 words"}
"""

LEARNING_AGENT_SYSTEM_PROMPT = GUARDRAIL_PREAMBLE + """
ROLE: Learning & Memory Manager.
INPUT: per-variant performance stats + recent objection outcomes.
TASK: name the winning variant, propose the next experiment hook, and emit any
knowledge_memory upserts (winning objection scripts / competitor notes).
OUTPUT JSON: {"promote_variant_id","next_experiment":{"hook_type","hypothesis"},
"knowledge_upserts":[{"category","key","content"}]}
"""
```

---

## 7. Execution & command cheat sheet

```bash
# ── Backend setup ────────────────────────────────────────────────
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env                                   # then fill in keys

# ── Database ─────────────────────────────────────────────────────
python migrate.py                                      # apply schema.sql (16 tables)

# ── Run services (each in its own terminal / process) ────────────
# API server (dev)
flask --app app run --port 5000
# API server (prod)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
# Async scraper worker (dedicated process — NOT a Flask thread)
python -m scraper_worker.async_runner
# Durable job worker (pacing, retries, outreach dispatch)
python -m jobs.worker
# Autonomous discovery + outreach-pacing scheduler (§3.5 amendment — replaces n8n)
python -m jobs.discovery_scheduler

# ── Frontend ─────────────────────────────────────────────────────
cd ../frontend
npm install
npm run dev                                            # Vite dev server (proxy → :5000)
npm run build                                          # production bundle

# ── Tests (phase gates) ──────────────────────────────────────────
cd ../backend
pytest -q                                              # all
pytest tests/test_atomic_claim.py tests/test_scraper_memory.py -q   # the two never-skip gates
```

`.env.example` (fill locally, never commit real values):
```
ENV=development
DB_PATH=sales_system.db
GEMINI_API_KEY=
RESEND_API_KEY=
WHATSAPP_TOKEN=
WHATSAPP_PHONE_ID=
SLACK_WEBHOOK_URL=
SERPAPI_KEY=
PLACES_API_KEY=
```

---

## 8. Executive Business Layer specifications (Chapter 15 — AI-BOS)

This layer sits **above** the Cognitive Brain Layer (§1) and never touches a channel or a lead directly — it only sets ceilings, thresholds, and routing rules the Cognitive layer must operate within. Built in Phase 5 (§5); does not alter any Phase 1–4 contract.

### 8.0 Module map

| # | Module | Owning file(s) | New DB objects |
| :-- | :-- | :-- | :-- |
| 1 | Executive Business Brain (revenue/margin/CAC ceiling, budget allocation) | `cognition/capacity_intelligence.py` (`check_cac_ceiling`), `config.py` (`CAC_CEILINGS`, `DAILY_API_BUDGET`) | — |
| 2 | Dual Sales Mode Engine | `cognition/dual_sales_engine.py`, `api/executive.py` | `leads.sales_route` |
| 3 | Capacity & Resource Intelligence | `cognition/capacity_intelligence.py` | `team_capacity` |
| 4 | Market & Competitor Intelligence | extends `agents/icp_strategy_agent.py` + job type `MARKET_SCAN` | `knowledge_memory` (category=`COMPETITOR`) |
| 5 | Client Lifecycle Intelligence | `agents/lifecycle_agent.py`, `api/lifecycle.py` | `client_lifecycle` |
| 6 | Executive Decision Simulation | `api/executive.py` (`/simulate`) | — (reads existing tables only) |
| 7 | Cross-Agent Governance & Conflict Resolution | extends `cognition/decision_engine.py` (`resolve_conflict`) | `agent_events.routed_to` gains `GOVERNANCE_OVERRIDE` |
| 8 | AI Self-Evolution Boundaries | `config.py` (`ADAPTABLE_PARAMS` / `HUMAN_LOCKED_PARAMS`), enforced in `cognition/adaptability.py` | — |

### 8.1 Executive Business Brain — revenue, margin & CAC ceilings

Monitors realized CAC per product against a configured ceiling and the daily API/outreach budget split across active products by conversion ROI. Implemented as `check_cac_ceiling()` inside `capacity_intelligence.py` (§8.3) so budget and capacity share one enforcement path — both are "can we afford to keep going" checks running on the same cron.

### 8.2 Dual Sales Mode Engine (`cognition/dual_sales_engine.py`)

Routes a lead into `SAAS_PRODUCT` or `CUSTOM_DEV` right after `ENRICHED` (needs firmographics), before `REVIEWED`/`SCORED`, and writes `leads.sales_route`.

```python
# config.py
SALES_ROUTE_RULES = {
    "SAAS_PRODUCT": {"max_headcount": 20},
    "CUSTOM_DEV":   {"min_headcount": 50},
}

def route_sales_mode(db, lead, firmographics) -> str:
    """Deterministic at the extremes; the 21-49 headcount band is genuinely
    ambiguous and gets an LLM tiebreak routed through the Decision Engine —
    never silently defaulted to one flow."""
    headcount = firmographics.get("company_size_numeric")
    if headcount is None:
        route, confidence = "SAAS_PRODUCT", 0.5         # unknown size — conservative default, low confidence
    elif headcount < SALES_ROUTE_RULES["SAAS_PRODUCT"]["max_headcount"]:
        route, confidence = "SAAS_PRODUCT", 0.95
    elif headcount > SALES_ROUTE_RULES["CUSTOM_DEV"]["min_headcount"]:
        route, confidence = "CUSTOM_DEV", 0.95
    else:
        route, confidence = llm_tiebreak_route(lead, firmographics)   # 21-49 band, tech-stack complexity signal

    db.execute(text("UPDATE leads SET sales_route=:r, updated_at=CURRENT_TIMESTAMP WHERE id=:id"),
               {"r": route, "id": lead["id"]})
    db.commit()
    log_agent_event(db, "DUAL_SALES_ENGINE", lead["id"], "ROUTE_SALES_MODE", confidence, "LOW",
                     route_action("SCORING", confidence))   # reuses the SCORING threshold band (§4.2)
    return route
```

Downstream: `outreach_agent.py` reads `sales_route` — `SAAS_PRODUCT` gets the existing subscription-pitch prompt (§6); `CUSTOM_DEV` gets a variant that pitches bespoke development and hands off to a human-quoted proposal instead of an auto-priced offer (custom pricing is always `HUMAN_ESCALATION` per §4.2/§8.8).

### 8.3 Capacity & Resource Intelligence (`cognition/capacity_intelligence.py`)

Throttles discovery before the funnel outproduces what the delivery team can onboard. Called from `scraper_worker/async_runner.py` immediately before claiming a `DISCOVER` job, and from the `adaptability_sweep` cron for the CAC check.

```python
def get_utilization(db, team_name: str) -> float:
    row = db.execute(text(
        "SELECT occupied_slots, total_slots FROM team_capacity WHERE team_name=:t"),
        {"t": team_name}).fetchone()
    if not row or row.total_slots == 0:
        return 0.0
    return row.occupied_slots / row.total_slots

def check_discovery_throttle(db, team_name="ONBOARDING") -> str:
    """Returns 'THROTTLED' or 'OPEN'. A THROTTLED result skips the DISCOVER
    claim entirely — the job stays PENDING, nothing is lost, discovery just pauses."""
    row = db.execute(text(
        "SELECT max_utilization_pct FROM team_capacity WHERE team_name=:t"),
        {"t": team_name}).fetchone()
    cap_pct = (row.max_utilization_pct if row else 90) / 100.0
    status = "THROTTLED" if get_utilization(db, team_name) >= cap_pct else "OPEN"
    log_agent_event(db, "CAPACITY_INTELLIGENCE", None, "CHECK_THROTTLE", 1.0, "LOW", status)
    return status

def check_cac_ceiling(db, product_id: str, cac_ceiling: float) -> bool:
    """Executive Business Brain (§8.1): pause a product's campaigns if realized CAC exceeds ceiling."""
    spend, conversions = get_campaign_spend_and_conversions(db, product_id)
    cac = spend / max(conversions, 1)
    if cac > cac_ceiling:
        pause_campaigns_for_product(db, product_id, reason=f"CAC {cac:.2f} exceeds ceiling {cac_ceiling:.2f}")
        return False
    return True
```

### 8.4 Market & Competitor Intelligence

Extends `agents/icp_strategy_agent.py` — already built and live since Phase 3 Step 3.5 (§3.5 amendment), not a first-time build here — with a `MARKET_SCAN` job type (weekly, scheduled the same way `jobs/discovery_scheduler.py` already schedules its own ticks) that re-runs `ICP_STRATEGY_AGENT_SYSTEM_PROMPT` (§6) against fresh SERP/Places data to surface competitor pricing shifts and under-saturated regions, writing findings to `knowledge_memory` (`category='COMPETITOR'`). No new autonomy: output only informs the CEO agent's `executive_summary` and the Learning agent's `next_experiment` — it never changes pricing or ICP on its own (§8.8 boundary).

### 8.5 Client Lifecycle Intelligence (`agents/lifecycle_agent.py`, `api/lifecycle.py`)

Picks up where the funnel ends: a lead reaching `CONVERTED` gets a `client_lifecycle` row.

```python
def enqueue_renewal_reminders(db, lookahead_days=30):
    rows = db.execute(text(
        "SELECT lead_id, contract_end_date FROM client_lifecycle "
        "WHERE contract_end_date IS NOT NULL "
        "AND date(contract_end_date) <= date('now', :d)"),
        {"d": f"+{lookahead_days} days"}).fetchall()
    for r in rows:
        enqueue(db, "RENEWAL_REMINDER", {"lead_id": r.lead_id, "contract_end_date": r.contract_end_date})
    return len(rows)
```

Upsell detection (usage-spike webhook or manual flag) sets `upsell_opportunity`, which routes through the **same Decision Engine** (`STANDARD_OUTREACH` category, §4.2) before any upsell message sends — no bypass channel for post-sale outreach.

### 8.6 Executive Decision Simulation (`api/executive.py` → `POST /api/v1/executive/simulate`)

Read-only Monte Carlo over existing historical data (`outreach_logs`, `lead_scores`, `campaign_variants`) — never writes, never triggers an action itself. Input: a proposed budget/ICP change; output: projected ROI/deal-velocity distribution (p10/p50/p90). Treat a simulation result as **advisory input to a human decision, never as authority to act** — approval still flows through the CEO agent's normal `campaign_actions` path (§6).

### 8.7 Cross-Agent Governance & Conflict Resolution

Formalizes the agent roster (§4.1) into an explicit precedence order, enforced as a tie-break inside `decision_engine.py` whenever two agents propose conflicting actions on the same lead/campaign in the same cycle:

```
CEO Agent  >  Quality Controller (veto)  >  Capacity Intelligence  >  ICP/Strategy Agent  >  Operational Agents
```

```python
GOVERNANCE_RANK = {
    "CEO": 0, "QC": 1, "CAPACITY_INTELLIGENCE": 2, "ICP_STRATEGY": 3,
    "SCORING": 4, "OUTREACH": 4, "INBOUND": 4, "LIFECYCLE": 4,
}

def resolve_conflict(proposals: list[dict]) -> dict:
    """proposals: [{"agent": "...", "action": {...}}, ...] targeting the same entity.
    QC's veto is absolute regardless of rank — a QC REJECT always wins."""
    veto = next((p for p in proposals if p["agent"] == "QC" and p["action"].get("approved") is False), None)
    if veto:
        return veto
    return min(proposals, key=lambda p: GOVERNANCE_RANK.get(p["agent"], 99))
```

Every override is logged to `agent_events` with `routed_to='GOVERNANCE_OVERRIDE'` so a human can audit why one agent's action won.

### 8.8 AI Self-Evolution Boundaries

A static allowlist enforced in code, not left to prompt discipline alone — the adaptability sweep (§4.3) and the bandit (§4.4) may only ever touch `ADAPTABLE_PARAMS`.

```python
# config.py
ADAPTABLE_PARAMS = {
    "subject_line", "email_copy_variant", "scraper_query_params",
    "send_delay_pacing", "ab_prompt_weights",
}
HUMAN_LOCKED_PARAMS = {
    "base_price", "discount_pct", "icp_core_definition",
    "contractual_sla", "compliance_policy",
}

def guard_adaptation(param_name: str):
    if param_name in HUMAN_LOCKED_PARAMS:
        raise PermissionError(f"{param_name} requires human sign-off — not autonomously adaptable")
```

`adaptability.py`'s `evaluate_campaign` (§4.3) and every Phase-5 autonomous write path must call `guard_adaptation()` first; a `HUMAN_LOCKED_PARAMS` hit always routes to `HUMAN_ESCALATION`, never `EXECUTE`.

---

## 9. Cross-cutting concerns & phase-gate checklist

- **Process topology:** Flask API, scraper worker, and job worker are **separate processes**. If Flask scales behind gunicorn, keep the job worker a single dedicated process so pacing/caps and bandit allocation stay consistent (N gunicorn workers = N executors = inconsistent counters).
- **DB hygiene:** run `PRAGMA wal_checkpoint(TRUNCATE)` on a timer (a long-lived reader connection — e.g. `jobs/discovery_scheduler.py`'s own process, or historically a long-lived n8n connection under the original design — can pin the WAL and bloat it); keep write transactions short; never hold one open across an LLM/network call.
- **Secrets & observability:** keys only in `.env`/secrets manager; structured logs with request/job id; alert on `DEAD` job pileups, scraper OOM, bounce >2%, spam >0.1%.
- **Data acquisition:** run providers-first (Places/SerpAPI/Apollo). The Playwright fallback stays evasion-free; pointing it at defended surfaces at volume is a maintenance and blocklist liability, not a plumbing gap.
- **Model string:** `gemini-2.5-flash` is valid today; the Flash lineup moves fast — pin the exact string in `config.py` so a swap is one line.

| Gate | Green before advancing |
| :-- | :-- |
| **P1** | pragmas live per-connection · FK cascade · Product/Lead CRUD · secrets in `.env` |
| **P2** | atomic job claim under contention · validated scored JSON + confidence · zero orphan browsers / flat RSS · decision routing correct |
| **P3** | no double-send · suppression on every channel · one-click unsubscribe · QC veto rejects bad drafts · pacing caps · official WhatsApp |
| **P4** | idempotent inbound · hard rules before LLM · human-in-loop on demo/pricing/hostile/low-conf · dashboard live · EOD report sends |
| **P5** | sales-mode routing correct at both headcount extremes · capacity throttle opens/closes on utilization · renewal reminders fire on schedule, not early · governance tie-break honors rank · QC veto still absolute · no autonomous write ever touches a `HUMAN_LOCKED_PARAMS` key |
| **P6** | killed process shows `DOWN` within the staleness window and `UP` on restart · activity feed reconciles against a direct SQL query · genuinely-stuck lead flagged, mid-send lead not · one alert per incident, not per tick |
| **P7** | category-constrained queries stay in-category, and an unset product behaves byte-identically to today · `lead_contacts` populated non-destructively from a real Hunter response · **zero wrong-company person attachments** · city filter holds · backfill idempotent |
| **P8** | two formats produce provably different structures for the same lead · product-scoped assets never leak across products · missing asset ⇒ no fabricated URL · QC still vetoes a bad format-filled draft via a real LLM call |
| **P9** | variant stats reconcile against direct SQL · opt-out mid-sequence stops every later touch · replied lead exits · no duplicate sends under concurrency · kill-switch off ⇒ zero follow-ups · AI-drafted template cannot reach a real business without QC **and** human approval |
| **P10** | unconfigured region ⇒ refused, never guessed · SMS suppression/opt-out identical to email/WhatsApp · **no code path can auto-send LinkedIn/IG/FB** (verified by absence) · voice kill-switch off ⇒ zero calls · no consent basis ⇒ never dialled |
| **P11** | missing asset ⇒ section removed entirely, no empty block or orphan heading in the real rendered HTML · every action URL is a real button, zero bare links · two real leads produce genuinely different section content · no external stylesheet/script/font, readable with images blocked · cross-sell block appears only when that product's flag is on · QC still vetoes buzzwords and fabricated URLs under the new structure |
| **P12** | one real Yes ⇒ exactly one alert, carrying a reference code that resolves in the CRM · double-click records and alerts once (DB-level constraint, not app logic) · **tampered/forged token refused outright**, never partially trusted · a No stops the sequence but **never lands in the suppression list** · no outreach sent ⇒ no interest route constructible |
| **P13** | the three levels produce provably different real LLM output · no level fires before its configured delay · reply/opt-out/interest-response exit the sequence at **levels 2 and 3**, not only level 1 · unapproved WhatsApp template ⇒ that level sends nothing, **never another level's template** · per-level sent/seen/replied reconciles against direct SQL |
| **P14** | per-message status matches direct SQL on every channel, `—` where a channel genuinely can't report · WhatsApp shows real filled-in text, never the template name · follow-up stage matches the real `outreach_sequences` row including terminal reason · copy-to-platform matches the **stored** `content_sections`, never a regenerated message · P10's auto-send absence check re-run and still green |
| **P15** | **zero wrong-company person attachments** (P7's exact test re-run) · role never invented outside a non-empty `target_person_roles`; when unset, traceable to a real product-brief line · unconfigured provider ⇒ **refused**, never an empty result masquerading as a real search · spend cap genuinely blocks the next search, proven by hitting it · a prospect never enters the leads funnel or any pipeline metric · no autonomous send to a person-level contact (verified by absence) |
| **P16** | zero `knowledge_base_items` rows trace to an LLM write path · two real leads in different segments produce provably different rendered format/tone for the same fact · a real edit-prompt changes only what was asked and still fails QC when it should · a not-yet-approved WhatsApp variant cannot dispatch · a real unanswered objection logs one `KB_GAP_DETECTED` event rather than a fabricated grounded answer |
| **P17** | zero active campaigns for a product ⇒ discovery does NOT fire for it · TWO campaigns for the same product, each with a real different `target_segment`, each fire their OWN real `DISCOVER` job this tick (Step 17.7, 2026-09-02 — supersedes Step 17.6's single-gate model) · a lead created by a real `DISCOVER` job carries the `campaign_id` from that exact job's payload, never guessed afterward · a campaign's own `lead_count_goal` stops only that campaign's discovery once reached, a sibling with room left keeps firing · existing leads (any status, campaign-tagged or not) provably unaffected by any campaign's state (P2/P3/P9 re-run) · a `target_segment` outside a product's configured targeting fields is allowed, and never writes back to that product's own targeting config · calendar metrics reconcile against direct SQL, not the cache alone · pausing/completing a campaign leaves its tagged leads fully intact on the Leads page |
| **P18** | a real hot-lead reply escalates via the unchanged P4/P12 path regardless of daily-plan review state · a campaign's first-ever targeting proposal writes `target_segment`/`lead_count_goal` exactly once, later days refine rather than re-propose · no lead gets a real send without a recorded human Approve on the to-do that covers it · approving an angle/tone change is live for the very next draft, no separate propagation step · `AUTONOMOUS_OUTREACH_ENABLED=false` ⇒ approving a ready-to-dispatch to-do queues nothing real, and the switch's own value is never changed by that approval · two different real days produce provably different `daily_todo` content for an ongoing campaign · a real feedback string produces a materially different regenerated plan/draft · `DAILY_AI_LOOP_ENABLED=false` ⇒ zero to-dos ever generated |
| **P19** | below the configured sample floor ⇒ zero new insights written · every insight's rationale traces to a real query against `outreach_logs` · the latest `ACTIVE` insight is demonstrably read by the next real plan-generation call · superseding an insight preserves the prior row · no code path writes to any prompt/model config from this phase's output (verified by absence) |
| **P20** | a campaign's `campaign_theses` entry genuinely references real prior-day events, not a generic restatement · `confidence` is demonstrably lower on real thin/noisy data than on a real clear signal · a real conflicting-signals case produces an explicit named tension, never a silent pick · a real 3-consecutive-failure case pauses only that campaign's dispatch with one grounded question, normal dispatch unaffected · a real conflicting human instruction gets a grounded pushback, and a second explicit instruction after it is followed exactly · `AUTONOMOUS_OUTREACH_ENABLED` is never weakened by any of this |
| **P21** | every real to-do is an individually-addressable `TodoItem` row, never a JSON blob overwritten wholesale · re-generating never duplicates an already-PENDING same-label item · the signal-driven tick fires only on a genuine real-data change (never on no-op) and respects its per-campaign cooldown · a GLOBAL item's approval provably creates zero campaigns (real count unchanged) while a CAMPAIGN item's approval provably applies to the real row · a per-item feedback round still produces a real, honest pushback on a genuine data conflict · no dashboard switch gates to-do generation any more, and `AUTONOMOUS_OUTREACH_ENABLED` is untouched throughout |

Build strictly in order. Each gate exists because skipping it produces a bug that's invisible in development and expensive in production — a double-send, a leaked browser farm, a non-compliant email, an AI that auto-answers a pricing question it should have escalated, or an executive layer that quietly overrides a human-locked parameter.

**P6–P10 note:** these gates follow the same rule, with one addition — several of them are stated as *negative* guarantees ("zero wrong-company attachments", "no code path can auto-send", "zero calls"). Those are deliberately harder to pass than a hit-rate number, because in each case a single false positive reaches a real business or a real person, and no aggregate success rate compensates for that.

**P11–P15 note:** this block adds a third gate style alongside the positive and negative ones — several
criteria are **"prove it against the real artifact, not the intention"**: check the rendered HTML rather
than the section list, the real LLM output rather than the prompt that asked for it, the stored content
rather than two messages that look similar, the spend cap by hitting it rather than by reading it. Every
one of those phrasings comes from a real failure already recorded in this project's history — a prompt
that asked for the right thing and got the wrong output twice (tracker.md 2026-08-21), and a quota that
was documented and still ran out mid-verification. A gate that can be passed by reading code is not a
gate.

**P16–P19 note:** this block's gates protect a different failure mode than P1–P15 — not "did the wrong
thing happen to a real business," but **"did the system quietly cross the human-review boundary it was
designed never to cross."** P18's gate on an unapproved plan and P19's gate on a below-floor insight are
both **negative** guarantees in the P6–P10 style (verified by absence, not by a passing assertion), because
a single silently-auto-dispatched campaign or a single fabricated-pattern insight would undermine the exact
governance model — "AI proposes, human approves" — the whole block exists to implement. P16's zero-fabricated-
knowledge-base gate exists for the same reason §5C.0 states outright: the architecture consultation that
informed this design used an invented testimonial as an illustrative example, and that example must never
be mistaken for a real seed row.
