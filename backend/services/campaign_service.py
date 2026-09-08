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
    CONVERSATIONAL_PUSHBACK_SYSTEM_PROMPT, TODO_ITEM_REVISION_SYSTEM_PROMPT)
from config import Config
from database.models import (
    AgentEvent, Campaign, CampaignThesis, InboundConversation, Lead, LeadReviewInsight, LeadScore, OutreachLog,
    Product, TodoItem, SUCCESSFULLY_SENT_STATUSES)
from services.message_format_service import get_available_assets
from services.outreach.cross_sell import get_cross_sell_products
from services.reporting_service import IST_OFFSET
from services.system_settings import get_bool, AUTONOMOUS_OUTREACH_ENABLED, DISCOVERY_ENABLED

_KB_GAP_LOOKBACK_DAYS = 14
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

# 2026-09-07 -- the two hand-written to-do labels (outside OPERATIONAL_READINESS) that
# represent a real, structural "must act" blocker rather than an ordinary strategic note --
# see generate_campaign_todo()'s use of this alongside operational_readiness's own labels.
_FIXED_BLOCKER_LABELS = {"Discovery off", "Ready to send"}

# Exact labels the AI Manager must use when it raises these cues (so Approve / Campaign-page
# Mark as approved can resolve the matching Inbox card). The AI writes the text; Python
# never invents these to-do rows.
_APPROVE_CAMPAIGN_LABEL = "Approve campaign"
_REVIEW_MESSAGES_LABEL = "Review messages"
# Option B (2026-09-08): QC-rejected email drafts land here for human Approve & send.
_REVIEW_SEND_EMAIL_LABEL = "Review & send email"
_OUTREACH_EMAIL_DRAFT_KIND = "outreach_email_draft"


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
        OutreachLog.lead_id.in_(lead_ids), OutreachLog.status.in_(SUCCESSFULLY_SENT_STATUSES)
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
    (`_run_daily_plan_tick`, `generate_campaign_todo`'s own `_today_ist()`) rather than a
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


def _campaign_operational_readiness(db, campaign, product) -> list[dict]:
    """2026-09-07, user's own real architectural complaint: every real blocker found this
    session (Discovery off, a half-set target, now product.is_active) needed its OWN
    hand-written prompt paragraph before the strategist would ever mention it -- a genuine
    AI Sales Manager reviewing an account wouldn't need a developer to separately teach it
    about each new way things can be silently broken; it would actually check the account's
    real operational state. This is that check, as real code (never inferred by the model
    from scattered raw fields) -- a plain list of {name, ok, detail}. CAMPAIGN_TODO_SYSTEM_
    PROMPT gets ONE general instruction to surface any `ok: false` entry, rather than one
    hardcoded paragraph per gate -- so a FUTURE gate only needs a new entry appended here,
    never another round of prompt surgery.

    Deliberately separate from the existing READY_TO_DISPATCH_COUNT/DISCOVERY_ENABLED
    signals below (proven, carefully worded, left untouched) -- this covers gates NOT
    already handled by those two, starting with the one just found live.

    2026-09-07 follow-up, same user's next real complaint: the first version used `name`
    (a snake_case code identifier, "product_active") as the to-do's actual LABEL -- a
    non-technical human read "PRODUCT_ACTIVE" on their dashboard and had no idea what it
    meant or what to do about it (their own words: "mujhe hi samajh nahi aa raha AI kya
    chahta hai"). `name` stays a stable internal id (still fine for code/logs); `label` is
    now a SEPARATE, plain-English phrase for the human-facing card -- same precedent as the
    hand-written "Discovery off" label elsewhere in this same prompt. `detail` also now
    names the exact real place to act (the Products page), matching "Discovery off"'s own
    "turn it on in Settings" concreteness -- a note that doesn't say WHERE to go is just as
    useless as one with no explanation at all.

    STANDING RULE FOR EVERY FUTURE CHECK ADDED HERE: `label` and `detail` are hand-written
    Python strings, not model output -- AI_MANAGER_PLAIN_LANGUAGE_RULE (cognition/prompts.py)
    governs the LLM's own wording but cannot fix a bad string written directly in this list,
    so the same bar applies by hand: `label` is a short plain-English phrase (never a
    snake_case/technical name -- that's what `name` is for), and `detail` names the real,
    concrete place a human goes to act (a real page/setting name), never just "this is
    misconfigured" with no destination."""
    checks = [{
        "name": "product_active",
        "label": "Product inactive",
        "ok": bool(product.is_active),
        "detail": (
            "Product is active." if product.is_active else
            f'The product this campaign is for, "{product.title}", is turned off on the '
            "Products page -- discovery only ever looks at active products, so this "
            "campaign will never be searched no matter what its own target says. Go to "
            "the Products page and turn it on if you want this campaign to find leads."
        ),
    }]
    return checks


def campaign_blocking_status(db, campaign: Campaign) -> list[dict]:
    """2026-09-07, user's real, sharp correction to the Calendar red-alert feature: "Got it"
    on a to-do dismisses a NOTIFICATION, it does not fix the real problem -- an alert that
    disappears the moment a human acknowledges it, while the campaign is still genuinely
    stuck, is worse than useless, it's actively misleading (their own words: "AI ab tak
    alert dikhayega jab tak wo solve na ho jaye, chahe koi bhi ruka hua ho usme"). The
    to_do_items table's `is_blocker`/PENDING status is a dismissible reminder; this function
    is the opposite -- a LIVE fact, recomputed fresh every call, completely independent of
    whether any TodoItem was ever created, approved, or dismissed for this campaign. The
    Calendar's red alert is driven by THIS, never by to-do state.

    Returns only the CURRENTLY true blockers (already filtered to the ones a human would
    need to act on) as [{label, detail}, ...] -- empty when nothing is actually blocking
    this campaign right now. Folds in the two hand-written signals (Discovery off,
    ready-to-send-but-outreach-off) alongside operational_readiness's own checks, so a
    single call covers every real blocker this campaign could have."""
    product = db.get(Product, campaign.product_id)
    if not product:
        return []
    target = json.loads(campaign.target_segment or "{}")
    target_ready = bool(target.get("industry")) and bool(target.get("location"))

    blockers = [
        {"label": c["label"], "detail": c["detail"]}
        for c in _campaign_operational_readiness(db, campaign, product) if not c["ok"]
    ]

    if target_ready and not get_bool(db, DISCOVERY_ENABLED, default=False):
        blockers.append({
            "label": "Discovery off",
            "detail": "This campaign is fully targeted and ready, but Discovery is switched "
                      "off system-wide, so it will not find any leads until someone turns it "
                      "on in Settings.",
        })

    ready_count = _ready_to_dispatch_count(db, campaign.id)
    if ready_count > 0 and not get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=Config.AUTONOMOUS_OUTREACH_ENABLED):
        blockers.append({
            "label": "Ready to send",
            "detail": f"This campaign has {ready_count} lead{'s' if ready_count != 1 else ''} "
                      "ready to contact, but sending is switched off system-wide -- turn on "
                      "Autonomous Outreach in Settings if you want them to actually go out.",
        })

    return blockers


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
        # 2026-09-07, user-caught real bug: a human's "target multiple business types"
        # instruction produced the literal string "multiple local business types" as
        # `industry` -- the schema only allowed one string, so the model wrote a summary
        # phrase instead of actually naming several. `industry` may now be a real vertical
        # (str) or a list of them -- validated here so a malformed value (empty list, list
        # of non-strings, blank string) never reaches a real Campaign row silently.
        industry = target_segment.get("industry")
        if isinstance(industry, list):
            names = [v.strip() for v in industry if isinstance(v, str) and v.strip()]
            if names:
                target_segment = {**target_segment, "industry": names}
            else:
                target_segment = {k: v for k, v in target_segment.items() if k != "industry"}
        elif isinstance(industry, str) and not industry.strip():
            target_segment = {k: v for k, v in target_segment.items() if k != "industry"}
        # 2026-09-08: location may be one city (str) or several (list) -- same validation
        # posture as industry. Empty / non-string entries dropped; empty list removes the key.
        location = target_segment.get("location")
        if isinstance(location, list):
            places = [v.strip() for v in location if isinstance(v, str) and v.strip()]
            if places:
                target_segment = {**target_segment, "location": places}
            else:
                target_segment = {k: v for k, v in target_segment.items() if k != "location"}
        elif isinstance(location, str) and not location.strip():
            target_segment = {k: v for k, v in target_segment.items() if k != "location"}
        if target_segment:
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


