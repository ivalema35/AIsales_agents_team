# Product Requirements Document (PRD): Production-Grade Autonomous AI Sales Multi-Agent System (v3 Architecture)

---

## 1\. Executive Summary & Core System Objectives

The **Autonomous AI Sales Multi-Agent System** is a 24/7 self-operating B2B sales development representative (SDR) platform built to automate prospecting, research, lead scoring, and hyper-personalized outreach across **multiple dynamic products and services**.

### Key Production Enhancements (v3 Architecture):

1. **Dynamic Multi-Product Management:** Admins register products/services via React UI without changing code.  
2. **Dedicated Async Scraper Process:** Async Playwright runner with strict browser context cleanup (`try...finally`) to eliminate memory leaks and event loop thread conflicts.  
3. **Atomic Lead Claiming:** Race-condition-proof state updates (`UPDATE leads SET status='OUTREACHING' WHERE id=? AND status='SCORED'`) preventing double outreach.  
4. **Non-Blocking Pacing:** Zero `time.sleep()` in threadpools; campaign delays owned by durable DB job queue and n8n schedulers.  
5. **SQLite WAL Mode with Strict Pragmas:** Sub-millisecond local reads/writes with `PRAGMA foreign_keys=ON;` and `busy_timeout=10000;`.  
6. **Active LLM Integration:** Powered by `gemini-2.5-flash` via OpenRouter/Direct API.  
7. **Compliance & Deliverability Guardrails:** Domain warmup, SPF/DKIM/DMARC enforcement, 1-click unsubscribes, and official/warm WhatsApp gateway options.

---

## 2\. System Architecture & Component Mapping

┌──────────────────────────────────────────────────────────────────────────────────┐

│                                  REACT / HTML FRONTEND                           │

│                     (Dynamic Product Entry, Pipeline View, Logs)                 │

└────────────────────────────────────────┬─────────────────────────────────────────┘

                                         │ REST API

                                         ▼

┌──────────────────────────────────────────────────────────────────────────────────┐

│                         PYTHON FLASK (CENTRAL BRAIN & MANAGER)                    │

│  \- SQLAlchemy ORM Models (Dynamic Products, Leads, Scores, Conversations)        │

│  \- Atomic State Transition Engine (Prevents Race Conditions)                     │

│  \- Gemini 2.5 Flash LLM Scoring & Intent Classification Engine                   │

└───────────────────────────┬──────────────────────────────────┬───────────────────┘

                            │ Reads & Writes                   │ REST API / Webhooks

                            ▼                                  ▼

┌──────────────────────────────────────┐            ┌──────────────────────────────┐

│  SQLITE DB (sales\_system.db \- WAL)   │            │   n8n AUTOMATION ENGINE      │

│  \- Single File Local Storage         │            │ \- Cron Schedulers & Pacing   │

│  \- PRAGMA foreign\_keys=ON            │            │ \- Inbound Webhook Receiver   │

│  \- PRAGMA busy\_timeout=10000         │            │ \- Resend / WhatsApp Sender   │

└───────────────────▲──────────────────┘            └──────────────────────────────┘

                    │ Reads & Writes

┌───────────────────┴──────────────────┐

│   ASYNC PLAYWRIGHT SCRAPER WORKER    │

│  \- Dedicated Async Event Loop        │

│  \- Strict Context & Memory Cleanup   │

│  \- Google Maps & Review Extractor    │

└──────────────────────────────────────┘

---

## 3\. Database Schema DDL (SQLite)

\-- SQLite Database Schema for sales\_system.db (WAL Mode)

\-- 1\. DYNAMIC PRODUCTS TABLE

CREATE TABLE IF NOT EXISTS products (

    id TEXT PRIMARY KEY,

    title TEXT NOT NULL,

    description TEXT NOT NULL,

    target\_keywords TEXT DEFAULT '\[\]', \-- JSON Array

    value\_proposition TEXT,

    pain\_point\_mappings TEXT DEFAULT '{}', \-- JSON Object

    priority INTEGER DEFAULT 1,

    is\_active INTEGER DEFAULT 1,

    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    updated\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP

);

\-- 2\. LEADS TABLE

CREATE TABLE IF NOT EXISTS leads (

    id TEXT PRIMARY KEY,

    product\_id TEXT NOT NULL,

    company\_name TEXT NOT NULL,

    website\_url TEXT,

    primary\_email TEXT,

    primary\_phone TEXT,

    whatsapp\_number TEXT,

    contact\_person\_name TEXT,

    contact\_person\_role TEXT,

    status TEXT DEFAULT 'DISCOVERED', \-- DISCOVERED, ENRICHED, SCORED, OUTREACHING, OUTREACHED, ENGAGED, HOT\_LEAD, CONVERTED, REJECTED

    source TEXT,

    region\_location TEXT,

    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    updated\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    FOREIGN KEY (product\_id) REFERENCES products(id) ON DELETE CASCADE

);

