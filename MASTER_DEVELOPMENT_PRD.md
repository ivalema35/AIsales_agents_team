# MASTER_DEVELOPMENT_PRD.md
## Autonomous AI Sales Operating System — Unified Build Specification

**Merges:** Technical PRD v3 (Execution Infrastructure) + Intelligence PRD v2 (Cognitive Brain Layer)
**Audience:** A software engineer or a coding agent (Claude Code / Cursor) building production code section by section.
**Build model:** 4 phases, each gated by a Definition-of-Done (DoD) test suite. Do not advance until the gate is green.

---

## 0. How to read this document

- **Sections 1–4** are *reference*: architecture, file tree, the complete data layer, and the cognitive contracts (agents, decision thresholds, memory). Implement against them; don't re-derive them per phase.
- **Section 5** is the *build order*: Phases 1→5, each step listing (a) files to create, (b) a focused code blueprint showing the non-obvious logic and its failure handling, and (c) the DoD tests that open the gate.
- **Section 6** is the *agent prompt library* — copy-pasteable Python string constants.
- **Section 7** is the *command cheat sheet*.
- **Section 8** is the *Executive Business Layer* (Chapter 15 / AI-BOS): the governance layer sitting above Cognitive + Execution — revenue/CAC ceilings, dual sales-mode routing, capacity throttling, client lifecycle, decision simulation, cross-agent governance, and self-evolution boundaries.
- **Section 9** covers cross-cutting concerns and the full phase-gate checklist (P1–P5).
- Code blocks are **blueprints**: they carry the critical logic (routing, atomic claims, cleanup, validation) verbatim and leave routine bodies (field mapping, selectors, styling) for you to fill.

**Three-layer contract:** the Executive layer *governs* (sets revenue/CAC ceilings, capacity throttles, sales-mode routing, and can pause or veto any campaign — Chapter 15 / §8); the Cognitive layer *decides* (emits structured intent + a confidence score); the Execution layer *acts* (Flask/SQLite/Playwright/n8n). Every autonomous decision passes the Decision Engine (§4.2) before the Execution layer touches a channel, and every Executive-level ceiling or override passes the Cross-Agent Governance Hierarchy (§8.7) first.

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
│  WhatsApp Cloud API · n8n schedulers · React/Vite/Tailwind dashboard            │
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
│   │   ├── models.py                   # SQLAlchemy ORM (all 14 tables)
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
│   │   └── worker.py                   # background poller (pacing, retries)
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
├── n8n/
│   ├── docker-compose.yml
│   └── workflows/
│       ├── morning_discovery.json
│       ├── hourly_outreach_pacer.json
│       ├── adaptability_sweep.json
│       ├── inbound_relay.json
│       └── eod_report.json
└── README.md
```

**Table count reconciliation:** the 11 named tables + 3 intelligence-layer tables (`agent_events`, `campaign_variants`, `knowledge_memory`) + 2 executive-layer tables (`team_capacity`, `client_lifecycle`) = **16 total**. The intelligence tables make the cognitive layer auditable, adaptive, and able to remember; the executive tables make it capacity-aware and post-sale-aware. All are flagged in §3.1.

---

## 3. Data layer

### 3.1 Complete SQLite DDL (`database/schema.sql`)

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

**Goal:** running Flask app, WAL SQLite with all 14 tables, per-connection pragmas, Product + Lead CRUD. No scraping, no LLM.

**Step 1.1 — Skeleton & config.** Create `app.py`, `config.py`, `logging_config.py`, `.env.example`, `requirements.txt` (`flask`, `flask-cors`, `sqlalchemy`, `python-dotenv`, `pytest`). Config loads keys + `DECISION_THRESHOLDS` from env. Enable CORS for the Vite dev origin. Structured JSON logging with a request id. **No secrets in source.**

**Step 1.2 — Models & pragma listener.** Implement `database/db_config.py` (§3.2), `database/models.py` (ORM mirror of all 14 tables), and run `migrate.py`. App factory calls nothing destructive on boot.

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

### PHASE 3 — n8n, Atomic Claiming & Multi-Channel Outreach

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

**Step 3.5 — n8n workflow specs** (`n8n/workflows/`). n8n is scheduler/trigger, not brain:
- `morning_discovery.json`: cron 09:00 → HTTP `POST /api/v1/leads/discover` (Flask enqueues `DISCOVER`).
- `hourly_outreach_pacer.json`: cron hourly → `POST /api/v1/outreach/tick` (Flask enqueues a staggered batch respecting per-channel daily caps; the Phase-2 worker drains it).
- `adaptability_sweep.json`: cron → `POST /api/v1/campaigns/adapt` (runs §4.3 evaluation).

**DoD tests (gate):**
- 10 concurrent claims on one `SCORED` lead → exactly one `True`; stale-claim sweeper resets an old `OUTREACHING`.
- Suppressed identifier → `SKIPPED_SUPPRESSED`, no provider call; unsubscribe endpoint suppresses and blocks the next send.
- Outgoing email carries `List-Unsubscribe` + `List-Unsubscribe-Post` and a visible unsubscribe link.
- **QC gate:** a draft containing "game-changer"/"delve" or lacking the pain-point reference is rejected (`test_qc_gate.py`).
- Pacing: 40 queued emails respect the daily cap and staggered `run_after` (no burst).

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

**Step 4.5 — EOD executive report** (`services/reporting_service.py` + `n8n/workflows/eod_report.json`). Cron 23:50 → `POST /api/v1/reports/generate`: aggregate discovered/scored-by-tier/outreached-per-channel/replies/high-intent + KPI framework (bounce <2%, spam <0.1%, intent accuracy, escalation response time) into `daily_reports`; CEO agent writes the executive summary; email it.

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
python migrate.py                                      # apply schema.sql (14 tables)

# ── Run services (each in its own terminal / process) ────────────
# API server (dev)
flask --app app run --port 5000
# API server (prod)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
# Async scraper worker (dedicated process — NOT a Flask thread)
python -m scraper_worker.async_runner
# Durable job worker (pacing, retries, outreach dispatch)
python -m jobs.worker

# ── n8n (self-hosted) ────────────────────────────────────────────
cd ../n8n
docker compose up -d                                   # then import workflows/*.json
docker compose logs -f n8n

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

Extends `icp_strategy_agent.py` with a `MARKET_SCAN` job type (weekly cron via n8n) that re-runs `ICP_STRATEGY_AGENT_SYSTEM_PROMPT` (§6) against fresh SERP/Places data to surface competitor pricing shifts and under-saturated regions, writing findings to `knowledge_memory` (`category='COMPETITOR'`). No new autonomy: output only informs the CEO agent's `executive_summary` and the Learning agent's `next_experiment` — it never changes pricing or ICP on its own (§8.8 boundary).

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
- **DB hygiene:** run `PRAGMA wal_checkpoint(TRUNCATE)` on a timer (a long-lived n8n read connection can pin the WAL and bloat it); keep write transactions short; never hold one open across an LLM/network call.
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

Build strictly in order. Each gate exists because skipping it produces a bug that's invisible in development and expensive in production — a double-send, a leaked browser farm, a non-compliant email, an AI that auto-answers a pricing question it should have escalated, or an executive layer that quietly overrides a human-locked parameter.
