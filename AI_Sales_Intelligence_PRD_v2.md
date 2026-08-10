# AI Sales Intelligence PRD v2: Autonomous AI Sales Operating System (The Brain Layer)

**Document Version:** 2.1.0-INTELLIGENCE  
**System Classification:** Enterprise Autonomous Multi-Agent Sales Operating System  
**Layer Focus:** Autonomous Cognition, Decision-Making, Strategy, Adaptability, Memory & Organizational Orchestration  
**v2.1 Addendum:** Chapter 15 — Enterprise Executive Business & Operating System Layer (AI-BOS). Implementation blueprints for the modules below live in `MASTER_DEVELOPMENT_PRD.md` §8 (spec) and Phase 5 (§5, build order); this chapter defines the cognitive/strategic contract, MASTER defines the code.

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

|  \- Playwright Scrapers             \- n8n Workflow Dispatchers                     |

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

#### C. ICP & Strategy Agent (Audience Intelligence)

* **Purpose:** Analyzes target industries, firmographics, and pain points to define exact Ideal Customer Profiles (ICPs).  
* **Inputs:** Product Brief JSON (Value props, target verticals, pricing tier).  
* **Outputs:** Detailed ICP Definitions (Target company size, role titles, key review complaints to search for).

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
|  - Playwright Scrapers             - n8n Workflow Dispatchers                     |
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

## Conclusion & Architectural Sign-Off

This **AI Sales Intelligence PRD v2** defines the complete cognitive, decision-making, and organizational framework required to transform the technical plumbing (Flask, SQLite, n8n, Playwright) into an **autonomous, enterprise-grade AI Sales Team** — and, with Chapter 15, extends that framework upward into a governing **Executive Business Layer (AI-BOS)** that turns the sales team into a revenue-and-capacity-aware business operating system.

By separating the **Technical Execution Layer (PRD v3)**, the **Cognitive Brain Layer (Chapters 1–12)**, and the **Enterprise Executive Layer (Chapter 15)**, the system achieves maximum modularity, zero-hallucination reliability, strict compliance, and scalable human-AI collaboration — with every layer's autonomy bounded by the one above it.