\-- 3\. FIRMOGRAPHICS TABLE

CREATE TABLE IF NOT EXISTS lead\_firmographics (

    id TEXT PRIMARY KEY,

    lead\_id TEXT UNIQUE NOT NULL,

    linkedin\_url TEXT,

    company\_size\_range TEXT,

    industry TEXT,

    remote\_work\_indicators TEXT DEFAULT '{}', \-- JSON Object

    tech\_stack TEXT DEFAULT '\[\]', \-- JSON Array

    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    FOREIGN KEY (lead\_id) REFERENCES leads(id) ON DELETE CASCADE

);

\-- 4\. REVIEW INSIGHTS TABLE

CREATE TABLE IF NOT EXISTS lead\_review\_insights (

    id TEXT PRIMARY KEY,

    lead\_id TEXT NOT NULL,

    review\_source TEXT DEFAULT 'GOOGLE\_REVIEWS',

    average\_rating REAL,

    total\_reviews\_count INTEGER,

    pain\_points\_extracted TEXT DEFAULT '\[\]', \-- JSON Array

    sentiment\_score REAL,

    raw\_review\_snippets TEXT DEFAULT '\[\]', \-- JSON Array

    analyzed\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    FOREIGN KEY (lead\_id) REFERENCES leads(id) ON DELETE CASCADE

);

\-- 5\. LEAD SCORES TABLE

CREATE TABLE IF NOT EXISTS lead\_scores (

    id TEXT PRIMARY KEY,

    lead\_id TEXT UNIQUE NOT NULL,

    score INTEGER NOT NULL, \-- 0 to 100

    tier TEXT NOT NULL, \-- HOT, WARM, COLD

    scoring\_breakdown TEXT DEFAULT '{}', \-- JSON Object

    justification TEXT,

    evaluated\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    FOREIGN KEY (lead\_id) REFERENCES leads(id) ON DELETE CASCADE

);

\-- 6\. OUTREACH LOGS TABLE

CREATE TABLE IF NOT EXISTS outreach\_logs (

    id TEXT PRIMARY KEY,

    lead\_id TEXT NOT NULL,

    channel TEXT NOT NULL, \-- EMAIL, CONTACT\_FORM, WHATSAPP

    message\_subject TEXT,

    message\_body TEXT NOT NULL,

    status TEXT NOT NULL, \-- SENT, FAILED, DELIVERED

    sent\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    FOREIGN KEY (lead\_id) REFERENCES leads(id) ON DELETE CASCADE

);

\-- 7\. INBOUND CONVERSATIONS TABLE

CREATE TABLE IF NOT EXISTS inbound\_conversations (

    id TEXT PRIMARY KEY,

    lead\_id TEXT NOT NULL,

    channel TEXT NOT NULL, \-- EMAIL, WHATSAPP

    sender\_type TEXT NOT NULL, \-- LEAD, AI\_AGENT, HUMAN\_REP

    message\_content TEXT NOT NULL,

    intent\_detected TEXT, \-- INTERESTED, DEMO\_REQUESTED, OBJECTION, NOT\_INTERESTED, SPAM

    ai\_suggested\_response TEXT,

    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,

    FOREIGN KEY (lead\_id) REFERENCES leads(id) ON DELETE CASCADE

);

\-- 8\. DAILY REPORTS TABLE

CREATE TABLE IF NOT EXISTS daily\_reports (

    id TEXT PRIMARY KEY,

    report\_date TEXT UNIQUE NOT NULL,

    metrics\_summary TEXT DEFAULT '{}', \-- JSON Object

    executive\_summary\_text TEXT,

    generated\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP

);

\-- INDEXES

CREATE INDEX IF NOT EXISTS idx\_leads\_product\_status ON leads (product\_id, status);

CREATE INDEX IF NOT EXISTS idx\_lead\_scores\_tier ON lead\_scores (tier, score DESC);

---

## 4\. SQLite Configuration & Connection Pragmas

To enforce cascade deletions and prevent locking issues:

\# database/db\_config.py

import sqlite3

from sqlalchemy import event

from sqlalchemy.engine import Engine

@event.listens\_for(Engine, "connect")

def set\_sqlite\_pragma(dbapi\_connection, connection\_record):

    if isinstance(dbapi\_connection, sqlite3.Connection):

        cursor \= dbapi\_connection.cursor()

        cursor.execute("PRAGMA journal\_mode=WAL;")

        cursor.execute("PRAGMA foreign\_keys=ON;")

        cursor.execute("PRAGMA synchronous=NORMAL;")

        cursor.execute("PRAGMA busy\_timeout=10000;") \# 10-second timeout

        cursor.close()

