"""Phase 17 Step 17.3 -- campaign metrics, computed LIVE from real tables every time,
never read from `campaigns.metrics_summary` as a source of truth. Same real
sent/seen/replied derivation `services/analytics_service.py`'s outreach-funnel already
uses (OutreachLog.status/read_at + a real InboundConversation reply lookup), just scoped
to one campaign's tagged leads (leads.campaign_id) instead of a date window. Real send
volume is small (daily caps 40/channel), so a per-row reply lookup is cheap here too --
same reasoning analytics_service.py's own docstring gives.

Phase 18 Step 18.1 additions (2026-09-01 revision, see tracker.md): a campaign is ALWAYS
human-created -- nothing here ever writes a new `campaigns` row. `generate_campaign_todo`
refreshes an EXISTING (human-made) campaign's `daily_todo` from real signals;
`generate_campaign_suggestion` only logs a `CAMPAIGN_SUGGESTED` note to `agent_events` for
a human to act on, never creates anything itself.
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timedelta

from agents.outreach_agent import draft_structured_email, suggest_draft_improvement
from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import (
    CAMPAIGN_TODO_SYSTEM_PROMPT, CAMPAIGN_SUGGESTION_SYSTEM_PROMPT, EXECUTION_WATCHDOG_SYSTEM_PROMPT,
    CONVERSATIONAL_PUSHBACK_SYSTEM_PROMPT)
from config import Config
from database.models import (
    AgentEvent, Campaign, CampaignThesis, InboundConversation, Lead, LeadReviewInsight, LeadScore, OutreachLog,
    Product)
from services.message_format_service import get_available_assets
from services.outreach.cross_sell import get_cross_sell_products
from services.reporting_service import IST_OFFSET
from services.system_settings import get_bool, AUTONOMOUS_OUTREACH_ENABLED

_KB_GAP_LOOKBACK_DAYS = 14
_SUGGESTION_LOOKBACK_DAYS = 7
_WATCHDOG_CONSECUTIVE_THRESHOLD = 3
_WATCHDOG_FAILURE_STATUSES = ("FAILED", "BOUNCED")

# Campaign email render mode (2026-09-05): HTML = Phase 11 designed sections +
# render_email_html for preview and send; TEXT = prose draft, plain preview, send
# without designed sections (email_service simple HTML fallback).
VALID_EMAIL_RENDER_MODES = frozenset({"HTML", "TEXT"})
TEXT_FORMAT_DIRECTIVE = (
    "Write a short plain-text personal email in continuous prose only. "
    "No badge lists, no card-style structured sections, no bullet-heavy layout -- "
    "readable as a simple email someone would send from Gmail."
)


def resolve_email_render_mode(campaign) -> str:
    mode = (getattr(campaign, "email_render_mode", None) or "HTML")
    mode = str(mode).strip().upper()
    return mode if mode in VALID_EMAIL_RENDER_MODES else "HTML"


def format_directive_for_mode(mode: str, product_default) -> str:
    if mode == "TEXT":
        return TEXT_FORMAT_DIRECTIVE
    return product_default


def detect_render_mode_request(instruction: str) -> str | None:
    """If free-text feedback clearly asks for HTML vs plain text, return that mode."""
    t = (instruction or "").lower()
    if any(h in t for h in (
        "plain text", "plain-text", "sirf text", "text only", "text mode",
        "no html", "bina html", "without html", "simple text",
    )):
        return "TEXT"
    if any(h in t for h in (
        "html template", "html email", "designed email", "html banao",
        "html me", "html mode", "use html", "with html",
    )):
        return "HTML"
    return None


def build_sample_draft_html(mode: str, draft: dict | None) -> str | None:
    """Preview-only HTML via Phase 11 renderer; unsubscribe is a inert # link.

    Real sends append INTEREST (Yes/No) in outreach_handler after QC, using signed URLs.
    Daily Review / kickoff preview has no outreach_log yet, so we append the same strip
    here with inert `#` links -- display-only, so the human sees what the real HTML send
    will include.
    """
    if mode != "HTML" or not isinstance(draft, dict):
        return None
    sections = draft.get("sections")
    if not sections:
        return None
    preview_sections = list(sections)
    if not any(isinstance(s, dict) and s.get("type") == "INTEREST" for s in preview_sections):
        preview_sections.append({
            "type": "INTEREST",
            "prompt": "Would this be worth a look?",
            "yes_url": "#",
            "no_url": "#",
            "yes_label": "Yes, tell me more",
            "no_label": "Not right now",
        })
    from services.outreach.email_renderer import render_email_html
    return render_email_html(
        preview_sections, unsubscribe_url="#", headline=draft.get("subject") or "",
        for_preview=True)



def _today_ist() -> str:
    return (datetime.utcnow() + IST_OFFSET).strftime("%Y-%m-%d")


def _pain_point_text(item) -> str:
    """LeadReviewInsight.pain_points_extracted's real shape (Scoring Agent's own OUTPUT
    JSON, MASTER §6) is a list of {code, evidence_quote, severity_0_1} objects, not plain
    strings -- a real bug caught live (2026-09-01): rendering one of these objects
    directly as React text crashed the whole page (real browser console error: "Objects
    are not valid as a React child"). This is the one safe extraction point every caller
    that wants a human-readable line should go through, rather than each guessing the
    shape itself."""
    if isinstance(item, dict):
        return str(item.get("evidence_quote") or item.get("code") or "")
    return str(item)


# Same active-status set Phase 18's Daily Review already filters campaigns by
# (DailyReviewPanel.jsx) -- COMPLETED/PAUSED campaigns never claim new leads.
ACTIVE_CAMPAIGN_STATUSES = ("PROPOSED", "APPROVED", "RUNNING")


def resolve_auto_campaign_id(db, product_id: str) -> str | None:
    """A new lead for a product auto-joins that product's own campaign -- but only when
    there's exactly ONE currently-active campaign for that product. A human picks the
    campaign when the leads are created (Discovery's search is already scoped to one
    product, Campaigns.py's own create form picks a product too), so in the common case
    (one product, one live campaign) this needs no manual tagging step at all.

    Real gap this fixes (2026-09-02, user-flagged): before this, `leads.campaign_id` was
    never set by ANY code path, so a freshly human-created campaign's metrics/sample-draft
    stayed empty forever. When two+ campaigns are active for the same product at once,
    this deliberately does NOT guess which one a new lead belongs to -- returns None, same
    as today, and a human can still set it explicitly (create_lead's own `campaign_id`
    field, or a future edit path)."""
    active = db.query(Campaign).filter(
        Campaign.product_id == product_id,
        Campaign.status.in_(ACTIVE_CAMPAIGN_STATUSES),
    ).all()
    return active[0].id if len(active) == 1 else None


def eligible_campaigns_for_discovery(db, product_id: str) -> list[Campaign]:
    """Step 17.7 (2026-09-02, MASTER_DEVELOPMENT_PRD.md §5C.0's revision) -- discovery is
    now campaign-driven, not just campaign-gated: every active campaign for this product
    with a REAL target_segment (both industry and location set -- a campaign the strategist
    hasn't targeted yet has nothing to search for) and, if it has a `lead_count_goal`, whose
    real tagged-lead count hasn't reached it yet. Each eligible campaign runs its OWN
    discovery using its OWN target -- this is what makes a newly-found lead's campaign_id
    unambiguous by construction: it comes from the very DISCOVER job that found it, never
    guessed afterward. Superseded `discovery_should_run_for_product()`'s single yes/no gate
    (that couldn't say which campaign's target to search, only whether >=1 existed) --
    THIS is what actually resolves the "2+ active campaigns" ambiguity, not a rule about
    which one wins: there is no single winner, each runs independently."""
    active = db.query(Campaign).filter(
        Campaign.product_id == product_id,
        Campaign.status.in_(ACTIVE_CAMPAIGN_STATUSES),
    ).all()
    eligible = []
    for campaign in active:
        target = json.loads(campaign.target_segment or "{}")
        if not target.get("industry") or not target.get("location"):
            continue
        if campaign.lead_count_goal is not None:
            tagged_count = db.query(Lead).filter(Lead.campaign_id == campaign.id).count()
            if tagged_count >= campaign.lead_count_goal:
                continue
        eligible.append(campaign)
    return eligible


def compute_campaign_metrics(db, campaign_id: str) -> dict:
    """Returns {"sent": int, "opened": int, "replied": int, "hot": int} -- always a real
    query against outreach_logs/leads for this campaign's tagged leads, so a UI reading
    this can never drift from what actually happened (Step 17.3's own requirement)."""
    lead_ids = [row[0] for row in db.query(Lead.id).filter(Lead.campaign_id == campaign_id).all()]
    if not lead_ids:
        return {"sent": 0, "opened": 0, "replied": 0, "hot": 0}

    logs = db.query(OutreachLog).filter(
        OutreachLog.lead_id.in_(lead_ids), OutreachLog.status == "SENT"
    ).all()

    sent = len(logs)
    opened = 0
    replied = 0
    for log in logs:
        if log.read_at is not None:
            opened += 1
        # >= a formatted string, not `> log.sent_at` (a raw datetime object) -- SQLite
        # stores CURRENT_TIMESTAMP with no microseconds but SQLAlchemy's sqlite dialect
        # binds a Python datetime WITH ".000000", so a plain `>`/`>=` against the object
        # silently loses any reply landing in the same recorded second as the send (real
        # root cause found 2026-09-02, see reference_sqlite_datetime_string_compare
        # memory -- this was the pre-existing, lower-risk instance of that same bug).
        sent_at_str = log.sent_at.strftime("%Y-%m-%d %H:%M:%S")
        is_replied = db.query(InboundConversation).filter(
            InboundConversation.lead_id == log.lead_id,
            InboundConversation.channel == log.channel,
            InboundConversation.sender_type == "LEAD",
            InboundConversation.created_at >= sent_at_str,
        ).first() is not None
        if is_replied:
            replied += 1

    hot = db.query(Lead).filter(Lead.campaign_id == campaign_id, Lead.status == "HOT_LEAD").count()

    return {"sent": sent, "opened": opened, "replied": replied, "hot": hot}


def compute_campaign_lead_summary(db, campaign_id: str) -> dict:
    """Campaign Detail page (UI Phase 16 revision, 2026-09-02) -- "aaj X leads mile, Y kaam
    ke the" in the operator's own words. `found_today`/`qualified_today` are scoped to the
    real IST calendar day, matching this project's other daily-boundary logic
    (`_run_daily_plan_tick`, `approve_campaign_today`'s `_today_ist()`) rather than a
    rolling 24h window. "Qualified" reuses the existing Score agent's own tier judgment
    (HOT/WARM) -- no new qualification logic invented for this."""
    today = _today_ist()
    leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
    total = len(leads)
    lead_ids = [l.id for l in leads]
    found_today_ids = [l.id for l in leads if str(l.created_at)[:10] == today]

    qualified_tiers = {"HOT", "WARM"}
    scores = {
        s.lead_id: s.tier for s in
        db.query(LeadScore).filter(LeadScore.lead_id.in_(lead_ids)).all()
    } if lead_ids else {}

    return {
        "total": total,
        "found_today": len(found_today_ids),
        "qualified_today": sum(1 for lid in found_today_ids if scores.get(lid) in qualified_tiers),
        "qualified_total": sum(1 for lid in lead_ids if scores.get(lid) in qualified_tiers),
    }


def _ready_to_dispatch_count(db, campaign_id: str) -> int:
    """Real count of this campaign's qualified-but-unsent leads -- the EXACT SCORED+HOT/
    WARM definition `discovery_scheduler.py`'s `_run_outreach_tick()` itself already uses
    to claim leads, so this is precisely what would start moving the moment
    AUTONOMOUS_OUTREACH_ENABLED goes on. Fed to the daily strategist (2026-09-02) so it can
    mention this in its own words when relevant -- never a hardcoded system banner; see
    CAMPAIGN_TODO_SYSTEM_PROMPT's own instruction for why."""
    return db.query(Lead).join(LeadScore, LeadScore.lead_id == Lead.id).filter(
        Lead.campaign_id == campaign_id, Lead.status == "SCORED", LeadScore.tier.in_(("HOT", "WARM")),
    ).count()


def evaluate_execution_watchdog(db, campaign_id: str | None) -> dict | None:
    """Phase 20 Step 20.3 -- a single, event-triggered anomaly check, called right after a
    real OutreachLog transitions to FAILED/BOUNCED (api/webhooks.py's Resend handler,
    api/inbound.py's WhatsApp status handler) -- NOT a continuous supervising loop, same
    bounded discipline the Gemini architecture review favored for this whole system.

    Looks at this campaign's own leads' most recent _WATCHDOG_CONSECUTIVE_THRESHOLD real
    sends (by sent_at) -- if EVERY one of them is a real failure, raises one grounded alert
    (an LLM call, quoting the real count/channel) and persists it to
    campaign.watchdog_alert. `_run_outreach_tick` skips claiming further leads for this
    ONE campaign while an alert is active -- every other campaign is unaffected, and
    AUTONOMOUS_OUTREACH_ENABLED itself is never touched in either direction.

    Idempotent: if this campaign already has an active alert, returns it unchanged rather
    than re-running the check or re-calling the LLM -- an already-paused campaign doesn't
    need to be told twice. Returns None for a lead never tagged to a campaign (nothing to
    protect) or when the real recent-sends pattern doesn't actually meet the threshold."""
    if not campaign_id:
        return None
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        return None
    if campaign.watchdog_alert:
        return json.loads(campaign.watchdog_alert)

    lead_ids = [row[0] for row in db.query(Lead.id).filter(Lead.campaign_id == campaign_id).all()]
    if not lead_ids:
        return None
    recent = (
        db.query(OutreachLog)
        .filter(OutreachLog.lead_id.in_(lead_ids), OutreachLog.sent_at.isnot(None))
        .order_by(OutreachLog.sent_at.desc())
        .limit(_WATCHDOG_CONSECUTIVE_THRESHOLD)
        .all()
    )
    if len(recent) < _WATCHDOG_CONSECUTIVE_THRESHOLD:
        return None
    if not all(log.status in _WATCHDOG_FAILURE_STATUSES for log in recent):
        return None

    channel_breakdown = dict(Counter(log.channel for log in recent))
    prompt = EXECUTION_WATCHDOG_SYSTEM_PROMPT + f"""
CAMPAIGN_NAME: {json.dumps(campaign.name, ensure_ascii=False)}
BOUNCE_COUNT: {json.dumps(len(recent))}
CHANNEL_BREAKDOWN: {json.dumps(channel_breakdown, ensure_ascii=False)}
TARGET_SEGMENT: {json.dumps(json.loads(campaign.target_segment or "{}"), ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
        message = str(data.get("message", "")).strip()[:400]
    except LLMError:
        message = ""
    if not message:
        # never a silent pause with nothing to show a human -- a plain, real, honest
        # fallback sentence if the LLM call itself failed (never fabricates a cause).
        message = (
            f"{len(recent)} consecutive sends failed/bounced for this campaign "
            f"({', '.join(f'{v} on {k}' for k, v in channel_breakdown.items())}) -- "
            "further sends for this campaign are paused pending review."
        )

    alert = {
        "reason": "consecutive_failures",
        "bounce_count": len(recent),
        "channel_breakdown": channel_breakdown,
        "message": message,
        "raised_at": datetime.utcnow().isoformat(),
    }
    campaign.watchdog_alert = json.dumps(alert)
    db.commit()
    log_agent_event(db, "CAMPAIGN", None, "EXECUTION_WATCHDOG_TRIGGERED", 1.0, "MEDIUM", "EXECUTE",
                    payload={"campaign_id": campaign_id, **alert})
    return alert


def check_instruction_pushback(db, campaign_id: str | None, instruction: str) -> str | None:
    """Phase 20 Step 20.4 -- one extra, separate check alongside the EXISTING Step 16.5
    revise-draft flow (api/leads.py's revise_outreach_draft). Never blocks or overrides the
    human's instruction -- the draft always regenerates from it exactly as before; this
    only decides whether a real, concrete disagreement (grounded in this campaign's own
    real metrics or a Phase 19 validated insight) is ALSO worth surfacing alongside it.
    Returns None for a lead never tagged to a campaign (nothing real to check against yet)
    or whenever no genuine conflict is found -- never invents one to seem vigilant."""
    if not campaign_id:
        return None
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        return None

    metrics = compute_campaign_metrics(db, campaign_id)
    from services.strategy_reflection_service import get_active_insights_for_product
    strategy_insights = get_active_insights_for_product(db, campaign.product_id)

    prompt = CONVERSATIONAL_PUSHBACK_SYSTEM_PROMPT + f"""
HUMAN_INSTRUCTION: {json.dumps(instruction, ensure_ascii=False)}
CAMPAIGN_STRATEGY_ANGLE: {json.dumps(campaign.strategy_angle or "", ensure_ascii=False)}
CAMPAIGN_METRICS: {json.dumps(metrics, ensure_ascii=False)}
STRATEGY_INSIGHTS: {json.dumps(strategy_insights, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
    except LLMError:
        return None  # never blocks the real revision on a failed side-check

    pushback = data.get("pushback")
    return str(pushback).strip()[:400] if pushback else None


def clear_campaign_watchdog_alert(db, campaign_id: str) -> None:
    """The only way a Step 20.3 alert is ever cleared -- a real human decision, never the
    system re-checking and clearing itself on its own."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    campaign.watchdog_alert = None
    db.commit()


def _sibling_campaign_summaries(db, product_id: str, exclude_id: str) -> list[dict]:
    """Every OTHER real campaign (past or active) for the same product -- same fetch
    shape `generate_campaign_suggestion` already uses, now ALSO fed to the daily
    strategist (2026-09-02) so a brand-new campaign's first real proposal can build on a
    same-product sibling's real result instead of guessing blind."""
    siblings = db.query(Campaign).filter(
        Campaign.product_id == product_id, Campaign.id != exclude_id
    ).all()
    return [
        {
            "name": c.name,
            "target_segment": json.loads(c.target_segment or "{}"),
            "strategy_angle": c.strategy_angle,
            "metrics": compute_campaign_metrics(db, c.id),
        }
        for c in siblings
    ]


def _clean_proposal(raw) -> dict | None:
    """Validates the strategist's optional structural proposal -- never trusts the LLM's
    shape blindly. Returns None if nothing usable survives (e.g. lead_count_goal wasn't a
    real positive number, or every field was empty/missing)."""
    if not isinstance(raw, dict):
        return None
    cleaned = {}
    target_segment = raw.get("target_segment")
    if isinstance(target_segment, dict) and target_segment:
        cleaned["target_segment"] = target_segment
    lead_count_goal = raw.get("lead_count_goal")
    if isinstance(lead_count_goal, (int, float)) and not isinstance(lead_count_goal, bool) and lead_count_goal > 0:
        cleaned["lead_count_goal"] = int(lead_count_goal)
    strategy_angle = raw.get("strategy_angle")
    if isinstance(strategy_angle, str) and strategy_angle.strip():
        cleaned["strategy_angle"] = strategy_angle.strip()[:500]
    email_render_mode = raw.get("email_render_mode")
    if isinstance(email_render_mode, str) and email_render_mode.strip().upper() in VALID_EMAIL_RENDER_MODES:
        cleaned["email_render_mode"] = email_render_mode.strip().upper()
    if not cleaned:
        return None
    rationale = raw.get("rationale")
    cleaned["rationale"] = str(rationale).strip()[:250] if rationale else ""
    # Phase 20 Step 20.2 -- only the daily strategist (generate_campaign_todo) asks for a
    # real confidence; generate_campaign_suggestion's prompt doesn't, so this is None there,
    # not a faked default.
    confidence = raw.get("confidence")
    if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
        cleaned["confidence"] = max(0.0, min(1.0, float(confidence)))
    else:
        cleaned["confidence"] = None
    return cleaned


def _clean_journal(raw) -> dict | None:
    """Phase 20 Step 20.1 -- validates the strategist's optional daily journal entry.
    Returns None if there's no real `hypothesis` to record (e.g. the field was missing or
    blank) -- a day with nothing genuine to say gets no journal row at all, same
    never-fill-space discipline as `todo`/`proposal`."""
    if not isinstance(raw, dict):
        return None
    hypothesis = str(raw.get("hypothesis", "")).strip()[:500]
    if not hypothesis:
        return None
    observation = raw.get("observation")
    observation = str(observation).strip()[:500] if observation else None
    pivot_decision = raw.get("pivot_decision")
    pivot_decision = str(pivot_decision).strip()[:500] if pivot_decision else None
    return {"hypothesis": hypothesis, "observation": observation, "pivot_decision": pivot_decision}


def _thesis_dict(row) -> dict | None:
    if not row:
        return None
    return {"day": row.day, "hypothesis": row.hypothesis, "observation": row.observation,
            "pivot_decision": row.pivot_decision}


def _recent_journal_entries(db, campaign_id: str, limit: int = 7) -> list[dict]:
    """This campaign's own persistent thesis log (Phase 20 Step 20.1) -- real prior entries,
    oldest first so the strategist reads it as a timeline. Excludes TODAY's own row (a
    same-day re-run of generate_campaign_todo must never compare the journal against
    itself)."""
    rows = (
        db.query(CampaignThesis)
        .filter(CampaignThesis.campaign_id == campaign_id, CampaignThesis.day != _today_ist())
        .order_by(CampaignThesis.day.desc())
        .limit(limit)
        .all()
    )
    return [_thesis_dict(r) for r in reversed(rows)]


def _recent_kb_gap_topics(db, product_id: str) -> list[str]:
    """Real Step 16.7 signals for this product, last _KB_GAP_LOOKBACK_DAYS days. payload
    isn't a queryable column (it's JSON text), so this filters in Python -- real event
    volume is small enough that this is cheap, same posture as compute_campaign_metrics'
    own per-row approach."""
    cutoff = datetime.utcnow() - timedelta(days=_KB_GAP_LOOKBACK_DAYS)
    events = db.query(AgentEvent).filter(
        AgentEvent.action_type == "KB_GAP_DETECTED", AgentEvent.created_at >= cutoff
    ).all()
    topics = []
    for e in events:
        try:
            payload = json.loads(e.payload or "{}")
        except ValueError:
            continue
        if payload.get("product_id") == product_id and payload.get("topic"):
            topics.append(payload["topic"])
    return topics


def generate_campaign_todo(db, campaign_id: str) -> dict:
    """AI Sales Manager's daily strategy review for one EXISTING (human-made) campaign.
    Rewritten 2026-09-02 (tracker.md): no kickoff/ongoing split, no fixed to-do types --
    one strategist reading whatever real data exists today, the same mechanism whether
    that's nothing yet (a fresh campaign's first day) or a real track record. Never
    creates a campaign. Returns {"todo": [...], "proposal": {...}|None,
    "journal": {...}|None} -- also persisted onto campaign.daily_todo /
    campaign.pending_strategy_proposal / a campaign_theses row (Phase 20 Step 20.1, one row
    per campaign per real IST day -- an upsert, so a same-day re-run overwrites today's own
    entry rather than duplicating it). The proposal is NOT applied to
    target_segment/lead_count_goal/strategy_angle here -- only approve_campaign_today()
    does that, once a human has actually seen it. The journal is different from
    `proposal`/`todo`: it is the strategist's own persistent, dated narrative belief about
    this campaign, carried across days regardless of whether anything today needs human
    action."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    product = db.get(Product, campaign.product_id)

    metrics = compute_campaign_metrics(db, campaign_id)
    kb_gap_topics = _recent_kb_gap_topics(db, campaign.product_id)
    sibling_campaigns = _sibling_campaign_summaries(db, campaign.product_id, exclude_id=campaign_id)
    ready_to_dispatch_count = _ready_to_dispatch_count(db, campaign_id)
    outreach_enabled = get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=Config.AUTONOMOUS_OUTREACH_ENABLED)
    # Step 19.4 -- local import to avoid a module-load cycle (strategy_reflection_service
    # itself imports compute_campaign_metrics from this module), same pattern
    # system_settings.get_all() already uses for its own Config import.
    from services.strategy_reflection_service import get_active_insights_for_product
    strategy_insights = get_active_insights_for_product(db, campaign.product_id)
    today = _today_ist()
    prior_journal = _recent_journal_entries(db, campaign_id)

    prompt = CAMPAIGN_TODO_SYSTEM_PROMPT + f"""
CAMPAIGN_NAME: {json.dumps(campaign.name, ensure_ascii=False)}
TARGET_SEGMENT: {json.dumps(json.loads(campaign.target_segment or "{}"), ensure_ascii=False)}
LEAD_COUNT_GOAL: {json.dumps(campaign.lead_count_goal)}
STRATEGY_ANGLE: {json.dumps(campaign.strategy_angle or "", ensure_ascii=False)}
PRODUCT_BRIEF: {json.dumps({"title": product.title, "description": product.description}, ensure_ascii=False)}
PRODUCT_TARGET_REGIONS: {json.dumps(json.loads(product.target_regions or "[]"), ensure_ascii=False)}
PRODUCT_TARGET_BUSINESS_CATEGORIES: {json.dumps(json.loads(product.target_business_categories or "[]"), ensure_ascii=False)}
METRICS: {json.dumps(metrics, ensure_ascii=False)}
KB_GAP_TOPICS: {json.dumps(kb_gap_topics, ensure_ascii=False)}
STRATEGY_INSIGHTS: {json.dumps(strategy_insights, ensure_ascii=False)}
PRIOR_JOURNAL: {json.dumps(prior_journal, ensure_ascii=False)}
SIBLING_CAMPAIGNS: {json.dumps(sibling_campaigns, ensure_ascii=False)}
READY_TO_DISPATCH_COUNT: {json.dumps(ready_to_dispatch_count)}
AUTONOMOUS_OUTREACH_ENABLED: {json.dumps(outreach_enabled)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
    except LLMError as exc:
        log_agent_event(db, "CAMPAIGN", None, "GENERATE_TODO", 0.0, "LOW", "EXECUTE",
                        payload={"campaign_id": campaign_id, "error": str(exc)})
        # leave existing todo/proposal/journal untouched on failure
        return {
            "todo": json.loads(campaign.daily_todo or "[]"),
            "proposal": json.loads(campaign.pending_strategy_proposal) if campaign.pending_strategy_proposal else None,
            "journal": _thesis_dict(db.query(CampaignThesis).filter_by(campaign_id=campaign_id, day=today).first()),
        }

    raw_todo = data.get("todo")
    todo = []
    if isinstance(raw_todo, list):
        for item in raw_todo:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()[:30]
            text = str(item.get("text", "")).strip()[:250]
            if text:
                todo.append({"label": label or "Note", "text": text})

    proposal = _clean_proposal(data.get("proposal"))
    journal = _clean_journal(data.get("journal"))

    campaign.daily_todo = json.dumps(todo)
    campaign.pending_strategy_proposal = json.dumps(proposal) if proposal else None
    if journal:
        thesis = db.query(CampaignThesis).filter_by(campaign_id=campaign_id, day=today).first()
        if thesis:
            thesis.hypothesis = journal["hypothesis"]
            thesis.observation = journal["observation"]
            thesis.pivot_decision = journal["pivot_decision"]
        else:
            db.add(CampaignThesis(campaign_id=campaign_id, day=today, **journal))
    db.commit()
    log_agent_event(db, "CAMPAIGN", None, "GENERATE_TODO", 1.0, "LOW", "EXECUTE",
                    payload={"campaign_id": campaign_id, "todo_count": len(todo), "has_proposal": bool(proposal),
                             "has_journal": bool(journal)})
    return {"todo": todo, "proposal": proposal, "journal": {"day": today, **journal} if journal else None}


def generate_campaign_suggestion(db, product_id: str) -> dict | None:
    """Notices, from real data, when a product looks worth a fresh campaign push -- never
    creates a campaign. Logs a CAMPAIGN_SUGGESTED agent_event (existing table, no new one)
    only when the model returns a real, non-empty suggestion. Returns
    {"suggestion": str, "target_segment": dict|None, "lead_count_goal": int|None}, or None
    if nothing concrete stood out. 2026-09-02: now also proposes a concrete target (not
    just a nudge sentence) -- this is what a human clicking "Create this campaign" straight
    from the suggestion (Dashboard) pre-fills the create form with."""
    product = db.get(Product, product_id)
    if not product:
        raise ValueError(f"product {product_id} not found")

    kb_gap_topics = _recent_kb_gap_topics(db, product_id)
    past_campaigns = db.query(Campaign).filter(Campaign.product_id == product_id).all()
    campaign_summaries = [
        {
            "name": c.name,
            "target_segment": json.loads(c.target_segment or "{}"),
            "strategy_angle": c.strategy_angle,
            "metrics": compute_campaign_metrics(db, c.id),
        }
        for c in past_campaigns
    ]

    prompt = CAMPAIGN_SUGGESTION_SYSTEM_PROMPT + f"""
PRODUCT_BRIEF: {json.dumps({"title": product.title, "description": product.description}, ensure_ascii=False)}
PRODUCT_TARGET_REGIONS: {json.dumps(json.loads(product.target_regions or "[]"), ensure_ascii=False)}
PRODUCT_TARGET_BUSINESS_CATEGORIES: {json.dumps(json.loads(product.target_business_categories or "[]"), ensure_ascii=False)}
KB_GAP_TOPICS: {json.dumps(kb_gap_topics, ensure_ascii=False)}
PAST_CAMPAIGNS: {json.dumps(campaign_summaries, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
    except LLMError as exc:
        log_agent_event(db, "CAMPAIGN", None, "SUGGEST_CAMPAIGN", 0.0, "LOW", "EXECUTE",
                        payload={"product_id": product_id, "error": str(exc)})
        return None

    suggestion = str(data.get("suggestion", "")).strip()[:250]
    if not suggestion:
        return None

    cleaned = _clean_proposal({
        "target_segment": data.get("target_segment"),
        "lead_count_goal": data.get("lead_count_goal"),
        "rationale": suggestion,
    }) or {}
    result = {
        "suggestion": suggestion,
        "target_segment": cleaned.get("target_segment"),
        "lead_count_goal": cleaned.get("lead_count_goal"),
    }

    log_agent_event(db, "CAMPAIGN", None, "CAMPAIGN_SUGGESTED", 1.0, "LOW", "EXECUTE",
                    payload={"product_id": product_id, **result})
    return result


def get_live_campaign_suggestions(db) -> list[dict]:
    """Every active product's most recent CAMPAIGN_SUGGESTED event, if it's still "live":
    within _SUGGESTION_LOOKBACK_DAYS AND no campaign has been created for that product
    since the suggestion fired (a human acting on it, via this suggestion or otherwise,
    naturally retires it -- no separate "dismissed" flag needed). Computed fresh from
    agent_events + campaigns every call, same "never a stale cache" discipline as
    compute_campaign_metrics."""
    products = db.query(Product).filter(Product.is_active == 1).all()

    # payload isn't queryable (JSON text) -- filter/group in Python once, same posture as
    # _recent_kb_gap_topics; real event volume is small enough this is cheap.
    cutoff = datetime.utcnow() - timedelta(days=_SUGGESTION_LOOKBACK_DAYS)
    events = (
        db.query(AgentEvent)
        .filter(AgentEvent.action_type == "CAMPAIGN_SUGGESTED", AgentEvent.created_at >= cutoff)
        .order_by(AgentEvent.created_at.desc())
        .all()
    )
    latest_by_product = {}
    for e in events:
        pid = json.loads(e.payload or "{}").get("product_id")
        if pid and pid not in latest_by_product:  # already sorted desc -- first hit is latest
            latest_by_product[pid] = e

    live = []
    for product in products:
        event = latest_by_product.get(product.id)
        if not event:
            continue
        # Real root cause found live (2026-09-02), NOT just "same-second granularity":
        # SQLite has no native datetime type -- `created_at` is stored as TEXT via SQL's
        # own CURRENT_TIMESTAMP ('2026-09-02 08:56:28', no microseconds), but SQLAlchemy's
        # sqlite dialect binds a Python datetime.datetime parameter as
        # '2026-09-02 08:56:28.000000' (WITH microseconds). SQLite then compares both as
        # plain strings -- and the shorter, no-microseconds stored value always sorts
        # BEFORE the longer bound one, so `Campaign.created_at >= event.created_at` was
        # false even for the literal same instant. Confirmed via SQLAlchemy engine echo,
        # not guessed. Fix: format the bound value to match SQLite's own CURRENT_TIMESTAMP
        # text shape before comparing, instead of letting the dialect add microseconds.
        cutoff_str = event.created_at.strftime("%Y-%m-%d %H:%M:%S")
        acted_on = db.query(Campaign).filter(
            Campaign.product_id == product.id, Campaign.created_at >= cutoff_str
        ).first()
        if acted_on:
            continue
        payload = json.loads(event.payload or "{}")
        live.append({
            "product_id": product.id,
            "product_title": product.title,
            "suggestion": payload.get("suggestion", ""),
            "target_segment": payload.get("target_segment"),
            "lead_count_goal": payload.get("lead_count_goal"),
            "created_at": str(event.created_at),
        })
    return live


def get_daily_review(db, campaign_id: str) -> dict:
    """Phase 18 Step 18.2 -- the 2-minute morning review: today's real to-do (Step 18.1)
    plus ONE real sample draft for this campaign, so the human sees actual content, not
    just a description of it. The sample is drafted for a REAL lead already tagged to
    this campaign, using the campaign's own strategy_angle as the tone directive
    (Step 16.4's exact mechanism) -- if no lead is tagged yet, a kickoff template preview
    (literal [Business Name]/[Pain Point] placeholders) is shown instead, never a
    fabricated fictional business.
    """
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    product = db.get(Product, campaign.product_id)

    render_mode = resolve_email_render_mode(campaign)
    format_directive = format_directive_for_mode(render_mode, product.default_format)

    sample_lead = db.query(Lead).filter(Lead.campaign_id == campaign_id).first()
    sample_draft = None
    sample_pain_points = []
    sample_is_kickoff_template = False
    if sample_lead:
        insight = (
            db.query(LeadReviewInsight)
            .filter(LeadReviewInsight.lead_id == sample_lead.id)
            .order_by(LeadReviewInsight.analyzed_at.desc())
            .first()
        )
        pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []
        product_brief = {"title": product.title, "description": product.description,
                         "value_proposition": product.value_proposition}
        lead_profile = {"company_name": sample_lead.company_name,
                        "contact_person_name": sample_lead.contact_person_name,
                        "contact_person_role": sample_lead.contact_person_role}
        content_assets = get_available_assets(db, product.id) or None
        sample_draft = draft_structured_email(
            db, sample_lead.id, product_brief, lead_profile, pain_points,
            content_assets=content_assets,
            tone_directive=campaign.strategy_angle or product.default_tone,
            format_directive=format_directive,
        )
        sample_pain_points = [_pain_point_text(p) for p in pain_points]
    else:
        # No real lead yet -- Step 18.1b kickoff template preview (cached on campaign).
        sample_draft = ensure_kickoff_draft(db, campaign, product)
        sample_is_kickoff_template = sample_draft is not None
        sample_pain_points = ["[Pain Point]"] if sample_draft else []

    return {
        "campaign_id": campaign.id,
        "todo": json.loads(campaign.daily_todo or "[]"),
        # Step 18.1/18.4 -- the strategist's latest not-yet-approved structural proposal, if
        # any (target_segment/lead_count_goal/strategy_angle + why) -- what Approve will
        # actually apply. current_target_segment/current_lead_count_goal are the campaign's
        # REAL, already-in-effect values, shown alongside so the reviewer can see the diff.
        "pending_proposal": json.loads(campaign.pending_strategy_proposal) if campaign.pending_strategy_proposal else None,
        "current_target_segment": json.loads(campaign.target_segment or "{}"),
        "current_lead_count_goal": campaign.lead_count_goal,
        "email_render_mode": render_mode,
        "sample_draft": sample_draft,
        # HTML mode only: real Phase 11 designed preview (preview-only unsubscribe #).
        "sample_draft_html": build_sample_draft_html(render_mode, sample_draft),
        "sample_lead_id": sample_lead.id if sample_lead else None,
        "sample_lead_company": sample_lead.company_name if sample_lead else ("[Business Name]" if sample_is_kickoff_template else None),
        "sample_is_kickoff_template": sample_is_kickoff_template,
        # Phase 18 Step 18.2 follow-up (2026-09-01, user-flagged): this preview is a real,
        # fully-personalized draft for ONE example lead, not a resolved copy of what every
        # lead gets -- the frontend uses these two fields to caption which real values
        # stand in for [Business Name]/[Pain Point] here, so a reviewer understands each
        # real send substitutes THAT lead's own real name/pain point, not this one's.
        "sample_pain_points": sample_pain_points,
        "approved_today": campaign.last_approved_date == _today_ist(),
        "metrics": compute_campaign_metrics(db, campaign_id),
        # Phase 20 Step 20.1 -- today's real journal entry (if generate_campaign_todo has
        # already run today) plus recent prior days, for the AI's Journal UI.
        "journal": _thesis_dict(db.query(CampaignThesis).filter_by(campaign_id=campaign_id, day=_today_ist()).first()),
        "recent_journal": _recent_journal_entries(db, campaign_id),
        # Phase 20 Step 20.3 -- active Execution Watchdog alert, if any.
        "watchdog_alert": json.loads(campaign.watchdog_alert) if campaign.watchdog_alert else None,
    }


def ensure_kickoff_draft(db, campaign: Campaign, product: Product) -> dict | None:
    """Build (or return cached) kickoff template preview for a campaign with no leads.
    Uses literal [Business Name]/[Pain Point] -- never invents a fictional business.
    Tone from pending proposal's strategy_angle if present, else campaign.strategy_angle,
    else product.default_tone. Format follows campaign.email_render_mode."""
    if campaign.kickoff_draft:
        try:
            cached = json.loads(campaign.kickoff_draft)
            if isinstance(cached, dict) and cached.get("body"):
                return cached
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    pending = json.loads(campaign.pending_strategy_proposal) if campaign.pending_strategy_proposal else {}
    tone = (
        (pending.get("strategy_angle") if isinstance(pending, dict) else None)
        or campaign.strategy_angle
        or product.default_tone
    )
    render_mode = resolve_email_render_mode(campaign)
    format_directive = format_directive_for_mode(render_mode, product.default_format)
    product_brief = {
        "title": product.title,
        "description": product.description,
        "value_proposition": product.value_proposition,
    }
    lead_profile = {
        "company_name": "[Business Name]",
        "contact_person_name": None,
        "contact_person_role": None,
    }
    pain_points = ["[Pain Point]"]
    content_assets = get_available_assets(db, product.id) or None
    cross_sell_products = get_cross_sell_products(db, product.id)

    draft = draft_structured_email(
        db, None, product_brief, lead_profile, pain_points,
        content_assets=content_assets,
        cross_sell_products=cross_sell_products,
        tone_directive=tone,
        format_directive=format_directive,
        kickoff_template_preview=True,
    )
    if not draft:
        return None
    campaign.kickoff_draft = json.dumps(draft)
    db.commit()
    return draft


def revise_kickoff_draft(db, campaign_id: str, instruction: str, current_draft: dict | None = None) -> dict:
    """Step 16.5 conversational revision for the kickoff template (no real lead yet).
    Persists the revised draft on campaigns.kickoff_draft and clears same-day approval.
    Free-text that clearly asks for HTML vs plain text flips email_render_mode first."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    product = db.get(Product, campaign.product_id)
    if not product:
        raise ValueError(f"product for campaign {campaign_id} not found")

    requested_mode = detect_render_mode_request(instruction)
    if requested_mode and requested_mode != resolve_email_render_mode(campaign):
        campaign.email_render_mode = requested_mode
        campaign.kickoff_draft = None

    previous_draft_text = None
    if isinstance(current_draft, dict) and current_draft.get("body"):
        subject = str(current_draft.get("subject") or "").strip()
        body = str(current_draft.get("body") or "").strip()
        previous_draft_text = f"Subject: {subject}\n\n{body}" if subject else body

    pending = json.loads(campaign.pending_strategy_proposal) if campaign.pending_strategy_proposal else {}
    tone = (
        (pending.get("strategy_angle") if isinstance(pending, dict) else None)
        or campaign.strategy_angle
        or product.default_tone
    )
    render_mode = resolve_email_render_mode(campaign)
    format_directive = format_directive_for_mode(render_mode, product.default_format)
    product_brief = {
        "title": product.title,
        "description": product.description,
        "value_proposition": product.value_proposition,
    }
    lead_profile = {"company_name": "[Business Name]", "contact_person_name": None, "contact_person_role": None}
    pain_points = ["[Pain Point]"]
    content_assets = get_available_assets(db, product.id) or None
    cross_sell_products = get_cross_sell_products(db, product.id)

    revised = draft_structured_email(
        db, None, product_brief, lead_profile, pain_points,
        content_assets=content_assets,
        cross_sell_products=cross_sell_products,
        tone_directive=tone,
        format_directive=format_directive,
        human_revision_instruction=instruction,
        previous_draft_text=previous_draft_text,
        kickoff_template_preview=True,
    )
    if not revised:
        raise RuntimeError("kickoff draft revision failed")

    suggestion = suggest_draft_improvement(db, None, product_brief, pain_points, revised.get("sections"))
    campaign.kickoff_draft = json.dumps(revised)
    clear_campaign_approval(db, campaign_id)
    db.commit()
    pushback = check_instruction_pushback(db, campaign_id, instruction)
    return {
        "draft": revised,
        "ai_suggestion": suggestion or None,
        "pushback": pushback,
        "email_render_mode": render_mode,
        "sample_draft_html": build_sample_draft_html(render_mode, revised),
    }


def set_campaign_email_render_mode(db, campaign_id: str, mode: str) -> dict:
    """Daily Review chips: set HTML|TEXT, clear kickoff cache so preview regenerates.
    Does not send anything."""
    mode = str(mode or "").strip().upper()
    if mode not in VALID_EMAIL_RENDER_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_EMAIL_RENDER_MODES)}")
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    if resolve_email_render_mode(campaign) != mode:
        campaign.email_render_mode = mode
        campaign.kickoff_draft = None
        clear_campaign_approval(db, campaign_id)
        db.commit()
    return {"campaign_id": campaign_id, "email_render_mode": mode}


def approve_campaign_today(db, campaign_id: str) -> dict:
    """Records human sign-off on today's plan AND, if the strategist left a pending
    structural proposal (targeting/lead-count/angle), applies it onto the campaign's real
    columns now -- Step 18.4, un-deferred 2026-09-02 (built sign-off-only on 2026-09-01,
    reopened once the fuller loop was clarified). generate_campaign_todo() is the only
    writer of pending_strategy_proposal; this is the only reader/clearer of it, so nothing
    a human hasn't actually seen on the review card ever gets applied."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")

    applied = None
    if campaign.pending_strategy_proposal:
        proposal = json.loads(campaign.pending_strategy_proposal)
        if "target_segment" in proposal:
            campaign.target_segment = json.dumps(proposal["target_segment"])
        if "lead_count_goal" in proposal:
            campaign.lead_count_goal = proposal["lead_count_goal"]
        if "strategy_angle" in proposal:
            campaign.strategy_angle = proposal["strategy_angle"]
            # Angle changed -- cached kickoff template was written against the old tone;
            # next no-lead review regenerates fresh.
            campaign.kickoff_draft = None
        if "email_render_mode" in proposal:
            new_mode = proposal["email_render_mode"]
            if resolve_email_render_mode(campaign) != new_mode:
                campaign.email_render_mode = new_mode
                campaign.kickoff_draft = None
        campaign.pending_strategy_proposal = None
        applied = proposal

    today = _today_ist()
    campaign.last_approved_date = today
    db.commit()
    log_agent_event(db, "CAMPAIGN", None, "DAILY_REVIEW_APPROVED", 1.0, "LOW", "EXECUTE",
                    payload={"campaign_id": campaign_id, "date": today, "applied_proposal": applied})
    return {"campaign_id": campaign_id, "approved_today": True, "date": today, "applied_proposal": applied}


def clear_campaign_approval(db, campaign_id: str) -> None:
    """A same-day feedback revision (Step 16.5's revise-draft, reused by the daily review
    card) changes what the human would actually be sending -- a stale 'approved' from
    before that edit would be misleading, so any real content change today clears it.
    Approving again is a fresh, deliberate re-confirmation, same discipline `daily_todo`
    already has for calendar days."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    campaign.last_approved_date = None
    db.commit()
