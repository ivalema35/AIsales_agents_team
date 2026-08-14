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
    target_regions       TEXT DEFAULT '[]',   -- JSON array, e.g. ["Ahmedabad","Surat"] (tracker.md A.2)
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

-- 17. PRODUCT STRATEGIES  (tracker.md A.2: ICP Strategy Agent output, versioned not overwritten)
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

-- 18. DISCOVERY RUNS  (tracker.md A.2: per product+query+region cooldown tracking for the scheduler)
CREATE TABLE IF NOT EXISTS discovery_runs (
    id            TEXT PRIMARY KEY,
    product_id    TEXT NOT NULL,
    query         TEXT NOT NULL,
    region        TEXT NOT NULL,
    last_run_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, query, region),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 19. SYSTEM SETTINGS  (Step 4.4: dashboard-controlled runtime switches, e.g. discovery/
-- outreach on-off -- checked fresh from the DB every scheduler tick so a dashboard toggle
-- takes effect within one tick, no process restart needed. Not the same as .env config,
-- which only changes at process start.)
CREATE TABLE IF NOT EXISTS system_settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
