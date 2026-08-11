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
- **`.gitignore`** abhi sirf `.venv/`, `__pycache__/`, `*.pyc` cover karta hai.
  - `.env` (real secrets) abhi ignore list me **nahi** hai kyunki real `.env` file abhi bani hi nahi (sirf `.env.example` hai, blank). Jab real `.env` banegi real API keys ke saath, tab **pehle usko `.gitignore` me daalna zaroori hai** commit karne se pehle.
  - `sales_system.db` (SQLite binary) **jaan-bujh kar commit ki gayi hai** — user ne explicitly "abhi commit kar do" chuna tha jab maine gitignore vs commit ka option pucha (2026-08-11). Agar future me isme real business data aaye aur user apna mind badle, to revisit karna.
- User agla laptop change karne wala hai — isliye jitna zyada context repo (git) me ho utna better, kyunki mera internal Claude memory system is machine tak local hai, naye laptop pe transfer nahi hoga.

## 4. Build status (as of 2026-08-11 — verify against tracker.md, ye stale ho sakta hai)

**Phase 1 (Foundation & Core REST API) — in progress:**
- ✅ Step 1.1 — Flask skeleton (`app.py`, `config.py`, `logging_config.py`, `requirements.txt`, `.env.example`). `/health` verified working.
- ✅ Step 1.2 — Database (`database/schema.sql` — 16 tables, `database/db_config.py` — pragma listener, `database/models.py` — ORM, `migrate.py`). Verified: WAL mode live, FK cascade works.
- ⏳ Step 1.3 (Product CRUD) — next, not started yet.
- Phases 2–5 — not started.

**Local dev setup:** Python venv at `backend/.venv` (not committed — naye laptop pe recreate karna: `cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`). Real `.env` abhi tak nahi bani.

## 5. Important technical rules (full list `tracker.md` Section 1 me hai)

Quick highlights — poori list ke liye `tracker.md` dekho: secrets sirf `.env` me kabhi source me nahi, SQLite pragmas per-connection zaroori, OPT_OUT/suppression 100% rule ahead of AI processing, QC veto absolute, HUMAN_LOCKED_PARAMS (pricing/discounts/SLA) kabhi autonomous nahi, atomic claims (rowcount check) har concurrency-sensitive jagah, WhatsApp sirf official Cloud API.

---

**Bottom line for a fresh session:** Naya kaam start karne se pehle — ye file padho, phir `tracker.md` ka Section 3 (Ongoing) aur Section 4 (Pending) dekho ki abhi kahan tak kaam hua hai, phir wahi collaboration protocol follow karo (explain → confirm → build → tracker update).