# Phase 21 -- how long a signal-driven regeneration must wait before re-checking the SAME
# campaign again, even if its signal keeps changing. Purely an engineering cost/spam rail
# (never a human-facing switch) -- a burst of replies must not turn into a burst of LLM calls.
_TODO_SIGNAL_COOLDOWN_HOURS = 2


def serialize_todo_item(item: TodoItem) -> dict:
    return {
        "id": item.id,
        "scope": item.scope,
        "campaign_id": item.campaign_id,
        "product_id": item.product_id,
        "lead_id": item.lead_id,
        "label": item.label,
        "text": item.text,
        "proposal": json.loads(item.proposal) if item.proposal else None,
        "confidence": item.confidence,
        "rationale": item.rationale,
        "is_blocker": bool(item.is_blocker),
        "status": item.status,
        "created_at": str(item.created_at),
        "resolved_at": str(item.resolved_at) if item.resolved_at else None,
    }


def create_lead_escalation_todo(
    db, lead: Lead, reason: str, label: str | None = None, draft: dict | None = None,
    followup_level=None,
) -> None:
    """2026-09-07, user's real catch: a dispatch handler that couldn't produce an
    acceptable draft after every real retry (QC rejected an email twice, WhatsApp
    variables failed validation) only ever wrote a HUMAN_ESCALATION `agent_events` row --
    a raw audit-log entry, invisible anywhere in the actual UI, with the lead's own status
    left completely unchanged. Their own words: "system ne bola review ke liye bheja, but
    kuch aya hi nahi todo me, kaise review karu?" It didn't, because nothing was ever
    created for a human to see. This is that missing real, visible to-do.

    Option B (2026-09-08): when a real email `draft` exists, label is "Review & send email"
    and `proposal` stores subject/body so the Inbox can Approve & send (or ask for a
    change). No draft (e.g. WhatsApp var failure) keeps the older "Needs manual outreach"
    hand-write path.

    Keyed on (campaign_id, lead_id, label) for dedup -- unlike the campaign-level
    fixed-label to-dos (Discovery off, Ready to send), MANY different leads in the same
    campaign can each independently need this, so dedup must be per-lead, not per-campaign
    -- a single shared label would silently swallow every lead after the first one.
    Always `is_blocker=True`: a lead waiting on a human send decision is exactly the kind
    of real, standing "must act" state the Calendar's red alert exists for."""
    if not lead.campaign_id:
        return

    has_draft = bool(draft and draft.get("subject") and draft.get("body"))
    if label is None:
        label = _REVIEW_SEND_EMAIL_LABEL if has_draft else "Needs manual outreach"

    # Dedup against both the new label and the legacy hand-write label for the same lead.
    existing = db.query(TodoItem).filter(
        TodoItem.campaign_id == lead.campaign_id, TodoItem.lead_id == lead.id,
        TodoItem.status == "PENDING",
        TodoItem.label.in_([label, _REVIEW_SEND_EMAIL_LABEL, "Needs manual outreach"]),
    ).first()
    if existing:
        # Upgrade a legacy "hand-write" card if we now have a real draft to review.
        if has_draft and (
            not existing.proposal
            or (json.loads(existing.proposal) or {}).get("kind") != _OUTREACH_EMAIL_DRAFT_KIND
        ):
            existing.label = _REVIEW_SEND_EMAIL_LABEL
            existing.text = (
                f'AI wrote an email for "{lead.company_name}" but wasn\'t sure it was '
                "good enough. Read it below — Approve & send if it looks right, or ask "
                f"for a change. ({reason})"
            )
            existing.proposal = json.dumps({
                "kind": _OUTREACH_EMAIL_DRAFT_KIND,
                "subject": draft["subject"],
                "body": draft["body"],
                "sections": draft.get("sections"),
                "subject_candidates": draft.get("subject_candidates"),
                "followup_level": followup_level,
                "qc_note": reason,
            })
            db.commit()
        return

    if has_draft:
        item = TodoItem(
            scope="CAMPAIGN", campaign_id=lead.campaign_id, lead_id=lead.id,
            label=_REVIEW_SEND_EMAIL_LABEL,
            text=(
                f'AI wrote an email for "{lead.company_name}" but wasn\'t sure it was '
                "good enough. Read it below — Approve & send if it looks right, or ask "
                f"for a change. ({reason})"
            ),
            proposal=json.dumps({
                "kind": _OUTREACH_EMAIL_DRAFT_KIND,
                "subject": draft["subject"],
                "body": draft["body"],
                "sections": draft.get("sections"),
                "subject_candidates": draft.get("subject_candidates"),
                "followup_level": followup_level,
                "qc_note": reason,
            }),
            is_blocker=True,
        )
    else:
        item = TodoItem(
            scope="CAMPAIGN", campaign_id=lead.campaign_id, lead_id=lead.id, label=label,
            text=f'"{lead.company_name}" needs a message written by hand -- {reason} '
                 "Open this lead's page to write and send one yourself.",
            is_blocker=True,
        )
    db.add(item)
    db.commit()


