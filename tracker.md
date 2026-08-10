# TRACKER.md — AI-BOS Development Journey Log

**Purpose:** Iss file ko main (Claude) khud maintain karunga — mera working memory aur progress log. Har development step ke baad ye file update hogi. Kisi bhi naye session/conversation me kaam resume karne se pehle ye file sabse pehle padhni hai.

**Source of truth for what to build:** `MASTER_DEVELOPMENT_PRD.md` (build spec, Phase 1–5) + `AI_Sales_Intelligence_PRD_v2.md` (cognitive/organizational reference, incl. Chapter 15).

---

## 1. Rules & Memory (Non-Negotiable)

### A. Collaboration process (how we work together on this project)
1. **Har development step shuru karne se pehle**, us step me kya hone wala hai — simple bhasha me, poora detail ke saath — samjhaunga, aur user ka confirmation aane ke baad hi aage badhunga. Bina confirmation ke code nahi likhunga.
2. **Har step complete hone ke baad**, is tracker.md ko turant update karunga — Section 3 (Ongoing) se Section 2 (Completed) me shift, aur agla item Section 4 (Pending) se Section 3 me laana.
3. **Phase order strictly follow karna hai** — Phase 1 → 2 → 3 → 4 → 5. Pichle phase ka DoD gate green hue bina agla phase start nahi karna (MASTER §5 / §9).
4. Koi bhi naya architectural decision ya deviation MASTER_DEVELOPMENT_PRD.md ke against lena ho, to pehle yahi is section me note karna, phir user se confirm karna.

### B. Non-negotiable technical/safety rules (from MASTER_DEVELOPMENT_PRD.md)
- **Secrets:** sirf `.env` me, kabhi bhi source code me hardcode nahi (config.py env-driven).
- **SQLite pragmas** (`foreign_keys`, `busy_timeout`, `journal_mode=WAL`, `synchronous=NORMAL`) per-connection set karne hain — connection listener (`db_config.py`) ke through, kahin aur nahi. Warna FK cascade silently no-op ho jata hai.
- Koi bhi write transaction LLM ya network call ke across open nahi rakhna — WAL lock storms ka risk.
- **OPT_OUT (STOP/unsubscribe) = 100% rule** — turant suppress, kisi bhi AI/LLM processing se pehle.
- **Suppression check** har single send se pehle, unconditionally — koi bypass nahi.
- **Quality Controller ka veto absolute hai** — Governance Hierarchy me sabse upar CEO ke bhi baad koi override nahi kar sakta QC ka reject.
- **HUMAN_LOCKED_PARAMS** (base pricing, discount%, ICP core definition, contractual SLA, compliance policy) — AI kabhi autonomously nahi badal sakta, hamesha human sign-off.
- Har autonomous action Decision Engine (`route_action`) se guzarna chahiye aur `agent_events` me log hona chahiye.
- **WhatsApp:** sirf official Cloud API, first-contact sirf pre-approved template se, free-form sirf 24h reply-window ke andar.
- **Playwright fallback evasion-free rehna chahiye** (no proxy rotation/fingerprinting/CAPTCHA bypass) — providers-first approach (Places/SerpAPI/Apollo) hamesha priority.
- **Atomic claims** har jagah zaroori hain (job queue, lead claiming) — `UPDATE ... WHERE status=X` + rowcount check — concurrency me double-processing nahi honi chahiye.
- **Custom pricing/negotiation** hamesha Human Escalation — AI kabhi auto-quote nahi karta (Dual Sales Mode Engine ke CUSTOM_DEV flow me bhi).

### C. Long-term project facts to remember
- Project naam: **Enterprise AI Business Operating System (AI-BOS)** — pehle "AI Sales OS" tha, ab upgrade ho chuka hai Executive layer ke saath.
- 3-layer architecture: **Executive Layer (governs)** → **Cognitive Brain Layer (decides)** → **Execution Infrastructure (acts)**.
- 16 total DB tables (11 core + 3 intelligence + 2 executive — `team_capacity`, `client_lifecycle`).
- Redundant docs already removed: `prd.md`, `ENTERPRISE_BUSINESS_LAYER_ADDON.md`, old `PRD v3` source file — sab MASTER_DEVELOPMENT_PRD.md me merge ho chuke hain.

---

## 2. Completed Modules / Steps

### Planning & Documentation
- [x] `MASTER_DEVELOPMENT_PRD.md` unified build spec (merges Technical PRD v3 + Intelligence PRD v2).
- [x] Chapter 15 / §8 — Enterprise Executive Business Layer (AI-BOS), saare 8 modules, dono PRDs me cross-referenced.
- [x] Phase 5 (Executive Business OS & Governance Layer) roadmap me add.
- [x] DDL: Table 15 (`team_capacity`), Table 16 (`client_lifecycle`), `leads.sales_route` column.
- [x] Redundant docs cleanup (`prd.md`, `ENTERPRISE_BUSINESS_LAYER_ADDON.md`, old PRD v3 file removed).
- [x] `tracker.md` set up.