---

## 5\. Atomic State Transitions (TOCTOU Fix)

Prevents race conditions when workers process leads:

\# services/lead\_service.py

def claim\_lead\_for\_outreach(db, lead\_id):

    """

    Atomically transitions lead status from SCORED to OUTREACHING.

    Returns True if successfully claimed, False if already claimed by another worker.

    """

    result \= db.execute(

        text("UPDATE leads SET status \= 'OUTREACHING' WHERE id \= :id AND status \= 'SCORED'"),

        {"id": lead\_id}

    )

    db.commit()

    return result.rowcount \> 0

---

## 6\. Async Playwright Worker with Strict Memory Cleanup

\# scrapers/async\_scraper\_worker.py

import asyncio

from playwright.async\_api import async\_playwright

async def scrape\_google\_maps\_async(query, max\_results=30):

    async with async\_playwright() as p:

        browser \= await p.chromium.launch(headless=True)

        context \= await browser.new\_context(viewport={'width': 1280, 'height': 800})

        page \= await context.new\_page()

        try:

            url \= f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

            await page.goto(url, timeout=30000)

            await page.wait\_for\_selector('div\[role="feed"\]', timeout=10000)

            

            \# Perform scrolling and extraction...

            cards \= await page.query\_selector\_all('div\[role="article"\]')

            results \= \[\]

            for card in cards\[:max\_results\]:

                \# Extract card details...

                pass

            return results

        finally:

            \# STRICT CLEANUP TO PREVENT MEMORY LEAKS

            await page.close()

            await context.close()

            await browser.close()

---

## 7\. Dynamic Gemini 2.5 Flash LLM Scoring

\# services/ai\_scoring\_service.py

import google.generativeai as genai

def score\_lead\_with\_gemini(product\_info, lead\_data, review\_data):

    genai.configure(api\_key="YOUR\_GEMINI\_API\_KEY")

    model \= genai.GenerativeModel('gemini-2.5-flash')

    

    prompt \= f"""

    SYSTEM ROLE: B2B Lead Scoring Agent.

    PRODUCT TITLE: {product\_info\['title'\]}

    DESCRIPTION: {product\_info\['description'\]}

    VALUE PROP: {product\_info\['value\_proposition'\]}

    LEAD DETAILS:

    Company: {lead\_data\['company\_name'\]}

    Extracted Review Complaints: {review\_data.get('pain\_points\_extracted', \[\])}

    Remote Team Indicator: {lead\_data.get('remote\_work\_indicators', {})}

    Task: Return JSON format:

    {{

      "score": \<0-100\>,

      "tier": "\<HOT|WARM|COLD\>",

      "justification": "\<brief reason\>"

    }}

    """

    response \= model.generate\_content(prompt)

    return response.text

---

## 8\. Division of Responsibilities

| Subsystem | Owner | Execution Mechanism |
| :---- | :---- | :---- |
| **Products & UI REST API** | Python Flask | React Frontend REST endpoints (`/api/v1/...`). |
| **Database & Atomic Locks** | SQLite (WAL) | Local ACID database file with `PRAGMA foreign_keys=ON;`. |
| **Web Scraping Engine** | Async Playwright Worker | Dedicated Async Process (`asyncio` loop) with `try...finally` browser cleanup. |
| **Lead Scoring & Intent** | Flask \+ Gemini 2.5 Flash | Dynamic context injection into `gemini-2.5-flash` API. |
| **Scheduling & Rate Pacing** | n8n Orchestrator | Cron Schedulers (09:00 AM scraping trigger, hourly outreach batching, 11:50 PM EOD report). |
| **Outreach Dispatchers** | n8n Gateway Nodes | Resend API (Email) & Evolution WhatsApp Cloud API. |

---

## 9\. Implementation Roadmap (Phases)

| Phase | Duration | Scope & Key Deliverables |
| :---- | :---- | :---- |
| **Phase 1: Foundation & DB** | Week 1–2 | SQLite WAL DB, PRAGMA event listeners, Flask REST API endpoints, Dynamic Product CRUD. |
| **Phase 2: Scrapers & Scoring** | Week 3–4 | Async Playwright scraper worker, memory leak cleanup tests, Gemini 2.5 Flash scoring integration. |
| **Phase 3: n8n Outreach & Pacing** | Week 5–6 | Atomic lead claiming logic, n8n Cron triggers, Resend email dispatch, Evolution WhatsApp API. |
| **Phase 4: Inbound & React UI** | Week 7–8 | Webhook reply listener, instant high-intent alerts, React pipeline dashboard, Daily EOD reporting. |