def _apply_proposal_to_campaign(campaign: Campaign, proposal: dict) -> None:
    """Shared field-by-field apply logic -- the ONLY place a strategist's proposal actually
    changes a real Campaign row, used by approve_todo_item() for a CAMPAIGN-scope item.
    Never called for a GLOBAL item (those never touch a campaign row -- see
    approve_todo_item's own docstring)."""
    if "target_segment" in proposal:
        campaign.target_segment = json.dumps(proposal["target_segment"])
    if "lead_count_goal" in proposal:
        campaign.lead_count_goal = proposal["lead_count_goal"]
    if "strategy_angle" in proposal:
        campaign.strategy_angle = proposal["strategy_angle"]
        # Angle changed -- cached kickoff template was written against the old tone; next
        # no-lead review regenerates fresh.
        campaign.kickoff_draft = None
    if "email_render_mode" in proposal:
        new_mode = proposal["email_render_mode"]
        if resolve_email_render_mode(campaign) != new_mode:
            campaign.email_render_mode = new_mode
            campaign.kickoff_draft = None


def _pending_proposal_for_campaign(db, campaign_id: str) -> dict | None:
    """Phase 21 -- the campaign's own current PENDING "Proposal" to-do item, if any (at most
    one can exist at a time -- generate_campaign_todo()'s own dedup guarantees that). Replaces
    every old direct read of the now-superseded campaign.pending_strategy_proposal column."""
    item = db.query(TodoItem).filter(
        TodoItem.campaign_id == campaign_id, TodoItem.status == "PENDING", TodoItem.label == "Proposal",
    ).first()
    return json.loads(item.proposal) if item and item.proposal else None


def todo_signal_fingerprint(db, campaign: Campaign) -> dict:
    """Phase 21 -- the lightweight tuple _run_signal_driven_todo_tick() diffs against
    campaign.last_todo_signal to decide "did anything real change since the last time we
    generated a to-do for this campaign". Deliberately cheap (reuses the same
    compute_campaign_metrics() every other surface already calls) -- no new aggregation.

    2026-09-07, user-caught real bug: this used to collapse TARGET_SEGMENT down to one
    coarse `has_target = bool(target_segment)` flag -- the SAME imprecision already fixed in
    generate_campaign_todo()'s own prompt logic, just hiding in this SEPARATE signal-diffing
    function too. A campaign going from "only location set" to "industry+location+lead_count
    all set" (a human approving the AI's own completion proposal) is a real, important
    change -- but `bool(target_segment)` is True both before and after (the dict was never
    empty), so the fingerprint looked unchanged and the mid-day tick silently never re-ran
    for this campaign. Found live: a real campaign's target went from half-set to fully-set
    by human approval, and the "Discovery is off" reminder that should have followed within
    one poll interval never fired -- would have sat silent until tomorrow's daily floor tick.
    Now mirrors the same three explicit ground-truth flags the prompt itself checks, so ANY
    real change to any of them is a real change here too.

    2026-09-07 follow-up: also folds in _campaign_operational_readiness()'s own `ok` values
    (starting with product.is_active) -- a product being switched active later must also
    wake this campaign's mid-day check, not just wait for tomorrow's daily floor."""
    metrics = compute_campaign_metrics(db, campaign.id)
    target = json.loads(campaign.target_segment or "{}")
    product = db.get(Product, campaign.product_id)
    readiness = _campaign_operational_readiness(db, campaign, product) if product else []
    tagged_lead_count = db.query(Lead).filter(Lead.campaign_id == campaign.id).count()
    return {
        **metrics,
        "target_has_industry": bool(target.get("industry")),
        "target_has_location": bool(target.get("location")),
        "lead_count_goal_set": campaign.lead_count_goal is not None,
        "campaign_status": campaign.status,
        # 2026-09-07 -- without this, leads arriving (0→N) while sent stays 0 left the
        # fingerprint unchanged, so signal-driven tick never re-ran the AI Manager same day.
        "tagged_lead_count": tagged_lead_count,
        "operational_readiness": {c["name"]: c["ok"] for c in readiness},
    }