### Code (backend/frontend/n8n)
- [x] **Phase 1 / Step 1.1 — Skeleton & config.** Created `backend/requirements.txt`, `backend/.env.example`, `backend/config.py` (env-driven Config class + `DECISION_THRESHOLDS`), `backend/logging_config.py` (structured JSON logs + per-request id via Flask `g`), `backend/app.py` (app factory, CORS for Vite dev origin, `/health` route). Verified via Flask test client: `/health` → 200, `{"status": "ok"}`. No secrets in source — only `.env.example` exists, real `.env` not created (no real keys available yet).

---

## 3. Ongoing Module / Step

*(Step 1.1 complete. Agla step — Phase 1 / Step 1.2 (Models & pragma listener) — user confirmation ka wait hai.)*

---

## 4. Pending Modules / Steps

### PHASE 1 — Foundation & Core REST API
- [ ] Step 1.2 — Models & pragma listener (`database/db_config.py`, `database/models.py`, `migrate.py`)
- [ ] Step 1.3 — Product CRUD (`api/products.py`)
- [ ] Step 1.4 — Lead CRUD & ingestion (`api/leads.py`)
- [ ] DoD Gate P1 (pragmas live · FK cascade · CRUD round-trip · secrets in `.env`)

### PHASE 2 — Async Scraper Process & Gemini 2.5 Flash Scoring Engine
- [ ] Step 2.1 — Durable job queue (`jobs/job_queue.py`, `jobs/worker.py`)
- [ ] Step 2.2 — Data acquisition provider interface (`services/data_acquisition/*`)
- [ ] Step 2.3 — Dedicated async scraper runner (`scraper_worker/async_runner.py`)
- [ ] Step 2.4 — Gemini scoring engine (`cognition/llm_client.py`, `agents/scoring_agent.py`)
- [ ] DoD Gate P2 (atomic claim under contention · validated scoring JSON · zero orphan browsers · decision routing correct)

### PHASE 3 — n8n, Atomic Claiming & Multi-Channel Outreach
- [ ] Step 3.1 — Atomic lead claiming (`services/lead_service.py`)
- [ ] Step 3.2 — Suppression enforcement (`services/outreach/suppression.py`)
- [ ] Step 3.3 — Compliant email (`services/outreach/email_service.py`)
- [ ] Step 3.4 — WhatsApp Cloud API (`services/outreach/whatsapp_service.py`)
- [ ] Step 3.5 — n8n workflow specs (`n8n/workflows/*`)
- [ ] DoD Gate P3 (no double-send · suppression everywhere · one-click unsubscribe · QC veto rejects bad drafts · pacing caps · official WhatsApp)

### PHASE 4 — Inbound Handler, Human-in-the-Loop, React UI & Nightly Report
- [ ] Step 4.1 — Inbound webhook + idempotency (`api/inbound.py`)
- [ ] Step 4.2 — Hard pre-classifiers (STOP/auto-reply before LLM)
- [ ] Step 4.3 — Gemini intent classifier + escalation guardrail (`agents/inbound_agent.py`)
- [ ] Step 4.4 — React dashboard (`frontend/`)
- [ ] Step 4.5 — EOD executive report (`services/reporting_service.py`)
- [ ] DoD Gate P4 (idempotent inbound · hard rules before LLM · human-in-loop · dashboard live · EOD report sends)

### PHASE 5 — Executive Business OS & Governance Layer
- [ ] Step 5.1 — Schema additions (`team_capacity`, `client_lifecycle`, `leads.sales_route`)
- [ ] Step 5.2 — Dual Sales Mode Engine (`cognition/dual_sales_engine.py`)
- [ ] Step 5.3 — Capacity & Resource Intelligence (`cognition/capacity_intelligence.py`)
- [ ] Step 5.4 — Executive & Lifecycle APIs (`api/executive.py`, `api/lifecycle.py`, `agents/lifecycle_agent.py`)
- [ ] Step 5.5 — Governance hierarchy (`cognition/decision_engine.py` extension)
- [ ] Step 5.6 — Self-evolution boundaries (`config.py`, `cognition/adaptability.py` extension)
- [ ] Step 5.7 — Executive dashboard (`ExecutiveControl.jsx`, `CapacityMeter.jsx`)
- [ ] DoD Gate P5 (sales-mode routing correct · capacity throttle works · renewal reminders on-time · governance tie-break honors rank · QC veto absolute · no autonomous write touches `HUMAN_LOCKED_PARAMS`)
