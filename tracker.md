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

### A.1 Architectural deviation — LLM provider (2026-08-11)
MASTER_DEVELOPMENT_PRD.md §2.4/§8 hardcodes Gemini 2.5 Flash (`google-genai` SDK) as THE model. User confirmed instead: **single swappable provider** — `config.py` will hold `LLM_PROVIDER` (`gemini`/`openai`/`claude`) + `LLM_MODEL`, and `cognition/llm_client.py`'s `call_json()` will branch on `LLM_PROVIDER` so swapping providers is a one-line config change, not a code rewrite. Testing abhi **OpenAI** key ke saath hoga (available key). Rest of the Decision Engine / scoring schema / confidence contract stays exactly as MASTER PRD defines it — only the underlying model call is swappable. This decision applies when we reach Step 2.4 (Gemini/LLM scoring engine); Step 2.1 (job queue) needs no LLM at all.

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
- [x] **Phase 1 / Step 1.2 — Models & pragma listener.** Created `backend/database/__init__.py`, `backend/database/schema.sql` (all 16 tables + indexes), `backend/database/db_config.py` (engine + per-connection PRAGMA listener), `backend/database/models.py` (SQLAlchemy ORM mirror of all 16 tables, incl. `UniqueConstraint` on `inbound_conversations`/`suppression_list`), `backend/migrate.py`. Verified: `migrate.py` runs clean, `journal_mode=wal` + `foreign_keys=1` confirmed live on an open session, `-wal`/`-shm` files present while a session is open, FK cascade delete tested (product delete → its lead vanishes). Fixed a stale "14 tables" reference in 3 places in MASTER_DEVELOPMENT_PRD.md (now correctly 16, post Phase-5 addition).
- [x] **Phase 1 / Step 1.3 — Product CRUD.** Created `backend/api/__init__.py`, `backend/api/products.py` (Blueprint mounted at `/api/v1/products`, routes: `GET` list w/ optional `?is_active=` filter, `GET /<id>`, `POST`, `PUT /<id>`, `DELETE /<id>`); registered blueprint in `app.py`. `target_keywords`/`pain_point_mappings` validated as JSON array/object → `422` with a clear error list on bad type or malformed request body, never `500`. Verified via a scratch Flask-test-client script against a disposable temp SQLite DB (migrated fresh, deleted after): full create→list→get→get-missing(404)→update→delete→get-after-delete(404) round-trip, `is_active` filter, and three 422 cases (bad field type, malformed JSON body, missing required field) — all passed.
- [x] **Phase 1 / Step 1.4 — Lead CRUD & ingestion.** Created `backend/api/leads.py` (Blueprint mounted at `/api/v1/leads`, routes: `GET` list w/ `?product_id=&status=` filters using `idx_leads_product_status`, `GET /<id>`, `POST` manual create, `PATCH /<id>/status`); registered blueprint in `app.py`. Status transitions kept direct/simple for now per MASTER PRD note — the atomic-claim `lead_service` logic is deferred to Phase 3. `status` PATCH and `?status=` filter validated against the 10-value enum → `422` on bad value; `product_id` validated against a real `products` row before insert → `422` (not a raw FK `IntegrityError`/500) on a dangling reference. Verified via scratch test-client script against a disposable temp DB: create→get→get-missing(404)→list-all→filter-by-product→filter-by-status→bad-status-filter(422)→status-patch→bad-status-patch(422)→patch-missing(404)→malformed-JSON(422)→**FK cascade re-confirmed** (deleting the parent product cascades the lead away, proving the pragma listener is still live) — all passed.
- [x] **Phase 1 DoD Gate — green.** All P1 criteria verified across Steps 1.1–1.4: pragmas live per-connection, FK cascade works, Product + Lead CRUD round-trip cleanly, bad JSON/bad enum/dangling FK → `422` never `500`, `/health` → 200, secrets only in `.env.example` (no real `.env` yet, no secrets in source), DB + `-wal`/`-shm` files created under WAL mode.
- [x] **Phase 2 / Step 2.1 — Durable job queue.** Created `backend/jobs/__init__.py`, `backend/jobs/job_queue.py` (`enqueue`, `claim_next` — atomic `UPDATE...WHERE status='PENDING'` + rowcount check, `mark_done`, `mark_failed` — backoff requeue or `DEAD` at `max_attempts`), `backend/jobs/worker.py` (pluggable `HANDLERS` registry via `register_handler(job_type)` decorator so Phase 2–5 job types register themselves without editing `worker.py`; `run_once`/`run_forever` poll loop — a handler exception is always caught and routed to `mark_failed`, never crashes the loop). Verified via scratch test-client script against a disposable temp DB: basic claim + re-claim-blocked, future `run_after` not claimed early, **10-thread contention on one job → exactly 1 winner**, 3 failed attempts → `DEAD` at cap (4th claim finds nothing), worker happy-path (`DONE`), failing-handler path (requeued with error recorded, loop doesn't crash), and no-registered-handler path (requeued with clear error, loop doesn't crash) — all passed.
- [x] **Setup — real API keys wired.** `backend/.env` created (gitignored) with real free-tier keys: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `SERPER_API_KEY`, `HUNTER_API_KEY`. `LLM_PROVIDER=gemini` default (swappable, §A.1). Fixed a real gap in `.gitignore`: it only listed `.venv/` but the actual venv folder on this machine is `backend/venv/` (no dot) — was untracked-but-not-ignored, one `git add -A` away from committing thousands of package files. Added `venv/` and `.env` to `.gitignore`.
- [x] **Phase 2 / Step 2.2 — Data acquisition provider interface.** Created `backend/services/__init__.py`, `backend/services/data_acquisition/__init__.py`, `base.py` (`LeadSourceProvider` ABC + `empty_lead()` standard dict shape), `serp_provider.py` (`SerperProvider` — Serper.dev **Places** endpoint, not plain web search, so results come back as structured business listings: name/website/phone/address), `b2b_provider.py` (`HunterProvider.enrich_domain()` — Hunter.io domain search for contact emails; intentionally NOT a `LeadSourceProvider` since enrichment of a known company is a different contract than discovering new ones). Added `requests` to `requirements.txt`. Places/SerpAPI providers and `playwright_fallback.py` skipped for now — no Places key, and Playwright's browser-binary install is deferred to Step 2.3 where it's actually invoked. **Verified with real live calls (user explicitly OK'd real-call testing over mocking, has credit headroom):** Serper `discover("coaching centers", location="Pune")` → 10 real business listings with correct fields; Hunter `enrich_domain("stripe.com")` → 10 real contacts with email/confidence/position. Both providers work end-to-end against the real APIs. *(Credit note: 1 Serper call used of 2,500 one-time; 1 Hunter call used of 25/month — both cheap enough to not worry about, but still worth not blasting in a loop.)*

- [x] **Phase 2 / Step 2.3 — Dedicated async scraper runner.** Installed `playwright>=1.40` + Chromium binary (added to `requirements.txt`; note the binary itself lives outside the repo in `%LOCALAPPDATA%\ms-playwright` and needs `python -m playwright install chromium` on a fresh machine). Created `services/data_acquisition/playwright_fallback.py` (`fetch_rendered()` — `headless=True`, evasion-free, `try/finally` closes page→context→browser on every path) and `scraper_worker/__init__.py` + `scraper_worker/async_runner.py`: one process, one asyncio loop, `asyncio.Semaphore(5)` cap, runs SEPARATELY from `jobs/worker.py` per MASTER §9 process topology. Handlers: `DISCOVER` (Serper → new `Lead` rows → one `ENRICH` job each) and `ENRICH` (Hunter domain-search → best contact by confidence onto the lead → status `ENRICHED` → queues `REVIEW`). Blocking provider HTTP runs via `asyncio.to_thread` with its own session (sessions aren't thread-safe) so one slow site never stalls the loop.
  - **Design decisions made here:** (a) `DISCOVER` dedupes on `(product_id, company_name)` — repeat searches of the same area are the normal case, and without this each re-run would fan out duplicate leads *and* duplicate `ENRICH` jobs, burning Hunter credits for nothing. (b) A lead with no usable website still advances to `ENRICHED` rather than failing — small businesses often have no site, and stranding them pre-pipeline would silently drop real leads; scoring downstream just sees no contact. (c) `REVIEW` jobs are queued but have no handler until Step 2.4 — the Step 2.1 queue tolerates this by design, they simply sit `PENDING`.
  - **Verified with real live calls:** `DISCOVER` → 9 real Nagpur coaching centers with website/phone/address, 9 `ENRICH` jobs queued 1:1, `DISCOVER` job `DONE`. Dedupe re-run → zero duplicate company names. 2 `ENRICH` jobs run (deliberately only 2, quota-conscious) → real emails resolved (`info@narayanaias.com`, `admin@wiceindia.com`), 8 left `PENDING`, 2 `REVIEW` jobs queued and correctly sitting `PENDING`. Failure path (ENRICH pointing at a missing lead) → job requeued with the error recorded, runner survived.
  - **DoD browser-leak gate: PASSED.** 50× `fetch_rendered` (data: URLs) + 3 real navigations + 3 deliberately failed navigations → chromium process count flat at baseline throughout, zero orphans on both the success and exception paths.
  - *Test-design note:* the first dedupe assertion (total lead count unchanged across two identical searches) was wrong and failed — a live search API legitimately returns a slightly different result set per call. Corrected to assert what dedupe actually guarantees: zero duplicate company names, and `ENRICH` jobs staying 1:1 with leads. Worth remembering when writing any future test against a live provider.

- [x] **Phase 2 / Step 2.3b — Website-first contact enrichment (accuracy fix).** Triggered by the user spotting, from the live site's own footer, that we had stored `admin@wiceindia.com` while the address the company actually publishes is `wiceindia@gmail.com`.
  - **Root cause (verified against Hunter's raw response, not assumed):** Hunter did *not* fabricate the address — `source_type: "found"`, `confidence: 85`, real sources including the company's own blog pages. The failure is structural: **Hunter's domain-search can only ever return `@thatdomain` addresses**, so any SMB whose real contact is a gmail/yahoo address is invisible to it. Sampling 4 discovered companies, **2 of 4 (`atlantacomputer.in`, `calibersnova.com`) had no domain email at all** and would have stayed permanently uncontactable; a 3rd (`narayanaias.com`) had a second gmail Hunter couldn't see. This is the norm, not an edge case, for the Indian SMB segment this system targets.
  - **Built `services/data_acquisition/website_scraper.py`:** `scrape_emails()` (plain `requests`, free — tries `https`/`www`/`http` variants plus `/contact`, `/contact-us`, stops at first hit, caps pages), `scrape_emails_rendered()` (Playwright fallback for JS-only sites), `is_valid_contact_email()`, `is_role_account()`, `belongs_to_company()`, `rank_candidates()`.
  - **Two real bugs found and fixed during testing:** (1) servers returning **406** to header-less requests (`atlantacomputer.in`) — fixed by sending a real `Accept`/`User-Agent`; this is compatibility, not evasion. (2) **Foreign-domain contamination** — extracting every address on a page also picks up vendors quoted in blog posts and the web designer's credit line, which would mean emailing a completely unrelated business. `belongs_to_company()` now accepts only the company's own domain/subdomains plus known free-webmail providers, and is applied to Hunter's output too.
  - **Rewrote `_handle_enrich`** to be website-first: free scrape → rank → call Hunter **only** when the site yielded nothing or role accounts only (a named decision-maker is worth a credit; `info@` off their own site can't be improved on). A Hunter failure is caught and never discards the free result or fails the job. Contact name/role are only overwritten when actually known — never invented.
  - **Ranking rationale** (deliverability is a hard PRD constraint, bounce <2%, so *reachable* beats *senior-sounding*): named person on own site → role account on own site → Hunter named contact → Hunter generic.
  - **Design decision — no schema change.** Best address goes to `leads.primary_email`, the rest are logged. Storing alternates would need a new column against the PRD's fixed 16-table schema, and re-scraping is free, so nothing is lost. Revisit if Phase 3 bounce-handling needs fallbacks.
  - **Results:** all 4 sampled domains now resolve a correct contact (**4/4, vs Hunter's 2/4 — one of which was the wrong address**), including `wiceindia.com → wiceindia@gmail.com`, the exact address from the footer. Hunter spend on those 3 real leads dropped from 3 credits to **0**. Verified by 60+ assertions: junk filter (image filenames, Sentry DSNs, `you@example.com`-style placeholders, `noreply@`), role detection, `mailto:`-first extraction, ownership filtering, all four ranking tiers, empty/None inputs, no-website leads still advancing rather than stranding, Hunter-throws path, and one REVIEW job per enriched lead.

---

## 3. Ongoing Module / Step

*(Steps 2.3 + 2.3b complete. Agla step — Phase 2 / Step 2.4 (LLM scoring engine: `cognition/llm_client.py` + `agents/scoring_agent.py`, plus the `REVIEW` handler that the queued REVIEW jobs are waiting on) — user confirmation ka wait hai. Ek open question hai: `sales_system.db` ko gitignore me daalna chahiye — user se confirm karna hai.)*

**API credit ledger (free tiers):** Serper ~5 calls used of 2,500 one-time · Hunter ~4 of 25/month · LLM 0 so far (Step 2.4 will be the first). Website scraping is free and now carries most of the enrichment load.

---

## 4. Pending Modules / Steps

### PHASE 2 — Async Scraper Process & LLM Scoring Engine
- [ ] Step 2.4 — LLM scoring engine (`cognition/llm_client.py`, `agents/scoring_agent.py`) + the `REVIEW` handler (review→weakness-code extraction) the queued REVIEW jobs are waiting on
- [ ] DoD Gate P2 (atomic claim under contention ✅ done in 2.1 · validated scoring JSON · zero orphan browsers ✅ done in 2.3 · decision routing correct)

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