def dismiss_pending_todos_by_label(db, campaign_id: str, label: str) -> int:
    """Resolve PENDING todos with this exact label for one campaign (e.g. after the human
    Marks as approved on the Campaign page, the matching Inbox card should not keep asking)."""
    rows = (
        db.query(TodoItem)
        .filter(
            TodoItem.campaign_id == campaign_id,
            TodoItem.status == "PENDING",
            TodoItem.label == label,
        )
        .all()
    )
    now = datetime.utcnow()
    for item in rows:
        item.status = "APPROVED"
        item.resolved_at = now
    return len(rows)


def generate_campaign_todo(db, campaign_id: str) -> dict:
    """AI Sales Manager's strategy review for one EXISTING (human-made) campaign -- called
    both by the daily floor tick (once per IST day, unconditionally) and the signal-driven
    tick (mid-day, only when something real changed). One strategist reading whatever real
    data exists right now, the same mechanism whether that's nothing yet (a fresh campaign's
    first review) or a real track record. Never creates a campaign.

    Phase 21 (2026-09-05): no longer writes campaign.daily_todo/pending_strategy_proposal --
    every real to-do (including a structural proposal, which becomes one to-do item carrying
    a `proposal` field) is its own addressable `TodoItem` row (scope=CAMPAIGN), inserted here,
    never overwritten. A new item is skipped if an already-PENDING item for this campaign has
    the same label -- the model's own "never fill space with a generic observation" discipline
    means real duplicates are rare; this is just a backstop against the SAME unresolved point
    being re-raised every tick before a human gets to it. Returns
    {"created_items": [...], "journal": {...}|None} -- created_items is only what THIS call
    added, not the campaign's full pending queue (callers needing the whole queue query
    TodoItem directly, e.g. get_daily_review()/GET /todos).

    The journal (campaign_theses upsert) is unrelated to todo_items -- it is the strategist's
    own persistent, dated narrative belief about this campaign, carried across days regardless
    of whether anything today needs human action, and unaffected by this rewrite."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"campaign {campaign_id} not found")
    product = db.get(Product, campaign.product_id)

    metrics = compute_campaign_metrics(db, campaign_id)
    kb_gap_topics = _recent_kb_gap_topics(db, campaign.product_id)
    sibling_campaigns = _sibling_campaign_summaries(db, campaign.product_id, exclude_id=campaign_id)
    ready_to_dispatch_count = _ready_to_dispatch_count(db, campaign_id)
    outreach_enabled = get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=Config.AUTONOMOUS_OUTREACH_ENABLED)
    # 2026-09-07, user-flagged real gap: approving a targeting decision closed no loop back
    # to the human about what's still blocking it from actually finding leads -- the AI has
    # full visibility into DISCOVERY_ENABLED already, it just wasn't being told to use it.
    discovery_enabled = get_bool(db, DISCOVERY_ENABLED, default=False)
    # Step 19.4 -- local import to avoid a module-load cycle (strategy_reflection_service
    # itself imports compute_campaign_metrics from this module), same pattern
    # system_settings.get_all() already uses for its own Config import.
    from services.strategy_reflection_service import get_active_insights_for_product
    strategy_insights = get_active_insights_for_product(db, campaign.product_id)
    today = _today_ist()
    prior_journal = _recent_journal_entries(db, campaign_id)

    target_segment = json.loads(campaign.target_segment or "{}")
    # 2026-09-07, user-flagged real gap: a human who deliberately sets ONLY location (or
    # only industry) and leaves the other for the AI to decide -- a genuinely intended,
    # legitimate use of "optional" -- produced a target_segment dict that IS non-empty, so
    # the model judged it as "already targeted" and never noticed the missing half. Real
    # live campaign found with target_segment={"location": "Mehsana"}: eligible_campaigns_
    # for_discovery() requires BOTH fields and would silently never pick it up, forever,
    # while the model's own "Discovery off" note described it as fully targeted anyway
    # (inferring the missing industry from PRODUCT_BRIEF rather than flagging it). Computed
    # explicitly here (not left for the model to infer from the raw JSON's shape) so the
    # prompt has ground truth instead of guessing completeness from an object's keys.
    target_has_industry = bool(target_segment.get("industry"))
    target_has_location = bool(target_segment.get("location"))
    # 2026-09-07 follow-up, same user ask generalized: "sirf business type add ho, sirf lead
    # numbers add ho, ya kuch add na ho -- AI Manager khud handle kare, approval ke saath" --
    # LEAD_COUNT_GOAL is the third setup field a human may likewise leave for the AI to pick,
    # same ground-truth-flag treatment as the two above (never inferred from whether the
    # column happens to be non-null in some other unrelated code path).
    lead_count_goal_set = campaign.lead_count_goal is not None
    operational_readiness = _campaign_operational_readiness(db, campaign, product)

    prompt = CAMPAIGN_TODO_SYSTEM_PROMPT + f"""
