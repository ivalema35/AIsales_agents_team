# AI Sales Intelligence PRD v2: Autonomous AI Sales Operating System (The Brain Layer)

**Document Version:** 2.3.0-INTELLIGENCE  
**System Classification:** Enterprise Autonomous Multi-Agent Sales Operating System  
**Layer Focus:** Autonomous Cognition, Decision-Making, Strategy, Adaptability, Memory & Organizational Orchestration  
**v2.1 Addendum:** Chapter 15 — Enterprise Executive Business & Operating System Layer (AI-BOS). Implementation blueprints for the modules below live in `MASTER_DEVELOPMENT_PRD.md` §8 (spec) and Phase 5 (§5, build order); this chapter defines the cognitive/strategic contract, MASTER defines the code.

**v2.3 Addendum (2026-08-19):** Chapter 16 — Multi-Channel Engagement & Adaptive Messaging Layer. Written *after* the system went live against real businesses, from the operator's own post-launch requirements plus every capability this document specified but deferred for lack of real data (notably §6/§6.1's learning loop and §12's Voice SDR Agent). Build order: `MASTER_DEVELOPMENT_PRD.md` §5A, Phases 6–10.

**v2.2 Amendment (2026-08-13, implemented):** the ICP & Strategy Agent (§2.1.C below) is no longer just a cognitive-contract definition — it is live code as of `MASTER_DEVELOPMENT_PRD.md` Phase 3 Step 3.5 (`agents/icp_strategy_agent.py`). n8n, named throughout this document as part of the Technical Execution Layer, was dropped from the actual build (see MASTER's §3.5 amendment / `tracker.md` §A.2) — its scheduler/trigger role is now a dedicated in-process Python worker (`jobs/discovery_scheduler.py`), which also autonomously triggers the ICP & Strategy Agent per product rather than that being a manual/CEO-agent-initiated step.

---

## Executive Summary & Architectural Mandate

The Technical PRD (v3) defined the **Execution Infrastructure** (Flask, SQLite WAL, Playwright, n8n, Resend, WhatsApp Cloud API). This document—**AI Sales Intelligence PRD v2**—defines the **Cognitive Brain Layer** that sits directly above that execution layer.

Where traditional automation relies on deterministic IF/THEN rules, the **AI Sales Operating System (AI-SOS)** operates as an autonomous, self-correcting, adaptive organization. It plans campaigns, analyzes Ideal Customer Profiles (ICPs), evaluates sentiment, auto-adjusts messaging strategies when conversion drops, maintains multi-tiered memory, and enforces strict self-evaluation and human escalation guardrails.

\+-----------------------------------------------------------------------------------+

|                        ENTERPRISE COGNITIVE BRAIN LAYER                           |

|  \- CEO & Supervisor Agents         \- Decision & Planning Engines                  |

|  \- Adaptive Learning Loops         \- Multi-Tiered Memory (Working, Campaign, Vector) |

\+-----------------------------------------------------------------------------------+

                                         │

                         Structured Agent Intent & Instructions

                                         ▼

\+-----------------------------------------------------------------------------------+

|                     TECHNICAL EXECUTION LAYER (PRD v3)                            |

|  \- Flask REST API                  \- SQLite WAL Engine \+ ThreadPool               |

|  \- Playwright Scrapers             \- In-process Discovery Scheduler               |

\+-----------------------------------------------------------------------------------+

---

## 1\. AI Sales Philosophy & Core Principles

The AI Sales OS operates on five foundational cognitive principles that dictate all autonomous reasoning:

### 1.1 Fundamental Operating Principles

1. **Value-First Engagement over Pitch Spam:** The system shall never pitch features directly without establishing a contextual, value-driven hook mapped to verified operational pain points.  
2. **Contextual Authenticity:** Outreach must read as hyper-personalized, one-to-one human communication. Generic, templated "AI-sounding" jargon (e.g., *"I hope this email finds you well"*, *"delve"*, *"game-changer"*) is strictly forbidden.  
3. **Radical Truthfulness & Zero Hallucination:** The AI must never invent product capabilities, fake customer testimonials, promise unauthorized discounts, or make false commitments regarding delivery timelines.  
4. **Autonomous Adaptability with Guardrails:** The system has full autonomy to iterate on subject lines, value propositions, and targeting parameters within predefined business and safety guardrails.  
5. **Respect for Prospect Boundaries:** Any opt-out signal (`STOP`, `unsubscribe`, `not interested`, hostile replies) must be respected immediately and permanently across all channels before any further AI processing occurs.

### 1.2 Opportunity Prioritization Framework

The system ranks outreach opportunities using a **Business Value vs. Conversion Probability Matrix**:

$$\\text{Priority Score} \= (\\text{ICP Fit Score} \\times 0.35) \+ (\\text{Pain Point Match} \\times 0.35) \+ (\\text{Reachability Quality} \\times 0.15) \+ (\\text{Buying Signal Intensity} \\times 0.15)$$

---

## 2\. AI Sales Organization Structure

The AI Sales OS is structured as a hierarchical organization with specialized agents possessing defined decision authorities, boundaries, and failure-handling rules.

                                 ┌────────────────────────┐

                                 │     CEO AGENT (AI)     │

                                 └───────────┬────────────┘

                                             │

                                 ┌───────────▼────────────┐

                                 │ SALES MANAGER AGENT    │

                                 └───────────┬────────────┘

                                             │

          ┌──────────────────────────────────┼──────────────────────────────────┐

          │                                  │                                  │

┌─────────▼──────────┐            ┌──────────▼──────────┐            ┌──────────▼──────────┐

│ CAMPAIGN PLANNER   │            │ QUALITY CONTROLLER  │            │ STRATEGY & LEARNING │

└─────────┬──────────┘            └──────────┬──────────┘            └──────────┬──────────┘

          │                                  │                                  │

  ┌───────┴───────┐                  ┌───────┴───────┐                  ┌───────┴───────┐

  │ Lead Discovery│                  │ Outbound      │                  │ Inbound       │

  │ & Enrichment  │                  │ Outreach Agent│                  │ Conversation  │

  └───────────────┘                  └───────────────┘                  └───────────────┘

### 2.1 Agent Catalog & Responsibilities

#### A. CEO Agent (Executive Strategy & System Overseer)

* **Purpose:** Sets high-level organizational sales targets, evaluates macro campaign performance, and allocates system resources across products.  
* **Responsibilities:** Analyzes product briefs, sets target ROI thresholds, approves new campaign structures, and reviews nightly performance metrics.  
* **Decision Authority:** High. Can pause underperforming campaigns and adjust global ICP parameters.  
* **Escalation Trigger:** Escalates to Human Admin if system conversion drops below 1% for 3 consecutive days or if global API failure occurs.

#### B. Sales Manager Agent (Operations & Delegation Controller)

* **Purpose:** Translates CEO goals into daily tactical tasks and manages workload distribution across specialized operational agents.  
* **Responsibilities:** Assigns lead batches to Enrichment and Scoring agents, approves personalized outreach batches, monitors queue velocity.  
* **Decision Authority:** Operational. Can adjust daily dispatch volumes and re-assign retry queues.

#### C. ICP & Strategy Agent (Audience Intelligence) — ✅ implemented (`agents/icp_strategy_agent.py`, v2.2 amendment)

* **Purpose:** Analyzes target industries, firmographics, and pain points to define exact Ideal Customer Profiles (ICPs).  
* **Inputs:** Product Brief JSON (Value props, target verticals, pricing tier). The human sets only the geographic boundary once per product (`products.target_regions`) — this agent has no location-judgment input of its own and does not invent one.
* **Outputs:** Detailed ICP Definitions (Target company size, role titles, key review complaints to search for), plus the exact search queries used to find those businesses.
* **Trigger:** autonomous — `jobs/discovery_scheduler.py` calls this per active product on a refresh cadence (default 7 days) rather than a human or the CEO Agent invoking it manually.

#### D. Lead Discovery & Enrichment Agent

* **Purpose:** Identifies target business prospects and enriches them with verified decision-maker details and tech stack signatures.  
* **Inputs:** Search queries generated by ICP Agent.  
* **Outputs:** Verified Lead Records in SQLite DB with company size, verified emails, and WhatsApp status.

#### E. Review & Weakness Detection Agent

* **Purpose:** Analyzes public reviews (1–3 stars) to uncover specific operational complaints.  
* **Inputs:** Google Reviews, G2, Trustpilot text snippets.  
* **Outputs:** Mapped Operational Weakness (e.g., `LEAD_LEAKAGE`, `STAFF_UNTRACKED`, `ADMIN_RECEIPT_ERRORS`).

#### F. Lead Scoring & Fit Agent

* **Purpose:** Calculates deterministic fit scores (0–100) and tiers leads (`HOT`, `WARM`, `COLD`).  
* **Inputs:** Firmographic data \+ Extracted Review Pain Points \+ Product Brief.  
* **Outputs:** Score breakdown JSON, tier assignment, and justification.

#### G. Hyper-Personalized Outreach Agent

* **Purpose:** Crafts unique, context-aware outreach copy tailored to the decision-maker and extracted pain point.  
* **Inputs:** Lead profile, extracted weakness, channel specs (Email / Contact Form / WhatsApp).  
* **Outputs:** Multi-channel personalized message copy with `List-Unsubscribe` compliance headers.

#### H. Inbound Conversation & Objection Handling Agent

* **Purpose:** Manages incoming prospect replies, resolves objections, and drives conversion toward meeting bookings.  
* **Inputs:** Inbound WhatsApp/Email webhook text, conversation history.  
* **Outputs:** Categorized intent (`INTERESTED`, `DEMO_REQUESTED`, `OBJECTION`, `STOP`), contextual reply copy, or human escalation trigger.

#### I. Quality Controller & Supervisor Agent

* **Purpose:** Performs peer review on generated outreach copy and AI replies before dispatch to prevent hallucination, tone errors, or policy violations.  
* **Decision Authority:** Veto power over any outbound message.

#### J. Learning & Memory Manager Agent

* **Purpose:** Tracks campaign conversion patterns, evaluates A/B copy performance, updates the central Knowledge Base, and optimizes prompt templates.

---

## 3\. Agent Collaboration & Orchestration Model

Agents communicate via structured JSON event buses managed by the Flask Central Engine.

*(v2.2 note: the CEO/Manager Agent is not yet built. As implemented since Phase 3 Step 3.5, the first two steps below — analyzing the product brief and generating search queries — are triggered directly by `jobs/discovery_scheduler.py` on a refresh cadence, not by a CEO Agent decision. The diagram's intent still holds once the CEO Agent lands in a later phase; it will sit above the scheduler's trigger, not replace it.)*

sequenceDiagram

    autonumber

    participant CEO as CEO / Manager Agent

    participant ICP as ICP & Strategy Agent

    participant Scraper as Discovery Agent

    participant Review as Review Analyst Agent

    participant Scoring as Scoring Agent

    participant QC as Quality Controller

    participant Outreach as Outreach Agent

    CEO-\>\>ICP: Analyze Product Brief (Coaching ERP / Tracker)

    ICP--\>\>CEO: Generated Search Queries & Target ICP Parameters

    CEO-\>\>Scraper: Execute Discovery Jobs

    Scraper--\>\>Review: Raw Lead Data (Google Maps / Web)

    Review--\>\>Scoring: Extracted Review Pain Points

    Scoring--\>\>CEO: Scored Leads (HOT / WARM / COLD)

    CEO-\>\>Outreach: Dispatch HOT Leads

    Outreach-\>\>QC: Submit Drafted Outreach Copy

    alt QC Approval \== True

        QC--\>\>Outreach: Approved for Delivery

        Outreach-\>\>Outreach: Send Email / WhatsApp

    else QC Approval \== False

        QC--\>\>Outreach: Reject with Feedback (Regenerate Copy)

    end

---

## 4\. Decision Engine & Confidence Thresholds

Every autonomous decision made by an agent must pass through a **Confidence & Risk Evaluation Matrix** before execution:

| Action Category | Confidence Threshold | Approval Required | Risk Level |
| :---- | :---- | :---- | :---- |
| **Data Ingestion & Scoring** | $\\ge 0.70$ | Fully Autonomous | Low |
| **Standard Initial Outreach** | $\\ge 0.85$ | QC Agent Review | Medium |
| **Inbound FAQ & Objection Reply** | $\\ge 0.85$ | Fully Autonomous | Medium |
| **Meeting Scheduling / Booking Link** | $\\ge 0.90$ | Fully Autonomous \+ Human Alert | Low |
| **Custom Pricing / Discount Query** | $\\ge 0.95$ | **Human Approval Mandatory** | High |
| **Unsubscribe / Opt-Out Request** | N/A (100% Rule) | Immediate Auto-Execution | Critical |

flowchart TD

    A\[Agent Proposes Action\] \--\> B{Calculate Confidence Score}

    B \--\>|Confidence \< 0.70| C\[Route to Human Escalation Queue\]

    B \--\>|0.70 \<= Confidence \< 0.85| D\[Quality Controller Agent Review\]

    B \--\>|Confidence \>= 0.85| E{High Risk Action?}

    E \--\>|Yes: Custom Pricing / Contract| C

    E \--\>|No: Standard Outreach / Booking| F\[Execute Action via Flask API\]

    D \--\>|Approved| F

    D \--\>|Rejected| G\[Regenerate with Feedback\]

---

## 5\. Planning & Adaptability Engine

The AI Sales OS continuously monitors campaign metrics and automatically shifts strategies when performance bottlenecks occur.

### 5.1 Self-Adaptation Trigger Matrix

| Observed Metric Failure | Root Cause Analysis | Autonomous Adaptation Trigger |
| :---- | :---- | :---- |
| **Email Open Rate \< 15%** | Poor Subject Line / Email Inbox Placement | Auto-generate 3 new subject line variations; rotate sending subdomain. |
| **Reply Rate \< 2% on 200 Sends** | Weak Value Proposition / Off-target ICP | Strategy Agent narrows company headcount filter; shifts value hook from *Price* to *Time Savings*. |
| **High Spam Complaint Rate (\>0.1%)** | Message reads as pitch spam / Missing Unsubscribe | Pause campaign; re-template outreach to ultra-short plain text (\<75 words); enforce `List-Unsubscribe` headers. |
| **High Bounce Rate (\>3%)** | Invalid scraped emails | Update email enrichment waterfall; enforce stricter SMTP handshake validation. |
| **Frequent "Existing Vendor" Objections** | Prospect already uses competitor tool | Inbound Agent shifts script to "Migration & Cost Reduction" comparative talking points. |

---

## 6\. Learning Engine & Continuous Optimization

The system learns through closed-loop feedback across three distinct time horizons:

\+-----------------------------------------------------------------------------------+

|                              LEARNING LOOP HORIZONS                               |

|                                                                                   |

|  1\. REAL-TIME LOOP (Per Conversation)                                             |

|     \- Analyzes reply sentiment \-\> Adjusts objection handling script on the fly.   |

|                                                                                   |

|  2\. CAMPAIGN LOOP (Weekly)                                                        |

|     \- Evaluates A/B subject lines & value hooks \-\> Promotes winning templates.    |

|                                                                                   |

|  3\. KNOWLEDGE LOOP (Monthly)                                                      |

|     \- Extracts industry-wide objection patterns \-\> Updates Master KB.             |

\+-----------------------------------------------------------------------------------+

### 6.1 Automated A/B Copy Optimization

1. Outreach Agent generates **Variant A** (Direct Pain Point Hook) and **Variant B** (Case Study / Proof Hook).  
2. Distributes batch 50/50 across scored leads.  
3. After 100 sends, Learning Agent evaluates conversion rates using a **Multi-Armed Bandit Algorithm**.  
4. Winning variant receives 80% traffic allocation; underperforming variant is retired and re-promoted into a new prompt experiment.

---

## 7\. Multi-Tiered Memory Architecture

To maintain deep context across long sales cycles without bloating token context windows, the system utilizes a 4-tier memory model:

\+-----------------------------------------------------------------------------------+

|                         MULTI-TIERED MEMORY ARCHITECTURE                          |

\+-----------------------------------------------------------------------------------+

| 1\. WORKING MEMORY     | Current prompt execution context & active agent state      |

\+-----------------------+-----------------------------------------------------------+

| 2\. CAMPAIGN MEMORY    | Active ICP rules, subject line variants, sending limits   |

\+-----------------------+-----------------------------------------------------------+

| 3\. LEAD MEMORY        | Contact details, extracted review quotes, lead score      |

\+-----------------------+-----------------------------------------------------------+

| 4\. HISTORICAL MEMORY  | Long-term vector store of successful objection responses  |

\+-----------------------------------------------------------------------------------+

* **Working Memory (In-Memory / Session):** Ephemeral context during active LLM execution.  
* **Campaign Memory (SQLite `outreach_campaigns`):** Operational rules, active A/B templates, and current sending velocity.  
* **Lead Memory (SQLite `leads` \+ `inbound_conversations`):** Granular interaction history, email thread context, extracted review quotes, and lead state.  
* **Historical Knowledge Memory (Vector Embeddings / SQLite JSON):** Unstructured long-term knowledge repository of winning objection-handling scripts, product FAQs, and competitor comparison matrices.

---

## 8\. Human-AI Collaboration & Escalation Protocol

The AI Sales OS is designed to operate autonomously while granting human reps absolute control over high-value and sensitive interactions.

stateDiagram-v2

    \[\*\] \--\> AutonomousDiscovery: Lead Scraped

    AutonomousDiscovery \--\> AutonomousScoring: Enriched & Reviewed

    AutonomousScoring \--\> QCReview: HOT Lead (Score \>= 80\)

    QCReview \--\> AutonomousOutreach: QC Approved

    AutonomousOutreach \--\> InboundHandling: Prospect Replies

    

    InboundHandling \--\> HumanEscalation: Demo Requested / Pricing Query / Low Confidence

    InboundHandling \--\> Suppressed: STOP / Opt-Out

    

    state HumanEscalation {

        \[\*\] \--\> AlertPushed: Slack / WhatsApp Alert Sent

        AlertPushed \--\> HumanTakeover: Rep Claims Lead

        HumanTakeover \--\> ClosedWon: Deal Closed

    }

### 8.1 Mandatory Human Escalation Triggers

1. **Meeting / Demo Explicit Request:** The moment a prospect asks for a call or demo, the AI marks the lead as `HOT_LEAD`, triggers an instant Slack/WhatsApp alert to the human rep, and halts automated follow-ups.  
2. **Custom Pricing / Negotiation:** Any inquiry regarding discounts, custom contract terms, or SLA guarantees routes directly to a human.  
3. **Hostile / Legal Threat:** Any reply containing legal jargon or extreme hostility suppresses the contact immediately and alerts the supervisor.  
4. **Low LLM Confidence (\< 0.70):** If the Inbound Agent is uncertain about a complex question, it drafts a suggested reply for human review instead of auto-sending.

---

## 9\. Agent System Prompts & Guardrail Strategy

Below are the core system prompt standards that govern agent cognition across the platform.

### 9.1 Quality Controller (Supervisor) System Prompt Blueprint

SYSTEM PROMPT: Quality Controller Agent

ROLE: You are the Chief Compliance and Quality Officer for an Enterprise B2B Sales System.

DUTIES:

1\. Review drafted outreach copy from Outreach Agent before delivery.

2\. Ensure copy contains NO generic AI buzzwords ("delve", "game-changer", "I hope this email finds you well").

3\. Verify that the outreach explicitly references the verified review pain point provided in the context.

4\. Ensure the email footer includes a valid physical address and a clear 1-click unsubscribe option.

5\. Verify that NO false commitments, unauthorized pricing discounts, or unverified feature claims exist.

OUTPUT FORMAT (JSON ONLY):

{

  "approved": boolean,

  "confidence\_score": float (0.0 to 1.0),

  "rejection\_reasons": \["string"\],

  "suggested\_corrections": "string"

}

### 9.2 Inbound Intent Classifier System Prompt Blueprint

SYSTEM PROMPT: Inbound Reply Intent Classifier

ROLE: You are a Senior SDR analyzing incoming email and WhatsApp replies from B2B prospects.

CATEGORIZE INTO EXACTLY ONE OF:

\- "INTERESTED": Prospect wants to learn more, see pricing, or get details.

\- "DEMO\_REQUESTED": Prospect explicitly asks for a call, meeting, or demo.

\- "OBJECTION": Prospect raises a concern (e.g., pricing, existing vendor, bad timing).

\- "STOP": Prospect requests unsubscribe, opt-out, or says "not interested".

\- "AUTO\_REPLY": Out-of-office or automated system bounce message.

STRICT RULE:

If intent is "STOP", set "suppress\_immediately": true.

If intent is "DEMO\_REQUESTED" or "INTERESTED", set "escalate\_to\_human": true.

OUTPUT FORMAT (JSON ONLY):

{

  "intent": string,

  "confidence": float,

  "suppress\_immediately": boolean,

  "escalate\_to\_human": boolean,

  "suggested\_reply": string

}

---

## 10\. Self-Evaluation & Peer Critique Engine

To eliminate hallucinations and maintain brand voice, agents perform cross-validation before executing critical state changes.

                          \[ Agent A Drafts Action \]

                                     │

                                     ▼

                      \[ Agent B (QC) Evaluation \]

                                     │

                  ┌──────────────────┴──────────────────┐

                  ▼                                     ▼

        \[ Score \>= Threshold \]                \[ Score \< Threshold \]

                  │                                     │

                  ▼                                     ▼

          \[ Execute Action \]                  \[ Reject & Send Feedback \]

                                                        │

                                                        ▼

                                              \[ Agent A Refines Draft \]

1. **Output Validation:** Every generated text output is parsed against strict JSON schema definitions.  
2. **Tone & Style Guard:** Outputs with \>0% match to blacklisted AI buzzword dictionaries are automatically rejected for revision.  
3. **Cross-Verification:** The Lead Scoring Agent's ratings are audited by the Sales Manager Agent once per batch to ensure consistent score distribution.

---

## 11\. KPI Framework for Autonomous Sales

The performance of the AI Sales OS is evaluated across 4 core metric categories:

\+-----------------------------------------------------------------------------------+

|                              SYSTEM KPI FRAMEWORK                                 |

\+-----------------------------------------------------------------------------------+

| 1\. BUSINESS KPIs     | \- Sales Qualified Leads (SQLs) generated per week          |

|                      | \- Meeting Booking Conversion Rate (% of outreached leads)  |

|                      | \- Cost per Qualified Pipeline Opportunity                  |

\+----------------------+------------------------------------------------------------+

| 2\. INTELLIGENCE KPIs | \- Intent Classification Accuracy Rate (\>95% target)       |

|                      | \- Auto-Response Confidence Score Average (\>0.88 target)    |

|                      | \- Zero-Hallucination Rate (100% mandatory target)          |

\+----------------------+------------------------------------------------------------+

| 3\. ADAPTABILITY KPIs | \- Time to adapt underperforming email subject lines (\<24h) |

|                      | \- Winning A/B Variant Promotion Rate                      |

\+----------------------+------------------------------------------------------------+

| 4\. OPERATIONAL KPIs  | \- Email Bounce Rate (\<2% mandatory limit)                 |

|                      | \- Unsubscribe / Spam Complaint Rate (\<0.1% limit)         |

|                      | \- Mean Human Escalation Response Time                     |

\+-----------------------------------------------------------------------------------+

---

## 12\. Future Expansion Modules

The intelligence architecture is designed to support seamless expansion into downstream sales lifecycle stages:

> **Status update (2026-08-19):** module 1 below is no longer speculative — the **Voice SDR Agent** is now specified in **Chapter 16** (§16.4, §16.6) and scheduled as `MASTER_DEVELOPMENT_PRD.md` §5A Phase 10 Step 10.4, with a scope deliberately wider than the "inbound qualification" originally sketched here, and correspondingly stricter guardrails: its own kill-switch, a per-lead consent/legal basis, a region gate, and assisted-before-autonomous rollout. Modules 2–4 remain future work.

1. **Voice SDR Agent:** Integration with real-time webRTC voice agents (e.g., Retell AI / ElevenLabs) for inbound phone call qualification.  
2. **Autonomous Demo & Proposal Agent:** Automated creation of personalized slide decks and proposal PDFs based on lead discovery insights.  
3. **Contract & Negotiation Agent:** Intelligent redlining assistant for standard NDAs and software subscription contracts within human-defined boundaries.  
4. **Customer Success & Renewal Agent:** Post-sale onboarding follow-ups, usage analytics monitoring, and expansion/renewal alerts.

---

## Chapter 15: Enterprise Executive Business & Operating System Layer (AI-BOS)

*(Chapter numbers 13–14 are reserved for future intelligence-layer expansions listed in §12; this addendum resumes at 15 to match its companion specification in `MASTER_DEVELOPMENT_PRD.md`.)*

### 15.0 Executive Overview

This chapter upgrades the platform from an **AI Sales Operating System (AI-SOS)** — a discovery/outreach automation brain — into a full **Enterprise AI Business Operating System (AI-BOS)**. It introduces a third layer that sits **above** the Cognitive Brain Layer (Chapters 1–12) and governs it: setting revenue and CAC ceilings, routing prospects into the correct sales motion, protecting delivery capacity, tracking clients after they convert, simulating strategic decisions before they're executed, and enforcing hard boundaries on what the system is allowed to change about itself.

The Executive Layer never talks to a lead and never touches a channel. It only sets the ceilings, thresholds, and routing rules the Cognitive Brain Layer must operate within — the two-layer contract from the Executive Summary becomes a three-layer contract:

```
+-----------------------------------------------------------------------------------+
|                    ENTERPRISE EXECUTIVE LAYER (Chapter 15 / AI-BOS)               |
|  - Executive Business Brain         - Dual Sales Mode Engine                      |
|  - Capacity & Resource Intelligence - Market & Competitor Intelligence            |
|  - Client Lifecycle Intelligence    - Executive Decision Simulation               |
|  - Cross-Agent Governance           - AI Self-Evolution Boundaries                |
+-----------------------------------------------------------------------------------+
                                         │
                    Budget Ceilings, Capacity Throttles, Sales-Mode Routing,
                              Governance Vetoes & Overrides
                                         ▼
+-----------------------------------------------------------------------------------+
|                        ENTERPRISE COGNITIVE BRAIN LAYER                           |
|  - CEO & Supervisor Agents         - Decision & Planning Engines                  |
|  - Adaptive Learning Loops         - Multi-Tiered Memory (Working, Campaign, Vector) |
+-----------------------------------------------------------------------------------+
                                         │
                         Structured Agent Intent & Instructions
                                         ▼
+-----------------------------------------------------------------------------------+
|                     TECHNICAL EXECUTION LAYER (PRD v3)                            |
|  - Flask REST API                  - SQLite WAL Engine + ThreadPool               |
|  - Playwright Scrapers             - In-process Discovery Scheduler               |
+-----------------------------------------------------------------------------------+
```

### 15.1 Module Catalog & Responsibilities

Following the Agent Catalog format established in §2.1, each Executive module is specified by Purpose, Logic/Decision Authority, and Escalation Trigger.

#### 15.1.1 Executive Business Brain (Revenue, Margin & CAC Ceiling Control)

* **Purpose:** Monitors revenue targets, profit margins, Customer Acquisition Cost (CAC) ceilings, and daily API/outreach budget allocation across all active products.
* **Logic:** Automatically allocates outreach budget across products in proportion to conversion ROI. If a product's realized CAC exceeds its configured ceiling, that product's campaigns are paused — not the whole system.
* **Decision Authority:** Autonomous within budget bands set by the CEO Agent (§2.1.A); pausing a campaign for CAC breach is autonomous, but *raising* a CAC ceiling or reallocating budget across products by more than the CEO's standing mandate is not (§15.1.8).
* **Escalation Trigger:** CAC exceeds ceiling for 3 consecutive days on a product, or aggregate daily spend approaches the hard API budget cap → Human Admin alert (mirrors the CEO Agent's existing 1%-conversion-drop trigger, §2.1.A).

#### 15.1.2 Dual Sales Mode Engine (Product SaaS vs. Custom Development Sales)

* **Purpose:** Dynamically routes each prospect into one of two distinct sales flows based on firmographics and requirement complexity, so the Outreach Agent (§2.1.G) pitches the right thing to the right buyer.
* **Routing Rules:**

| Flow | Trigger | Pitch |
| :-- | :-- | :-- |
| **Product SaaS** | Headcount < 20; standard pain points (fee tracking, attendance, basic CRM) | Off-the-shelf software subscription |
| **Custom Dev Services** | Headcount > 50; complex tech stack; custom workflow requirements | Bespoke software development, API integration, custom quotation |
| **Ambiguous band (21–49)** | Mixed or unclear signals | Low-confidence LLM tiebreak, routed through the Decision Engine (§4) like any other sub-0.85-confidence action — never silently defaulted |

* **Decision Authority:** Autonomous at the two extremes (≥0.90 confidence); the 21–49 headcount band always carries a confidence score into the standard Decision Engine, so an uncertain call gets QC/human eyes exactly like an uncertain outreach draft does.
* **Escalation Trigger:** Custom Dev Services flow never auto-generates or auto-sends a quotation — pricing is always a Custom Pricing action (§4, ≥0.95 / Human Approval Mandatory).

#### 15.1.3 Capacity & Resource Intelligence (Delivery Bandwidth Protection)

* **Purpose:** Monitors internal delivery/onboarding team bandwidth so the top of the funnel never outproduces what the business can actually deliver.
* **Logic:** If onboarding/dev-team capacity utilization reaches the configured ceiling (default 90%), the system automatically throttles new cold-lead discovery. Existing leads already in the pipeline continue normally — only new `DISCOVER` jobs pause.
* **Decision Authority:** Fully autonomous, symmetric in both directions — throttles on breach, re-opens automatically once utilization drops back below the ceiling. No human step needed for either direction; this is a mechanical safety valve, not a strategic call.
* **Escalation Trigger:** Sustained throttling (capacity pinned at ceiling for an extended period) is a Sales Manager Agent (§2.1.B) signal to raise with the CEO Agent — the fix is a staffing/delivery decision, not something the AI can solve by discovering more leads.

#### 15.1.4 Market & Competitor Intelligence

* **Purpose:** Tracks competitor pricing shifts and identifies under-saturated geographic regions for expansion (e.g., tier-2/tier-3 cities), extending the ICP & Strategy Agent's (§2.1.C) existing audience-intelligence role outward to the market itself.
* **Logic:** Periodic scan job re-runs ICP/search-query generation against fresh public data, writes findings to Historical Memory (§7) as competitor matrices.
* **Decision Authority:** Advisory only. Findings feed the CEO Agent's executive summary and the Learning Agent's next-experiment hypothesis (§6.1) — this module never changes pricing or the core ICP definition on its own (§15.1.8).
* **Escalation Trigger:** A material competitor pricing shift (e.g., undercutting current positioning by a large margin) surfaces in the nightly executive summary for the CEO/human to act on; it does not trigger an autonomous re-pricing.

#### 15.1.5 Client Lifecycle Intelligence (Post-Sale LTV Engine)

* **Purpose:** Extends the system's intelligence beyond lead conversion into the post-sale relationship — the first extension of AI-SOS scope past "close the deal."
* **Logic:** Tracks onboarding milestones, triggers automated renewal reminders 30 days prior to contract expiry, and surfaces cross-sell/upsell suggestions on usage spikes.
* **Decision Authority:** Autonomous for reminder scheduling and drafting upsell outreach; any upsell message still passes the same Decision Engine + QC gate (§4, §2.1.I) as first-touch outreach — post-sale is not a lower-scrutiny channel.
* **Escalation Trigger:** Any pricing, discount, or contract-term component of an upsell/renewal conversation routes to Human Approval Mandatory, identical to first-touch custom pricing (§4). A detected churn-risk signal (e.g., usage collapse near renewal) escalates to the human account owner.

#### 15.1.6 Executive Decision Simulation ("What-If" Analysis)

* **Purpose:** Simulates financial outcomes (ROI, deal velocity) before the business executes a major strategic budget reallocation — a Monte Carlo pass over historical performance, not a live action.
* **Logic:** Takes a proposed change (e.g., "shift 30% of budget from Product A to Product B") and returns a projected outcome distribution (p10/p50/p90) drawn from realized campaign/variant/score history.
* **Decision Authority:** None — this module is read-only by design. It never writes to campaign state or budget allocation itself.
* **Escalation Trigger:** N/A — every simulation result is advisory input to a CEO Agent or human decision (§2.1.A), never authority to act on its own.

#### 15.1.7 Cross-Agent Governance & Conflict Resolution

* **Purpose:** Resolves deadlocks when two or more specialized agents propose conflicting actions on the same lead or campaign in the same cycle — formalizing the implicit precedence already present in the org chart (§2).
* **Hierarchy:**

```
CEO Agent  >  Quality Controller (Veto)  >  Resource Capacity Agent  >  Strategy Agent  >  Operational Agents
```

* **Decision Authority:** The Quality Controller's veto (§2.1.I) is absolute and sits above rank — a QC rejection wins even against a higher-ranked agent's proposal. Below QC, ties resolve strictly by rank.
* **Escalation Trigger:** Every governance override is logged for audit (mirrors the audit intent of §4's Decision Engine logging) so a human can review why one agent's action won over another's.

#### 15.1.8 AI Self-Governance & Evolution Boundaries

* **Purpose:** Draws a hard, non-negotiable line between what the AI may adapt on its own and what always requires a human — the enforcement backbone that makes every "autonomous" claim elsewhere in this document credible.
* **Guardrails:**

| AI **CAN** autonomously adapt | AI **CANNOT** adapt — mandatory human sign-off |
| :-- | :-- |
| Subject lines | Base product pricing |
| Email copy variants | Discount offers |
| Scraper query parameters | ICP core definitions |
| Sending delay/pacing | Contractual SLAs |
| A/B prompt experiment weights | Compliance/privacy policies |

* **Decision Authority:** This boundary is enforced in code, not left to prompt discipline — any attempted autonomous write to a locked parameter is rejected and routed to Human Escalation (§8), the same channel used for custom pricing and hostile-message handling.
* **Escalation Trigger:** N/A by design — a locked-parameter write attempt *is* the escalation; there is no autonomous path around it.

### 15.2 Relationship to the Existing Decision Engine (§4)

Modules 15.1.2 (ambiguous-band routing), 15.1.5 (upsell/renewal outreach), and 15.1.8 (locked-parameter attempts) don't introduce a parallel approval system — they emit a confidence score and a category and pass through the **same** Confidence & Risk Evaluation Matrix defined in §4. The only new terminal state is `GOVERNANCE_OVERRIDE` (§15.1.7), logged alongside the existing `EXECUTE` / `QC_REVIEW` / `HUMAN_ESCALATION` / `IMMEDIATE_EXECUTE` outcomes.

### 15.3 Relationship to Multi-Tiered Memory (§7)

A fifth tier extends the model in §7: **Post-Sale Memory** — onboarding status, MRR, and renewal/upsell state per converted client, owned by Client Lifecycle Intelligence (§15.1.5). It follows the same pattern as Lead Memory: structured, per-entity, queried rather than embedded.

---

## Chapter 16: Multi-Channel Engagement & Adaptive Messaging Layer

*(Added 2026-08-19. Companion build specification: `MASTER_DEVELOPMENT_PRD.md` §5A, Phases 6–10. Where
Chapter 15 added a layer **above** the Cognitive Brain that governs it, this chapter widens the brain
itself: more channels to speak through, a human-defined structure to speak within, and a feedback loop
that finally makes §6's Learning Engine operate on real data instead of a design promise.)*

### 16.0 Why this chapter exists

Chapters 1–12 were written before the system had ever contacted a real business. Chapter 16 is written
after — from eleven requirements raised by the operator watching it run, plus every capability this
architecture specified but deliberately deferred for lack of real data.

One theme runs through all of it: **the system could already act, but it could not yet see itself act,
be steered without a code change, or learn from what it had done.** This chapter closes those three
gaps, in that order.

### 16.1 Observability as a cognitive prerequisite

§10 (Self-Evaluation & Peer Critique) and §6 (Learning Engine) both assume the system can observe its
own behaviour. In practice it could not: process liveness and in-flight work were visible only through
server logs. Two real incidents were found that way rather than through any interface — a worker
process silently not running for a whole session, and leads stranded mid-outreach after a provider
outage.

**Principle established:** an autonomous system's operator must be able to answer *"is it alive, and
what is it doing right now?"* without shell access. Observability is not a reporting feature bolted on
at the end — it is what makes every downstream claim in this document auditable.

### 16.2 Human-set boundaries, AI-filled interiors

The architecture already had one instance of this pattern: `target_regions` (§2.1.C amendment) — a human
sets the geographic boundary, the AI decides business types freely inside it, precisely because the ICP
agent has no grounded basis for inventing geography.

Chapter 16 generalises the pattern into the system's **defining collaboration shape**, applying it in
three new places:

| Human sets (the boundary) | AI decides (inside it) |
| :-- | :-- |
| Target business categories, target person roles (Phase 7) | Which specific businesses and which named individuals actually match |
| Message **format** — slot structure: hook → this business's own weak points → solution → demo slot (Phase 8) | The actual content of every slot, per lead, per product |
| Content library — the real demo URLs, case studies, testimonials (Phase 8) | Which asset fits this lead, or that none fits and the slot should be dropped |

This is also a **hallucination boundary**, not merely an ergonomic one. An AI that must select a demo
URL from a human-curated library cannot invent one. An AI constrained to human-approved verticals cannot
drift into the self-referential-query failure that once required rejecting 157 real leads. The boundary
does more safety work than the prompt does.

### 16.3 The measurement → adaptation dependency

§6 (Learning Engine) and §6.1 (Automated A/B Copy Optimization) specify a multi-armed bandit over
message variants. It has never run, for an honest reason: no variants were ever recorded. The
`campaign_variants` structure was designed and left empty.

The same gap deferred the operator-flagged **autonomous WhatsApp template loop** — an agent that decides
a template is underperforming, drafts a replacement, submits it for approval, and adopts it once
approved. Building that before performance data existed would have produced an agent that *appears* to
learn while actually guessing.

**Ordering rule, now explicit in the architecture:** *variants are produced (Phase 8) → variants are
measured against real outcomes (Phase 9) → and only then may an agent adapt them (Phase 9, late).*
Any future "learning" capability must state which real signal it learns from, or it does not ship.

This is what makes Phase 9's adaptive-template agent legitimate where the same agent would have been
illegitimate a year earlier in the build: it reads real sent/seen/replied counts, produced by real
delivery-receipt tracking that already exists on both channels.

### 16.4 New agent responsibilities

These extend §2.1's catalog. None of them gains authority above the Quality Controller — QC's veto
remains absolute (§2, §8), and every one of these still routes through the Decision Engine (§4).

| Agent / responsibility | Role | Authority ceiling |
| :-- | :-- | :-- |
| **Format Adaptation** (extends Outreach Agent) | Fills a human-authored format per lead; selects a content asset or drops the slot | May never invent an asset, nor bypass QC |
| **Cadence Agent** | Decides whether/when a follow-up touch is warranted; exits on reply or opt-out | Bound by suppression, pacing caps, and the autonomous-outreach kill-switch — at *every* touch, not just the first |
| **Engagement Escalation** | Reads real open/seen signal; escalates repeated-open-no-reply to another channel or a human | Fires only on real signal; never infers engagement where a channel provides none |
| **Template Lifecycle Agent** | Detects underperforming/missing templates, drafts replacements, submits for platform approval, adopts on approval | QC review **and** a human approval gate before any AI-authored template reaches a real business |
| **Channel Router** | Chooses the channel for a lead's region and available contact points | Refuses to send into a region with no explicit policy; never guesses a fallback other than email |
| **Voice SDR Agent** (§12's first future module, now specified) | Conducts or assists a real phone conversation | Its own kill-switch, stricter than the global one; a per-lead consent/legal basis is mandatory before any dial; hands off to a human on anything it cannot handle |

### 16.5 Channel reality: what the platforms actually permit

The operator asked for AI outreach on LinkedIn, Instagram and Facebook. The honest architectural answer
distinguishes three regimes, and this distinction is a **design constraint, not a preference**:

1. **Cold-contact-capable channels** — email, WhatsApp (via pre-approved templates), SMS (region-gated).
   These support a genuine first touch to a stranger, within their own compliance rules.
2. **Reply-window-only channels** — Instagram DM and Facebook Messenger. Meta's official APIs permit
   messaging only someone who contacted *us* first, inside a limited window. There is no cold-template
   equivalent to WhatsApp's. Automated *responses* here are legitimate and worth building; automated
   *cold outreach* is not available at all.
3. **No-automation channels** — LinkedIn. No official API exists for general cold messaging. The only
   technical route is driving a logged-in account with a browser, which violates the platform's terms
   and risks permanent account loss — and directly contradicts this project's own evasion-free rule.

**Resulting design:** for regimes 2 and 3 the AI does everything *except* send — research, targeting,
personalisation, drafting — and places the finished message in a **human-send queue**. The operator gets
the full intelligence benefit at zero policy risk. The system deliberately contains **no code path
capable of auto-sending on those platforms**, and Phase 10's DoD verifies that by absence.

This is a case where the correct architecture is defined by what it refuses to build.

### 16.6 Escalating risk, escalating guardrails

The channels added in Phase 10 are not equivalent in consequence, and the guardrails scale accordingly:

- **Email/WhatsApp** (live today): suppression list, one-click unsubscribe, pacing caps, QC veto,
  global autonomous-outreach kill-switch.
- **SMS**: all of the above, plus a per-country compliance gate that refuses unconfigured regions
  outright, plus its own kill-switch.
- **AI voice calling**: all of the above, plus a *dedicated kill-switch independent of and stricter than
  the global one*, a recorded per-lead consent/legal basis before any dial, a region gate, and an
  assisted-before-autonomous rollout — a human dials and the AI assists, until real calls prove the
  compliance posture.

The reasoning is uniform across all three: **the cost of one wrong action rises sharply with each
channel.** A mistargeted email is a nuisance; an unlawful automated call is a per-call statutory
penalty in some jurisdictions and a legal exposure in others. Guardrail strength is scaled to the cost
of being wrong once — never to the average case.

---

## Chapter 17: Message Composition, Declared Intent & Person-Level Relevance

*(Added 2026-08-22. Companion build specification: `MASTER_DEVELOPMENT_PRD.md` §5B, Phases 11–15.
Chapter 16 widened the brain — more channels, a human-defined structure, a real feedback loop.
Chapter 17 sharpens it: the same brain now has to compose persuasively, read a declared answer, sustain
a multi-touch conversation with three distinct intents, stay consistent across channels, and target the
person who can actually evaluate what it is saying.)*

### 17.0 Why this chapter exists

Chapter 16 was written from eleven requirements raised by an operator who could not see the system work.
Chapter 17 is written from six raised by the same operator after watching it work *well* — Phases 6–9
live on real leads, real sends, real replies, real Meta-approved templates.

The complaint changed shape entirely, and that shift is the whole content of this chapter. It is no
longer *"I can't see it, steer it, or measure it."* It is:

> The message is competent but not compelling. A lead who is interested has to compose a reply to say
> so. The second and third touches say the same thing as the first. What goes out on Instagram is not
> what went out by email. And the person receiving it often has no basis to judge the offer at all.

Five failures, all of which happen **after** the system is working correctly by its own existing
measures — which is exactly why none of them were visible in Chapter 16.

### 17.1 Composition is a cognitive act, not a rendering step

Today the Outreach Agent emits `{subject, body}` where `body` is one undifferentiated block of prose.
That shape encodes an assumption worth naming: that writing a sales message is a single act of
generation, and everything after it is presentation.

That assumption fails in four concrete ways this architecture already has evidence for:
- A missing content asset cannot cleanly remove *its own part* of the message, because there are no
  parts — only a paragraph that either mentions a link or awkwardly does not. §16.2's "drop the slot
  rather than fabricate" rule is honest at the data layer and invisible at the message layer.
- Nothing can attach to a position in the message — no button, no per-section check, no per-section
  reuse — because positions do not exist as addressable things.
- QC can only judge the message as a whole. It cannot verify that the required sections are present, in
  order, and non-empty, because "sections" is not a claim the draft makes.
- A second channel cannot re-render the same content differently, because the prose *is* the rendering.

**Principle established:** an outreach message is an **ordered set of typed sections**, each with its own
communicative job, produced by the agent as structure and rendered per channel. Generation emits
meaning; rendering emits format. Where those two collapse into one string, every downstream capability
that needs to address part of the message becomes impossible — not difficult, impossible.

This also extends QC's contract in a way worth stating explicitly: QC now performs a **structural**
review alongside its existing factual one. Its veto remains absolute and still fails closed (§9.1) — the
change is that "well-formed" joins "truthful" as something it can actually check.

### 17.2 Declared intent outranks inferred intent

Every engagement signal this system has ever had is **inferred**: an open, a click, a repeat open. §16.4
gave the Engagement Escalation agent an explicit boundary for exactly that reason — *"fires only on real
signal; never infers engagement where a channel provides none."*

A one-click "yes, I'm interested" is categorically different. It is **declared** — the lead stating
intent in their own action, not the system deducing it from behaviour. This architecture has never had a
first-party intent signal before, and it must not be flattened into the same bucket as an open count.

**Ranking rule, now explicit:**

| Signal | Kind | What it licenses |
| :-- | :-- | :-- |
| A reply, or a declared interest click | **Declared** | Immediate human escalation; stop all automated sequences |
| Repeat opens with no reply (§16.4) | **Inferred** | Escalate for human attention; never treat as consent or agreement |
| A single open, a link click | **Weak inferred** | Informs cadence and measurement only; never escalates alone |

Two consequences follow, and both are stated as constraints rather than preferences:

1. **A declared negative is not a legal opt-out.** A lead clicking "not interested" has declined *this
   pitch*; they have not revoked contactability. Writing that into the suppression list would silently
   and permanently destroy a channel the lead never closed. Suppression stays reachable only through the
   one-click unsubscribe, which is the mechanism that actually carries that meaning (§8, and the
   project's own 100% opt-out rule).
2. **A declared signal must be tamper-evident.** Because this signal arrives over a public,
   unauthenticated route, its integrity is part of its meaning. An unsigned or altered token is
   **refused**, never resolved to a best-guess lead — the same posture as "refuse an unconfigured region
   rather than guess a channel" (§16.4, Channel Router). A guessed identity attached to a declared intent
   would be worse than no signal, because the operator would act on it with full confidence.

### 17.3 A sequence is a conversation with a plot, not a repetition with a delay

§16.4 introduced the Cadence Agent with an authority ceiling — bound by suppression, pacing and the
kill-switch at every touch. That ceiling is correct and has held in production. What it never specified
is what each touch should *mean*.

In practice every follow-up receives the same instruction ("write a short nudge"), so touches 2 and 3
differ from touch 1 only by timing and model variance. That is not a sequence; it is one message sent
repeatedly at intervals.

**Principle established:** each touch in a sequence has a **distinct communicative goal**, and an agent
with nothing new to say should not send:

| Touch | Goal | Premise about the reader |
| :-- | :-- | :-- |
| First touch | Establish relevance | They have never heard of us |
| Follow-up 1 | Re-present, lead with the strongest asset | They skimmed it and did not act |
| Follow-up 2 | Ask an open question — aim for a reply, not another pitch | They read it and have an unspoken objection |
| Follow-up 3 | Leave a standing offer, not a chase | They are not a buyer now; the goal is to be remembered later |

The final touch is the one most likely to be written badly, so its constraint is explicit: it must read
as availability, not pressure. Escalating urgency into a fourth ask is the point at which persistence
becomes the harassment this architecture's own guardrails exist to prevent.

**Measurement obligation carries over unchanged.** §16.3's ordering rule — variants produced → measured
→ only then adapted — applies here without exception. Three new touch behaviours that cannot be
compared per-level are three guesses, and this architecture has already refused to ship that once.

### 17.4 One content object, many renderings

The operator wants the same outreach carried to other channels by hand — copy what went out by email,
paste it into Instagram or LinkedIn.

The naive implementation is a second generation call per channel. It is wrong for a reason that is
architectural rather than economical: **two independent generations of "the message for this lead"
drift.** The follow-up sent on Instagram would then reference a pain point the emailed version never
raised, or offer a trial the email did not mention — and the lead, who received both, experiences the
inconsistency as carelessness. Cost is a secondary objection; incoherence is the primary one.

**Principle established:** for a given lead and product there is **one canonical content object**,
generated once and stored. Each channel is a *rendering* of it — HTML with buttons for email, plain text
with full URLs for messaging platforms, condensed where a platform's norms require. Re-rendering is
always permitted; regenerating for a second channel is not.

This is the same distinction as §17.1, applied one level up: meaning is produced once, format is
produced per destination.

### 17.5 Relevance is about comprehension, not seniority

§16.2 established the boundary pattern — the human sets target roles, the AI matches inside them. It is
correct and stays. What it left unanswered is **which** role is the right boundary for a given product,
and the default assumption baked into most sales tooling — target the most senior person — is often
simply wrong.

The operator's own example is precise: pitching AI automation to a company's CEO or HR contact when the
person able to evaluate it is an engineer. The message can be flawless and still fail, because it reached
someone with no basis to assess the claim. Seniority predicts *authority to buy*; it does not predict
*ability to judge*. For a technical product, comprehension usually gates the conversation before
authority ever becomes relevant.

**Principle established:** the relevant role is inferred **from the product brief itself** — grounded in
what the product actually requires the reader to understand — and constrained by the operator's own role
list when one is set. The AI may narrow within a human-set list; it may never invent a role outside a
non-empty one. §16.2's hallucination boundary is unchanged; this only specifies what fills it.

Two limits are deliberate:

- **Attaching a person and messaging that person are different acts.** Phase 7's gate proved
  zero-wrong-company *attachment*. Autonomously messaging a named individual employee is a higher-
  consequence action than messaging a business — a wrong business is a nuisance, a wrong individual is
  a person receiving a pitch that was never about them. Person-level outreach stays human-initiated
  until that has its own gate.
- **A prospect found without a company lead is not a lead.** People sourced by a standalone criteria
  search never entered discovery, ICP matching or scoring. Recording them as leads would corrupt every
  funnel metric this document's §11 KPI framework depends on, by mixing a population that was never
  qualified into one that was. They are a separate population and must stay one.

### 17.6 Cross-sell without hype

The operator wants every outreach to mention that we also build AI automation — so a lead uninterested
in the pitched product but interested in AI services can still convert.

This sits in direct tension with `GUARDRAIL_PREAMBLE`'s buzzword ban, which already forbids exactly the
register this kind of line usually gets written in ("revolutionary", "cutting-edge", "unlock"). The
tension is real and resolving it by exception would hollow out the rule.

**Resolution:** the cross-sell is a **factual availability statement grounded in real product records**,
not a claim about AI in general. "We also build AI automation for businesses like yours" is a fact about
our catalogue. "AI is transforming how businesses operate" is hype, is unverifiable, and stays banned.
QC judges this line by the same zero-hallucination standard as any other claim — against the real
product records, not against market sentiment.

**And it is per-product opt-in, off by default.** A generic secondary offer appended to a highly
specific niche pitch dilutes the specificity that made the pitch work. This is §16.2's boundary pattern
once more: the operator decides where a second offer helps; the AI writes it where they have said it
does.

### 17.7 What this chapter does not change

Stated explicitly, because every chapter that widens a system's autonomy should also name what it left
alone:

- **QC's veto is still absolute** (§2, §8) and still fails closed. Structural review is added *to* it,
  never traded against it.
- **Every autonomous action still routes through the Decision Engine** (§4) and lands in `agent_events`.
- **The autonomous-outreach kill-switch still gates every real send**, follow-up levels included.
- **The 100% opt-out rule is untouched** — and §17.2 explicitly protects it from being widened into
  something it never meant.
- **§16.5's channel-reality constraint holds**: LinkedIn/Instagram/Facebook remain human-send only, and
  this architecture still contains no code path capable of auto-sending on them. Phase 14 makes copying
  easier; it does not make sending automatic, and its gate re-verifies that by absence rather than
  assuming it still holds.

---

## Conclusion & Architectural Sign-Off

This **AI Sales Intelligence PRD v2** defines the complete cognitive, decision-making, and organizational framework required to transform the technical plumbing (Flask, SQLite, Playwright, and — as actually implemented, per the v2.2 amendment — an in-process discovery scheduler rather than n8n) into an **autonomous, enterprise-grade AI Sales Team** — and, with Chapter 15, extends that framework upward into a governing **Executive Business Layer (AI-BOS)** that turns the sales team into a revenue-and-capacity-aware business operating system.

By separating the **Technical Execution Layer (PRD v3)**, the **Cognitive Brain Layer (Chapters 1–12)**, the **Enterprise Executive Layer (Chapter 15)**, the **Multi-Channel Engagement & Adaptive Messaging Layer (Chapter 16)**, and the **Message Composition, Declared Intent & Person-Level Relevance layer (Chapter 17)**, the system achieves maximum modularity, zero-hallucination reliability, strict compliance, and scalable human-AI collaboration — with every layer's autonomy bounded by the one above it, and every channel's autonomy bounded by what that channel's own platform and jurisdiction actually permit.

**On the progression of Chapters 15 → 16 → 17.** Each was written from a different vantage point, and
the sequence is worth reading as one argument. Chapter 15 added a layer *above* the brain to govern it.
Chapter 16 *widened* the brain, from an operator who could not yet see it work. Chapter 17 *sharpens*
it, from the same operator watching it work correctly and finding that correctness was not sufficient —
a message can be truthful, compliant, well-targeted and measured, and still fail to persuade, fail to be
answerable in one click, repeat itself, contradict itself across channels, or land in front of someone
with no basis to judge it. Chapters 16 and 17 together make the point that an autonomous system's
maturity is measured by the *quality* of the problems its operator is left with.
