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
    target_country       TEXT DEFAULT 'IN',   -- ISO 3166-1 alpha-2, phone-parsing default region
    -- Phase 7 Step 7.1: human-set boundary the ICP agent works inside (MASTER §5A Phase 7).
    target_business_categories TEXT DEFAULT '[]',  -- JSON array, e.g. ["dental clinic","law firm"]
    target_person_roles        TEXT DEFAULT '[]',  -- JSON array, e.g. ["CEO","Property Manager"]
    -- Phase 9 Step 9.3: day-offsets between follow-up touches, e.g. [3,7] = touch 2 three
    -- days after touch 1, touch 3 seven days after touch 2, then stop. Empty = no
    -- follow-ups at all for this product (today's single-touch behavior, unchanged).
    followup_cadence_days       TEXT DEFAULT '[]',  -- JSON array of integers
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LEADS
CREATE TABLE IF NOT EXISTS leads (
    id                   TEXT PRIMARY KEY,
    product_id           TEXT NOT NULL,
    company_name         TEXT NOT NULL,
    website_url          TEXT,
    instagram_url        TEXT,
    facebook_url         TEXT,
    linkedin_url         TEXT,
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
    provider_message_id TEXT,                 -- Meta wamid (WhatsApp) or Resend email id
    read_at          TIMESTAMP,                -- set by a real read-receipt/open webhook
    subject_candidates TEXT,                  -- JSON array, Phase 8 Step 8.4 -- every subject
                                                -- candidate generated, not just the chosen one
    -- Phase 9 Step 9.4 -- real count of Resend "email.opened" events for this send
    -- (EMAIL only; WhatsApp has no open/read-receipt webhook today, so this stays 0
    -- there, never inferred). read_at only ever marks the FIRST open; this counts every
    -- one, real signal for "opened repeatedly, never replied" escalation.
    open_count       INTEGER DEFAULT 0,
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
    is_read              INTEGER DEFAULT 0,    -- Dashboard's Recent Replies grid -- "Mark as read"
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

-- 20. SYSTEM HEARTBEATS  (Phase 6 Step 6.1: liveness for the long-running background
-- processes. Deliberately a DB row, NOT a `systemctl is-active` shell-out -- the API
-- process must never need root, and the same code has to work on a dev machine where
-- none of these are systemd units. A process is considered DOWN by comparing
-- last_seen_at against a staleness window at READ time; nothing marks itself dead,
-- because a process that has crashed cannot write its own tombstone.)
CREATE TABLE IF NOT EXISTS system_heartbeats (
    process_name  TEXT PRIMARY KEY,   -- e.g. 'jobs.worker'
    status        TEXT NOT NULL DEFAULT 'RUNNING',  -- RUNNING, IDLE, ERROR
    detail        TEXT DEFAULT '{}',  -- JSON: small per-process context
    -- How often THIS process is expected to beat. Non-negotiable for a correct reader:
    -- these processes loop at wildly different rates (worker ~2s, scraper ~3s, inbound
    -- poller 120s, discovery scheduler 300s), so a single global staleness window is
    -- always wrong -- either the scheduler reads as permanently DOWN while healthy, or
    -- the window is widened until a genuinely dead worker stays invisible for minutes.
    -- Each process declares its own rate; the reader compares against that (Step 6.2).
    expected_interval_seconds INTEGER NOT NULL DEFAULT 60,
    last_seen_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Phase 7 Step 7.3 -- multiple people per lead (today `leads` holds exactly one contact
-- via contact_person_name/_role/primary_email/primary_phone, which those columns keep
-- doing unchanged as the canonical outreach target). This table is purely additive --
-- populated later by Step 7.4 (Hunter's discarded contact fields) and Step 7.5
-- (role-targeted LinkedIn person discovery).
CREATE TABLE IF NOT EXISTS lead_contacts (
    id                TEXT PRIMARY KEY,
    lead_id           TEXT NOT NULL,
    full_name         TEXT,
    role              TEXT,
    seniority         TEXT,
    department        TEXT,
    email             TEXT,
    phone             TEXT,
    linkedin_url      TEXT,
    is_decision_maker INTEGER DEFAULT 0,
    source            TEXT,   -- e.g. 'HUNTER', 'LINKEDIN'
    confidence        REAL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Phase 8 Step 8.1 -- admin-authored message STRUCTURE, not final copy (tracker.md A.7:
-- deliberate deviation from a rigid fill-in-the-blank "slots" design -- `sections` is an
-- ordered list of GUIDELINES the AI follows while writing its own adaptive, personalized
-- draft, not literal template pieces it substitutes into). `product_id` nullable = a
-- global default for that channel; resolution order (Step 8.3): product+channel exact
-- match -> global channel default -> no format at all (today's free-form drafting,
-- unchanged). Versioned like product_strategies (status ACTIVE/SUPERSEDED, never
-- overwritten) so a format change never invalidates the performance history Phase 9
-- measures.
CREATE TABLE IF NOT EXISTS message_formats (
    id          TEXT PRIMARY KEY,
    product_id  TEXT,                    -- NULL = global default for this channel
    channel     TEXT NOT NULL,           -- 'EMAIL' or 'WHATSAPP'
    sections    TEXT NOT NULL,           -- JSON array of guideline strings, ordered
    version     INTEGER NOT NULL DEFAULT 1,
    status      TEXT DEFAULT 'ACTIVE',   -- ACTIVE, SUPERSEDED
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Phase 8 Step 8.2 -- the AI SELECTS from this library per lead/product, it never
-- invents a URL. A format slot that asks for a demo link and finds no matching active
-- asset renders the message without that slot rather than fabricating one.
CREATE TABLE IF NOT EXISTS content_assets (
    id          TEXT PRIMARY KEY,
    product_id  TEXT,                    -- NULL = available to any product
    asset_type  TEXT NOT NULL,           -- DEMO_URL, VIDEO_URL, CASE_STUDY, TESTIMONIAL, TEXT_BLOCK
    title       TEXT NOT NULL,
    value       TEXT NOT NULL,           -- the URL, or the text itself for TEXT_BLOCK
    tags        TEXT DEFAULT '[]',       -- JSON array, for matching against a lead's pain points
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Phase 9 Step 9.3 -- per-lead+channel follow-up cadence state. Only ever created when
-- the lead's product has a real cadence configured (products.followup_cadence_days) --
-- no cadence means no row means today's single-touch-only behavior, unchanged. Every
-- send this drives still goes through the exact same OUTREACH_EMAIL/OUTREACH_WA job
-- handlers as a fresh touch -- suppression/QC/pacing all apply identically, every touch.
CREATE TABLE IF NOT EXISTS outreach_sequences (
    id                TEXT PRIMARY KEY,
    lead_id           TEXT NOT NULL,
    channel           TEXT NOT NULL,       -- 'EMAIL' or 'WHATSAPP'
    original_sent_at  TIMESTAMP NOT NULL,  -- touch 1's sent_at, for "replied since?" checks
    next_step         INTEGER NOT NULL DEFAULT 2,  -- touch number about to be sent next
    max_steps         INTEGER NOT NULL,    -- total touches configured (len(cadence) + 1)
    next_run_at       TIMESTAMP NOT NULL,
    status            TEXT DEFAULT 'ACTIVE',   -- ACTIVE, CLAIMED, COMPLETED, STOPPED
    terminal_reason   TEXT,                -- REPLIED, SUPPRESSED, MAX_STEPS_REACHED
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Phase 9 Step 9.5 -- admin composes + submits a real WhatsApp template from the CRM
-- (real Meta Create Template API call), mirroring its real Meta-side approval state
-- here instead of only in code (TEMPLATE_LIBRARY). `purpose` distinguishes a first-
-- touch template from a FOLLOW_UP one -- a real gap found live testing Step 9.3: a
-- WhatsApp follow-up had no choice but to resend the exact same first-touch template
-- word for word, since Meta only allows pre-approved templates and none existed yet
-- specifically written as a brief nudge.
CREATE TABLE IF NOT EXISTS whatsapp_templates (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL UNIQUE,  -- Meta's own template name (lowercase_underscored)
    language          TEXT NOT NULL DEFAULT 'en',
    category          TEXT NOT NULL,         -- Meta's real categories: MARKETING, UTILITY, AUTHENTICATION
    purpose           TEXT NOT NULL DEFAULT 'FIRST_TOUCH',  -- FIRST_TOUCH or FOLLOW_UP
    body_text         TEXT NOT NULL,         -- with {{1}}, {{2}} placeholders, Meta's own syntax
    variable_labels   TEXT DEFAULT '[]',     -- JSON array, what each {{n}} means, e.g. ["company_name"]
    -- DRAFT: AI-authored, awaiting admin review, never yet sent to Meta (Step 9.6).
    -- PENDING: submitted to Meta (by an admin directly, or an admin-approved AI draft),
    -- awaiting Meta's own decision. APPROVED/REJECTED: Meta's own decision. ADMIN_REJECTED:
    -- an admin rejected a DRAFT before it ever reached Meta -- terminal, no Meta call made.
    status            TEXT DEFAULT 'PENDING',
    rejection_reason  TEXT,
    -- ADMIN: submitted directly via the dashboard form, real Meta call made immediately
    -- (today's only behavior before Step 9.6). AI: drafted by the adaptive-template loop,
    -- starts as DRAFT, never reaches Meta without an explicit admin approve action.
    origin            TEXT DEFAULT 'ADMIN',
    -- Only set for origin='AI' rows -- the drafting agent's own <=40-word explanation of
    -- why this candidate addresses the real signal it was given, so an admin reviewing a
    -- DRAFT can judge it informed, not blind.
    reasoning         TEXT,
    meta_template_id  TEXT,                  -- Meta's own returned id for this template
    -- NULL = shared/global (usable by every product); set = only this product may use it.
    -- Optional, not mandatory, deliberately (tracker.md Step 9.5 follow-up): each new
    -- product-specific template needs its own separate Meta approval, so defaulting to
    -- shared keeps that real cost down while still allowing a product with a genuinely
    -- distinct pitch to get its own.
    product_id        TEXT REFERENCES products(id),
    is_active         INTEGER DEFAULT 1,  -- manual kill-switch, independent of Meta's own status
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
CREATE INDEX IF NOT EXISTS idx_lead_contacts_lead    ON lead_contacts (lead_id);
CREATE INDEX IF NOT EXISTS idx_message_formats_scope ON message_formats (product_id, channel, status);
CREATE INDEX IF NOT EXISTS idx_content_assets_scope  ON content_assets (product_id, asset_type, is_active);
CREATE INDEX IF NOT EXISTS idx_sequences_due          ON outreach_sequences (status, next_run_at);
CREATE INDEX IF NOT EXISTS idx_sequences_lead_channel  ON outreach_sequences (lead_id, channel);
CREATE INDEX IF NOT EXISTS idx_wa_templates_status     ON whatsapp_templates (status, purpose);
CREATE INDEX IF NOT EXISTS idx_wa_templates_product     ON whatsapp_templates (product_id);
CREATE INDEX IF NOT EXISTS idx_discovery_runs_lookup  ON discovery_runs (product_id, last_run_at);
