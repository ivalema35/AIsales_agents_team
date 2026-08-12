# MEMORY.md — Read This First in Any New Session

**Purpose:** Ye file is poore project ki conversational memory hai. Agar ye ek naya laptop hai ya naya chat session hai jisme pehle ki baatcheet yaad nahi hai — **ye file sabse pehle padho**, phir `tracker.md` (live progress log). Dono milkar poora context de dete hain jaisa purane chat me tha.

---

## 1. User kaun hai, kaise kaam karna hai

- User Hinglish me baat karta hai — main bhi Hinglish me hi respond karta hoon (simple, clear, detailed).
- **Collaboration protocol (strict):**
  1. Koi bhi development step shuru karne se pehle, us step me kya banega — simple bhasha me, poora detail ke saath — samjhaana hai, aur user ka explicit confirmation aane ke baad hi code likhna hai.
  2. Har step complete hone ke baad `tracker.md` turant update karna hai (Ongoing → Completed, agla item Pending se Ongoing me).
  3. Phase order strictly follow karna hai (Phase 1 → 2 → 3 → 4 → 5), DoD gate green hue bina agla phase start nahi karna.
- **User khud backend/server run aur test karna pasand karta hai** — jab live server chalana ho (jaise `python app.py` chalana, browser me hit karna), to sirf clear steps de do, khud mat chalao. Lekin one-off automated checks (test client se ek route hit karna, `migrate.py` chalana, pytest) khud kar sakta hoon — ye "live app chalane" wali restriction me nahi aata.
- Koi bhi risky/destructive action (delete, force push, gitignore banana) se pehle confirm karna — user ne khud kai baar explicitly bola hai "abhi mat karo, baad me bataunga" jaisi cheezein, unko respect karna.

## 2. Project kya hai

Project ka naam **AI-BOS (Enterprise AI Business Operating System)** hai — pehle ye "Autonomous AI Sales Operating System" tha, 2026-08-10 ko upgrade kiya gaya ek naye **Enterprise Executive Layer (Chapter 15 / §8)** ke saath jo Cognitive Brain Layer ke upar baithta hai.

**3-layer architecture:** Executive Layer (governs — budget/CAC ceilings, capacity throttles, sales-mode routing) → Cognitive Brain Layer (decides — AI agents, Decision Engine, QC veto) → Execution Infrastructure (acts — Flask/SQLite/Playwright/n8n).

### Authoritative docs (sab kuch inhi do me hai — baaki files delete ho chuki hain)
- **`MASTER_DEVELOPMENT_PRD.md`** — single build spec. Phases 1–5, poora DDL (16 tables), saare agent/cognition code blueprints. **Isi ke against build karna hai.**
- **`AI_Sales_Intelligence_PRD_v2.md`** — cognitive/organizational reference (agent roles, decision engine, memory tiers, Chapter 15 ke 8 executive modules).
- **`tracker.md`** — meri apni live progress log. 4 sections: Rules & Memory, Completed, Ongoing, Pending. **Har naye session me sabse pehle ye padhna hai** current status jaanne ke liye.

### Removed docs (ab exist nahi karti, dobara mat banana)
`prd.md`, `ENTERPRISE_BUSINESS_LAYER_ADDON.md`, aur original standalone "PRD v3" file — inka saara content upar wali 2 files me merge ho chuka hai (2026-08-10).

## 3. Git / GitHub setup

- Remote: `https://github.com/ivalema35/AIsales_agents_team.git`, branch `main`.
- **`.gitignore`** covers `.venv/`, `venv/` (actual folder name on this machine, no dot — fixed a real gap here 2026-08-11), `.env` (real secrets, added when real `.env` was created with real API keys), `__pycache__/`, `*.pyc`.
  - `sales_system.db` (SQLite binary) **jaan-bujh kar commit ki gayi hai** — user ne explicitly "abhi commit kar do" chuna tha jab maine gitignore vs commit ka option pucha (2026-08-11). Agar future me isme real business data aaye aur user apna mind badle, to revisit karna.
- User agla laptop change karne wala hai — isliye jitna zyada context repo (git) me ho utna better, kyunki mera internal Claude memory system is machine tak local hai, naye laptop pe transfer nahi hoga.

## 4. Build status (as of 2026-08-12 — full detail always in tracker.md, this is a curated summary not a log)

**Phase 1 (Foundation & Core REST API) — ✅ COMPLETE, DoD gate green.** Flask skeleton, 16-table DB + pragma listener, Product CRUD, Lead CRUD. All 422-not-500 validated, FK cascade confirmed live.