CAMPAIGN_NAME: {json.dumps(campaign.name, ensure_ascii=False)}
CAMPAIGN_STATUS: {json.dumps(campaign.status)}
TARGET_SEGMENT: {json.dumps(target_segment, ensure_ascii=False)}
TARGET_HAS_INDUSTRY: {json.dumps(target_has_industry)}
TARGET_HAS_LOCATION: {json.dumps(target_has_location)}
LEAD_COUNT_GOAL_SET: {json.dumps(lead_count_goal_set)}
LEAD_COUNT_GOAL: {json.dumps(campaign.lead_count_goal)}
TAGGED_LEAD_COUNT: {json.dumps(db.query(Lead).filter(Lead.campaign_id == campaign_id).count())}
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
DISCOVERY_ENABLED: {json.dumps(discovery_enabled)}
OPERATIONAL_READINESS: {json.dumps(operational_readiness, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
    except LLMError as exc:
        log_agent_event(db, "CAMPAIGN", None, "GENERATE_TODO", 0.0, "LOW", "EXECUTE",
                        payload={"campaign_id": campaign_id, "error": str(exc)})
        return {
            "created_items": [],
            "journal": _thesis_dict(db.query(CampaignThesis).filter_by(campaign_id=campaign_id, day=today).first()),
        }

    pending_labels = {
        row[0] for row in db.query(TodoItem.label).filter(
            TodoItem.campaign_id == campaign_id, TodoItem.status == "PENDING",
        ).all()
    }

    # 2026-09-07 -- which labels represent a real, structural "must act" blocker (drives the
    # Calendar's red alert) vs an ordinary strategic note. Computed here in Python from a
    # fixed set of known labels, never left to the model to self-classify: "Discovery off"/
    # "Ready to send" are the two hand-written fixed-label signals above, and every
    # OPERATIONAL_READINESS check's own `label` is blocker-worthy by definition (that's the
    # whole point of that list) regardless of its current `ok` value -- a check that's
    # currently ok just never produces a todo item with that label in the first place.
    blocker_labels = _FIXED_BLOCKER_LABELS | {c["label"] for c in operational_readiness}

    raw_todo = data.get("todo")
    proposal = _clean_proposal(data.get("proposal"))
    created_items = []
    if isinstance(raw_todo, list):
        for raw_item in raw_todo:
            if not isinstance(raw_item, dict):
                continue
            label = str(raw_item.get("label", "")).strip()[:30] or "Note"
            text = str(raw_item.get("text", "")).strip()[:250]
            if not text or label in pending_labels:
                continue
            item = TodoItem(
                scope="CAMPAIGN", campaign_id=campaign_id, label=label, text=text,
                is_blocker=label in blocker_labels,
            )
            db.add(item)
            created_items.append(item)
            pending_labels.add(label)  # this same call never raises the same label twice either

    # A structural proposal becomes its OWN to-do item -- `proposal` field carries the JSON,
    # `text` carries the human-readable rationale, so it renders through the exact same
    # per-item card as every other to-do (no separate "pending_proposal" concept anymore).
    if proposal and "Proposal" not in pending_labels:
        proposal_item = TodoItem(
            scope="CAMPAIGN", campaign_id=campaign_id, label="Proposal",
            text=proposal.get("rationale") or "The AI has a structural change to propose for this campaign.",
            proposal=json.dumps(proposal), confidence=proposal.get("confidence"),
            rationale=proposal.get("rationale"),
        )
        db.add(proposal_item)
        created_items.append(proposal_item)

    journal = _clean_journal(data.get("journal"))
    if journal:
        thesis = db.query(CampaignThesis).filter_by(campaign_id=campaign_id, day=today).first()
        if thesis:
            thesis.hypothesis = journal["hypothesis"]
            thesis.observation = journal["observation"]
            thesis.pivot_decision = journal["pivot_decision"]
        else:
            db.add(CampaignThesis(campaign_id=campaign_id, day=today, **journal))

    campaign.last_todo_signal = json.dumps(todo_signal_fingerprint(db, campaign))
    db.commit()
    # expire_on_commit=False (db_config.py) means a freshly-added row's server_default
    # columns (created_at) stay None on the Python side after commit unless refreshed --
    # only matters for this call's own return value, the persisted row is correct either way.
    for item in created_items:
        db.refresh(item)
    log_agent_event(db, "CAMPAIGN", None, "GENERATE_TODO", 1.0, "LOW", "EXECUTE",
                    payload={"campaign_id": campaign_id, "items_created": len(created_items),
                             "has_proposal": bool(proposal), "has_journal": bool(journal)})
    return {
        "created_items": [serialize_todo_item(i) for i in created_items],
        "journal": {"day": today, **journal} if journal else None,
    }


def generate_campaign_suggestion(db, product_id: str) -> dict | None:
    """Notices, from real data, when a product looks worth a fresh campaign push -- never
    creates a campaign. Returns {"suggestion": str, "target_segment": dict|None,
    "lead_count_goal": int|None}, or None if nothing concrete stood out.

    Phase 21 (2026-09-05): when the model returns a real suggestion, this now inserts a
    GLOBAL-scope `TodoItem` (product_id=product_id, no campaign_id) -- the free-for-all half
    of the unified inbox ("this product's leads are trending strong in industry X, worth a
    new campaign"), alongside the existing CAMPAIGN-scope items. Skips inserting if a PENDING
    GLOBAL item already exists for this product (a human hasn't acted on the last one yet --
    no point repeating it every tick). Still also logs the CAMPAIGN_SUGGESTED agent_event
    (existing table, unchanged) purely for the audit trail; nothing downstream reads it as a
    source of truth anymore -- get_live_campaign_suggestions() (the last consumer of that
    event-derived view) is removed entirely by Phase 21 in favor of querying TodoItem directly
    (GET /api/v1/todos, api/todos.py)."""
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

    already_pending = db.query(TodoItem).filter(
        TodoItem.product_id == product_id, TodoItem.scope == "GLOBAL", TodoItem.status == "PENDING",
    ).first()
    if not already_pending:
        db.add(TodoItem(
            scope="GLOBAL", product_id=product_id, label="New campaign idea", text=suggestion,
            proposal=json.dumps({k: v for k, v in cleaned.items() if k != "rationale"}) if cleaned else None,
            rationale=suggestion,
        ))
        db.commit()
    return result


def build_sample_whatsapp_preview(db, product, sample_lead, pain_points: list) -> dict | None:
    """What the first WhatsApp touch would look like for this campaign's sample lead —
    same selection path as jobs/outreach_wa_handler.py's first-touch branch (product-
    scoped APPROVED template, else TEMPLATE_LIBRARY). Read-only preview for Daily Review;
    never sends, never invents Meta-unapproved copy."""
    from services.outreach.whatsapp_template_service import get_approved_first_touch_template
    from services.outreach.whatsapp_templates import (
        TEMPLATE_LIBRARY, select_template, fill_variables, fill_variables_for_labels,
        interpolate_template,
    )

    if sample_lead:
        lead_profile = {
            "company_name": sample_lead.company_name,
            "contact_person_name": sample_lead.contact_person_name,
        }
        company_label = sample_lead.company_name
    else:
        lead_profile = {
            "company_name": "[Business Name]",
            "contact_person_name": "[Contact Name]",
        }
        # Library pain filler expects dicts with evidence_quote when using fill_variables
        pain_points = [{"evidence_quote": "[Pain Point]"}]
        company_label = "[Business Name]"

    product_id = product.id if product else None
    first_touch = get_approved_first_touch_template(db, product_id=product_id)
    if first_touch:
        body_text = first_touch.body_text or ""
        labels = json.loads(first_touch.variable_labels or "[]")
        values = fill_variables_for_labels(labels, lead_profile, pain_points or [])
        return {
            "template_name": first_touch.name,
            "purpose": "FIRST_TOUCH",
            "source": "product" if first_touch.product_id else "shared",
            "body": interpolate_template(body_text, values),
            "body_template": body_text,
            "filled_for": company_label,
            "manage_hint": "This is the approved WhatsApp first-touch template that real sends use. "
                           "To change wording, go to WhatsApp Templates — Meta must re-approve edits.",
        }

    key = select_template(pain_points or [])
    spec = TEMPLATE_LIBRARY[key]
    values = fill_variables(key, lead_profile, pain_points or [])
    return {
        "template_name": spec["name"],
        "purpose": "FIRST_TOUCH",
        "source": "library",
        "body": interpolate_template(spec.get("body_text") or "", values),
        "body_template": spec.get("body_text") or "",
        "filled_for": company_label,
        "manage_hint": "Using the shared WhatsApp library template. Add a product-specific "
                       "approved template under WhatsApp Templates if you want a custom first touch.",
    }


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
    raw_pain_points = []
    if sample_lead:
        insight = (
            db.query(LeadReviewInsight)
            .filter(LeadReviewInsight.lead_id == sample_lead.id)
            .order_by(LeadReviewInsight.analyzed_at.desc())
            .first()
        )
        raw_pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []
        product_brief = {"title": product.title, "description": product.description,
                         "value_proposition": product.value_proposition}
        lead_profile = {"company_name": sample_lead.company_name,
                        "contact_person_name": sample_lead.contact_person_name,
                        "contact_person_role": sample_lead.contact_person_role}
        content_assets = get_available_assets(db, product.id) or None
        sample_draft = draft_structured_email(
            db, sample_lead.id, product_brief, lead_profile, raw_pain_points,
            content_assets=content_assets,
            tone_directive=campaign.strategy_angle or product.default_tone,
            format_directive=format_directive,
        )
        sample_pain_points = [_pain_point_text(p) for p in raw_pain_points]
    else:
        # No real lead yet -- Step 18.1b kickoff template preview (cached on campaign).
        sample_draft = ensure_kickoff_draft(db, campaign, product)
        sample_is_kickoff_template = sample_draft is not None
        sample_pain_points = ["[Pain Point]"] if sample_draft else []

    sample_whatsapp = build_sample_whatsapp_preview(db, product, sample_lead, raw_pain_points)

    # Phase 21 -- this campaign's own real, individually-addressable to-do queue, newest
    # first. Replaces `todo`/`pending_proposal`/`approved_today` entirely: a structural
    # proposal is just the one item in this list that happens to carry a `proposal` field,
    # and there is no more single whole-day approval flag -- each item has its own status.
    todo_items = (
        db.query(TodoItem)
        .filter(TodoItem.campaign_id == campaign_id, TodoItem.status == "PENDING")
        .order_by(TodoItem.created_at.desc())
        .all()
    )

    return {
        "campaign_id": campaign.id,
        "todo_items": [serialize_todo_item(i) for i in todo_items],
        "current_target_segment": json.loads(campaign.target_segment or "{}"),
        "current_lead_count_goal": campaign.lead_count_goal,
        "email_render_mode": render_mode,
        "sample_draft": sample_draft,
        # HTML mode only: real Phase 11 designed preview (preview-only unsubscribe #).
        "sample_draft_html": build_sample_draft_html(render_mode, sample_draft),
        # First-touch WhatsApp preview (same template selection as a real WA send).
        "sample_whatsapp": sample_whatsapp,
        "sample_lead_id": sample_lead.id if sample_lead else None,
        "sample_lead_company": sample_lead.company_name if sample_lead else ("[Business Name]" if sample_is_kickoff_template else None),
        "sample_is_kickoff_template": sample_is_kickoff_template,
        # Phase 18 Step 18.2 follow-up (2026-09-01, user-flagged): this preview is a real,
        # fully-personalized draft for ONE example lead, not a resolved copy of what every
        # lead gets -- the frontend uses these two fields to caption which real values
        # stand in for [Business Name]/[Pain Point] here, so a reviewer understands each
        # real send substitutes THAT lead's own real name/pain point, not this one's.
        "sample_pain_points": sample_pain_points,
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

    pending = _pending_proposal_for_campaign(db, campaign.id)
    tone = (pending or {}).get("strategy_angle") or campaign.strategy_angle or product.default_tone
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
    Persists the revised draft on campaigns.kickoff_draft. Free-text that clearly asks for
    HTML vs plain text flips email_render_mode first."""
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

    pending = _pending_proposal_for_campaign(db, campaign.id)
    tone = (pending or {}).get("strategy_angle") or campaign.strategy_angle or product.default_tone
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
        db.commit()
    return {"campaign_id": campaign_id, "email_render_mode": mode}


def revise_todo_item(db, todo_id: str, instruction: str) -> dict:
    """Phase 21 -- per-item conversational feedback, the SAME lightweight "current state +
    one new instruction" pattern already proven for drafts (Step 16.5) and the kickoff
    template (Step 18.1b) -- never a stored multi-turn transcript, the caller's own resent
    `text`/`proposal` IS the memory. Re-grounds the revision in the same real data the item
    was originally generated from (a campaign's metrics/insights for CAMPAIGN scope, sibling
    campaigns for GLOBAL) so the model can't drift from what's actually true. Runs
    check_instruction_pushback for CAMPAIGN-scope items only (it needs a real campaign_id to
    check against) -- a GLOBAL item has no existing campaign yet to compare data against.

    Option B (2026-09-08): items with proposal.kind=outreach_email_draft revise the stored
    email (subject/body/sections) via the same draft_structured_email path Daily Review
    uses -- not the campaign-proposal revision prompt."""
    item = db.get(TodoItem, todo_id)
    if not item:
        raise ValueError(f"todo item {todo_id} not found")
    if item.status != "PENDING":
        raise ValueError(f"todo item {todo_id} is already {item.status}, no longer editable")

    proposal = json.loads(item.proposal) if item.proposal else None
    if (
        item.scope == "CAMPAIGN"
        and isinstance(proposal, dict)
        and proposal.get("kind") == _OUTREACH_EMAIL_DRAFT_KIND
        and item.lead_id
    ):
        return _revise_outreach_email_todo(db, item, proposal, instruction)

    if item.scope == "CAMPAIGN":
        campaign = db.get(Campaign, item.campaign_id)
        real_data = {
            "metrics": compute_campaign_metrics(db, item.campaign_id),
            "strategy_angle": campaign.strategy_angle if campaign else None,
        } if campaign else {}
    else:
        product = db.get(Product, item.product_id) if item.product_id else None
        real_data = {
            "sibling_campaigns": _sibling_campaign_summaries(db, item.product_id, exclude_id="")
        } if product else {}

    prompt = TODO_ITEM_REVISION_SYSTEM_PROMPT + f"""
TODO_LABEL: {json.dumps(item.label, ensure_ascii=False)}
TODO_TEXT: {json.dumps(item.text, ensure_ascii=False)}
TODO_PROPOSAL: {item.proposal or "null"}
REAL_DATA: {json.dumps(real_data, ensure_ascii=False)}
HUMAN_INSTRUCTION: {json.dumps(instruction, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.3)
    except LLMError as exc:
        raise RuntimeError(f"to-do revision failed: {exc}") from exc

    new_text = str(data.get("text", "")).strip()[:250] or item.text
    new_proposal = _clean_proposal(data.get("proposal")) if data.get("proposal") else None

    item.text = new_text
    item.proposal = json.dumps(new_proposal) if new_proposal else item.proposal
    if new_proposal and new_proposal.get("confidence") is not None:
        item.confidence = new_proposal["confidence"]
    db.commit()

    pushback = check_instruction_pushback(db, item.campaign_id, instruction) if item.scope == "CAMPAIGN" else None
    return {"item": serialize_todo_item(item), "pushback": pushback}


def _revise_outreach_email_todo(db, item: TodoItem, proposal: dict, instruction: str) -> dict:
    """Rewrite the stored QC-escalation email draft from human feedback; keep Inbox card PENDING."""
    from services.outreach.pain_points import confident_pain_points

    lead = db.get(Lead, item.lead_id)
    if not lead:
        raise ValueError(f"lead {item.lead_id} not found for todo {item.id}")
    product = db.get(Product, lead.product_id)
    if not product:
        raise ValueError(f"product {lead.product_id} not found")

    campaign = db.get(Campaign, lead.campaign_id) if lead.campaign_id else None
    tone_directive = (campaign.strategy_angle if campaign and campaign.strategy_angle else None) \
        or product.default_tone
    render_mode = resolve_email_render_mode(campaign) if campaign else "HTML"
    format_directive = format_directive_for_mode(render_mode, product.default_format)

    insight = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.lead_id == lead.id)
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []
    pain_points = confident_pain_points(pain_points)
    product_brief = {
        "title": product.title,
        "description": product.description,
        "value_proposition": product.value_proposition,
    }
    lead_profile = {
        "company_name": lead.company_name,
        "contact_person_name": lead.contact_person_name,
        "contact_person_role": lead.contact_person_role,
    }
    previous_draft_text = f"Subject: {proposal.get('subject', '')}\n\n{proposal.get('body', '')}"

    revised = draft_structured_email(
        db, lead.id, product_brief, lead_profile, pain_points,
        content_assets=get_available_assets(db, lead.product_id) or None,
        cross_sell_products=get_cross_sell_products(db, lead.product_id),
        tone_directive=tone_directive,
        format_directive=format_directive,
        human_revision_instruction=instruction,
        previous_draft_text=previous_draft_text,
    )
    if not revised:
        raise RuntimeError("email rewrite failed -- try again or rephrase the instruction")

    proposal = {
        **proposal,
        "kind": _OUTREACH_EMAIL_DRAFT_KIND,
        "subject": revised["subject"],
        "body": revised["body"],
        "sections": revised.get("sections"),
        "subject_candidates": revised.get("subject_candidates", proposal.get("subject_candidates")),
    }
    item.proposal = json.dumps(proposal)
    item.text = (
        f'Updated email for "{lead.company_name}" from your note. '
        "Read it below — Approve & send if it looks right, or ask for another change."
    )
    db.commit()
    pushback = check_instruction_pushback(db, item.campaign_id, instruction) if item.campaign_id else None
    return {"item": serialize_todo_item(item), "pushback": pushback}


def approve_todo_item(db, todo_id: str) -> dict:
    """Phase 21 -- the ONLY way a to-do's `proposal` ever reaches a real Campaign row
    (CAMPAIGN scope) -- a per-item decision, never a whole-day bulk action. GLOBAL scope
    never touches a campaign row at all: a campaign is always human-created (Phase 17's own
    invariant), so approving a "new campaign idea" only hands the frontend a pre-fill
    payload for the existing CampaignFormModal -- the exact same shape/flow
    CampaignCalendar's own "Create this campaign" button already used.

    Option B (2026-09-08): proposal.kind=outreach_email_draft sends that email via the
    shared dispatch path, then resolves the to-do -- never applies campaign structural fields."""
    item = db.get(TodoItem, todo_id)
    if not item:
        raise ValueError(f"todo item {todo_id} not found")
    if item.status != "PENDING":
        raise ValueError(f"todo item {todo_id} is already {item.status}")

    proposal = json.loads(item.proposal) if item.proposal else None
    applied = None
    campaign_prefill = None

    if (
        item.scope == "CAMPAIGN"
        and isinstance(proposal, dict)
        and proposal.get("kind") == _OUTREACH_EMAIL_DRAFT_KIND
    ):
        lead = db.get(Lead, item.lead_id) if item.lead_id else None
        if not lead:
            raise ValueError(f"todo {todo_id} has no lead to send to")
        if not proposal.get("subject") or not proposal.get("body"):
            raise ValueError("this review card has no email to send")
        # Local import: jobs.outreach_handler imports create_lead_escalation_todo from here.
        from jobs.outreach_handler import dispatch_structured_email
        try:
            sent = dispatch_structured_email(
                db, lead,
                {
                    "subject": proposal["subject"],
                    "body": proposal["body"],
                    "sections": proposal.get("sections"),
                    "subject_candidates": proposal.get("subject_candidates")
                        or [proposal["subject"]],
                },
                followup_level=proposal.get("followup_level"),
                qc_confidence=1.0,
            )
        except Exception as exc:
            raise RuntimeError(f"send failed: {exc}") from exc
        applied = {
            "sent_email": True,
            "to": sent["to"],
            "subject": sent["subject"],
            "company_name": sent["company_name"],
        }
    elif item.scope == "CAMPAIGN" and item.label == _APPROVE_CAMPAIGN_LABEL:
        # Dashboard Inbox Approve on this standing cue IS the formal campaign OK -- same
        # outcome as Campaign Detail's "Mark as approved" button.
        campaign = db.get(Campaign, item.campaign_id)
        if campaign and campaign.status == "PROPOSED":
            campaign.status = "APPROVED"
            applied = {"status": "APPROVED"}
    elif item.scope == "CAMPAIGN" and proposal:
        campaign = db.get(Campaign, item.campaign_id)
        if campaign:
            _apply_proposal_to_campaign(campaign, proposal)
            applied = proposal
    elif item.scope == "GLOBAL" and proposal:
        campaign_prefill = {**proposal, "product_id": item.product_id}

    item.status = "APPROVED"
    item.resolved_at = datetime.utcnow()
    db.commit()
    log_agent_event(db, "CAMPAIGN", None, "TODO_ITEM_APPROVED", 1.0, "LOW", "EXECUTE",
                    payload={"todo_id": todo_id, "scope": item.scope, "applied_proposal": applied})
    return {"item": serialize_todo_item(item), "applied": applied, "campaign_prefill": campaign_prefill}


def dismiss_todo_item(db, todo_id: str) -> dict:
    """Resolves a to-do with no change applied -- the human looked at it and decided against
    acting, as valid an outcome as approving."""
    item = db.get(TodoItem, todo_id)
    if not item:
        raise ValueError(f"todo item {todo_id} not found")
    if item.status != "PENDING":
        raise ValueError(f"todo item {todo_id} is already {item.status}")
    item.status = "DISMISSED"
    item.resolved_at = datetime.utcnow()
    db.commit()
    return {"item": serialize_todo_item(item)}