**Phase 2 (Async Scraper + LLM Scoring) — ✅ COMPLETE, DoD Gate P2 green.**
- Step 2.1 — Durable job queue (atomic claim, 10-thread contention tested).
- Step 2.2 — Serper.dev (Places) + Hunter.io providers, real API calls verified.
- Step 2.3 — Async scraper runner + Playwright fallback, zero browser leaks (50× + real + exception paths).
- Step 2.3b/2.3c — Full contact-enrichment waterfall (website scrape → Hunter → Serper snippets → Maps circuit-breaker, for both email and phone), rebuilt from a user-caught wrong-email bug into a 6-item verified checklist. **Real, cross-category results: phone 0/10 → 10/10, email accuracy fixed (was silently wrong on some leads, not just low-coverage).**
- Step 2.4 — First LLM calls in the project (`cognition/llm_client.py`, swappable Gemini/OpenAI; `agents/review_analyst_agent.py`; `agents/scoring_agent.py`). Decision Engine routing reproduces MASTER PRD's own DoD test exactly. Real Gemini calls proved both the positive path (genuine pain-point extraction) and graceful degradation (503/quota-exhaustion → safe defaults, no crash).

**Local dev setup:** Python venv at `backend/venv` (no dot — differs from an earlier assumption; not committed, gitignored). Real `.env` exists locally (gitignored) with Gemini/OpenAI/Serper/Hunter keys.

### Key lessons from Phase 2 (the reusable wisdom — full bug-by-bug narrative is in tracker.md §2 if ever needed)

1. **A paid enrichment API's silence is not evidence a contact doesn't exist.** Hunter can only return `@company-domain` emails; it structurally cannot see the gmail/yahoo addresses most Indian SMBs actually use. Always ask "what can this provider structurally never return?" before trusting an empty result.
2. **The single most common accuracy bug this project has hit: loose name-matching lets one business's data attach to a different lead.** Happened independently in `find_phone`, `find_website`, and `find_email` before a shared, reused fix (`_name_matches_blob()`, plus `_is_own_profile_link()` for URL-handle trust) closed all three. **Rule going forward: any new "does this result belong to this business" check must reuse these shared helpers, never a fresh bespoke check — bespoke matching has been wrong every single time it's been tried here.**
3. **Two real businesses can share a name across different cities** (e.g. "Infinity Gaming Zone" Ahmedabad vs "Infinity Gaming" Navsari) — name-matching alone cannot disambiguate this; needs real location/gazetteer logic. Known, deliberately unfixed limitation (see tracker.md §3 "Known open items").
4. **LLM model names go stale.** `gemini-2.5-flash` (MASTER PRD's named model) returned 404 for new accounts mid-project — use self-updating aliases like `gemini-flash-latest` where available.
5. **The swappable `LLM_PROVIDER` design (§4.1 below) paid for itself the first time it was needed** — when Gemini's free-tier daily quota (20 requests/day) was exhausted mid-testing, switching to OpenAI for the rest of that session's verification was a one-env-var change, not a rewrite.
6. **Test against independently-known ground truth, not just "the code runs."** Nearly every real bug above was caught by checking a result against something already verified another way (a user's own screenshot, a Google Maps read, a site's own `<title>` tag) — a green test suite alone missed all of them initially.

## 4.1 Architectural deviation — LLM provider (2026-08-11, full detail in tracker.md §A.1)
MASTER PRD hardcodes Gemini 2.5 Flash; user confirmed instead a **single swappable provider** (`config.py`: `LLM_PROVIDER` + `LLM_MODEL`, `cognition/llm_client.py` branches on it) — provider swap = one config change. `LLM_PROVIDER=gemini` is the default (genuinely free tier); `openai` is the tested fallback, already proven useful once when Gemini's daily quota ran out mid-session.

## 5. Important technical rules (full list `tracker.md` Section 1 me hai)

Quick highlights — poori list ke liye `tracker.md` dekho: secrets sirf `.env` me kabhi source me nahi, SQLite pragmas per-connection zaroori, OPT_OUT/suppression 100% rule ahead of AI processing, QC veto absolute, HUMAN_LOCKED_PARAMS (pricing/discounts/SLA) kabhi autonomous nahi, atomic claims (rowcount check) har concurrency-sensitive jagah, WhatsApp sirf official Cloud API.

---

**Bottom line for a fresh session:** Naya kaam start karne se pehle — ye file padho, phir `tracker.md` ka Section 3 (Ongoing) aur Section 4 (Pending) dekho ki abhi kahan tak kaam hua hai, phir wahi collaboration protocol follow karo (explain → confirm → build → tracker update).
