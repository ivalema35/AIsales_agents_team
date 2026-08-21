"""Phase 9 Step 9.5 -- admin submits a real WhatsApp template from the CRM (real Meta
Create Template API call), mirrors its real Meta-side approval state locally, and a
poll updates that state + activates approved templates without a code edit.

Real endpoint shape (Meta's own WhatsApp Business Management API, mirrored 1:1 by this
project's BSP -- confirmed in services/outreach/whatsapp_service.py's own docstring,
same base URL/version/auth as every other real WhatsApp call in this codebase):
  Create: POST {base}/{version}/{waba_id}/message_templates
  Status: GET  {base}/{version}/{waba_id}/message_templates?name=<name>
"""
from __future__ import annotations
import json
import logging

import requests

from config import Config
from database.models import WhatsappTemplate, LeadReviewInsight
from services.outreach.whatsapp_templates import TEMPLATE_LIBRARY

logger = logging.getLogger(__name__)

# Step 9.6 sub-step 4 -- how confident the real data needs to be before proposing
# anything. A template with only a handful of sends is noise, not a real signal; "less
# than 10% replies" is a deliberately low bar (real reply rates vary a lot) so this only
# fires on a genuinely poor performer, not routine variance.
MIN_SAMPLE_FOR_SIGNAL = 20
LOW_REPLY_RATE_THRESHOLD = 0.10


def _templates_url():
    return f"{Config.WHATSAPP_API_BASE_URL}/{Config.WHATSAPP_API_VERSION}/{Config.WHATSAPP_WABA_ID}/message_templates"


def _find_by_name(data, name):
    """The BSP's own `?name=` filter is unreliable -- confirmed live (2026-08-21): a GET
    with `params={"name": "marketing_gen"}` returned the WABA's full ~20-template list,
    completely ignoring the filter, with an unrelated template first in the array. Taking
    `data["data"][0]` blindly (the original Step 9.5 code) could silently assign a
    DIFFERENT template's real status/wording to the one actually being polled. Always
    filter the response client-side instead of trusting the request-side filter.
    """
    for row in (data.get("data") or []):
        if row.get("name") == name:
            return row
    return None


def _create_on_meta(name, language, category, body_text):
    """The actual real Meta Create Template API call, shared by every path that ends in
    a real submission (a direct admin submit, or an admin approving an AI draft --
    Step 9.6). Raises on failure -- same contract as every other real send in this
    codebase (email_service.send_email, whatsapp_service.send_template_message); the
    caller decides how to surface that. Returns Meta's raw response dict.
    """
    if not Config.WHATSAPP_TOKEN:
        raise RuntimeError("WHATSAPP_TOKEN not configured")
    if not Config.WHATSAPP_WABA_ID:
        raise RuntimeError("WHATSAPP_WABA_ID not configured")

    payload = {
        "name": name,
        "language": language,
        "category": category,
        "components": [{"type": "BODY", "text": body_text}],
    }
    resp = requests.post(
        _templates_url(),
        headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def submit_template(db, name, language, category, purpose, body_text, variable_labels, product_id=None):
    """Real Meta Create Template API call, for a template an admin is submitting
    directly from the dashboard form -- creates the row AND submits it to Meta in one
    step, exactly like before Step 9.6. Stores the new row as PENDING with Meta's own
    returned template id, never guesses an approval state.

    product_id is optional (tracker.md Step 9.5 follow-up) -- None keeps the template
    shared/usable by every product (today's default, and the only option before this),
    set means only that one product may use it. Deliberately optional rather than
    mandatory: a new product-specific template still needs its own separate Meta
    approval, so defaulting to shared keeps that real cost down.
    """
    data = _create_on_meta(name, language, category, body_text)

    row = WhatsappTemplate(
        name=name,
        language=language,
        category=category,
        purpose=purpose,
        body_text=body_text,
        variable_labels=json.dumps(variable_labels),
        status="PENDING",
        meta_template_id=data.get("id"),
        product_id=product_id,
        origin="ADMIN",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("whatsapp template '%s' submitted to Meta, id=%s, status=PENDING", name, data.get("id"))
    return row


def create_draft_template(db, name, language, category, purpose, body_text, variable_labels,
                          product_id=None, reasoning=None):
    """Step 9.6 -- an AI-authored candidate template, stored as DRAFT. Deliberately makes
    NO real Meta call: nothing an AI writes reaches Meta (or a real business) without an
    explicit admin approve action first (approve_draft_and_submit below). `reasoning` is
    the drafting agent's own explanation of why this candidate addresses the real signal
    it was given -- shown to the admin so an approve/reject decision is informed, not blind.
    """
    row = WhatsappTemplate(
        name=name,
        language=language,
        category=category,
        purpose=purpose,
        body_text=body_text,
        variable_labels=json.dumps(variable_labels),
        status="DRAFT",
        product_id=product_id,
        origin="AI",
        reasoning=reasoning,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("whatsapp template '%s' drafted by AI, awaiting admin review", name)
    return row


def approve_draft_and_submit(db, template):
    """An admin approved a DRAFT (Step 9.6) -- NOW, and only now, the real Meta Create
    Template API call happens. Raises on failure, same contract as submit_template();
    the row stays DRAFT if the real call fails, so a failed submission is retryable
    rather than silently lost.
    """
    if template.status != "DRAFT":
        raise ValueError(f"template {template.name!r} is not a DRAFT (status={template.status!r})")

    data = _create_on_meta(template.name, template.language, template.category, template.body_text)
    template.status = "PENDING"
    template.meta_template_id = data.get("id")
    db.commit()
    db.refresh(template)
    logger.info("AI-drafted template '%s' approved by admin, submitted to Meta, id=%s",
                template.name, data.get("id"))
    return template


def reject_draft(db, template):
    """An admin rejected a DRAFT (Step 9.6) -- terminal, no Meta call ever made. Distinct
    from Meta's own REJECTED (a real submission Meta itself declined)."""
    if template.status != "DRAFT":
        raise ValueError(f"template {template.name!r} is not a DRAFT (status={template.status!r})")

    template.status = "ADMIN_REJECTED"
    db.commit()
    db.refresh(template)
    logger.info("AI-drafted template '%s' rejected by admin, never reached Meta", template.name)
    return template


def poll_template_status(db, template):
    """Real Meta GET call for this ONE template's current approval state. Only writes
    back a state Meta actually returned -- never infers PENDING->APPROVED on its own.
    Returns True if the local row's status changed, False otherwise (including on a
    real API failure, which is logged and swallowed -- one template's lookup failing
    must not break a bulk poll of the rest, see poll_all_pending below).
    """
    if not Config.WHATSAPP_TOKEN or not Config.WHATSAPP_WABA_ID:
        return False
    try:
        resp = requests.get(
            _templates_url(),
            headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}"},
            params={"name": template.name},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - one template's poll failing must not break the batch
        logger.warning("whatsapp template poll failed for '%s': %s", template.name, exc)
        return False

    match = _find_by_name(data, template.name)
    if not match:
        return False
    real_status = match.get("status")
    if not real_status or real_status == template.status:
        return False

    template.status = real_status
    if real_status == "REJECTED":
        template.rejection_reason = match.get("rejected_reason") or match.get("reason")
    db.commit()
    logger.info("whatsapp template '%s' status updated: %s", template.name, real_status)
    return True


def fetch_template_wording(name):
    """Real, read-only Meta GET call for one template's full definition, including its
    actual approved BODY text -- unlike poll_template_status() this doesn't write
    anything back, it's purely for display (tracker.md Step 9.5 follow-up: TEMPLATE_
    LIBRARY's 2 built-in templates never had their wording stored in this codebase, so
    there was no way to show an admin what they actually say). Returns None on any
    failure -- display-only, must never block the page it's shown on.
    """
    if not Config.WHATSAPP_TOKEN or not Config.WHATSAPP_WABA_ID:
        return None
    try:
        resp = requests.get(
            _templates_url(),
            headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}"},
            params={"name": name},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - display-only, one failed lookup must not break the page
        logger.warning("whatsapp template wording fetch failed for '%s': %s", name, exc)
        return None

    match = _find_by_name(data, name)
    if not match:
        return None
    components = match.get("components") or []
    body = next((c for c in components if c.get("type") == "BODY"), None)
    return {
        "body_text": body.get("text") if body else None,
        "real_status": match.get("status"),
    }


def poll_all_pending(db):
    """Called from jobs/discovery_scheduler.py's own tick loop. Returns how many
    templates actually changed status this run."""
    pending = db.query(WhatsappTemplate).filter(WhatsappTemplate.status == "PENDING").all()
    changed = 0
    for template in pending:
        if poll_template_status(db, template):
            changed += 1
    return changed


def get_approved_followup_template(db, product_id=None):
    """The real gap Step 9.3 found live: a WhatsApp follow-up had no choice but to
    resend the exact same first-touch template word for word. Returns the best
    approved, active FOLLOW_UP template, or None if none exists yet -- callers fall
    back to today's behavior (reusing the first-touch template) when this is None,
    never a hard failure.

    Tiered: a template scoped to THIS product wins over a shared one, so a product with
    a genuinely distinct pitch can override the shared default without disabling it for
    everyone else. is_active is a manual kill-switch independent of Meta's own APPROVED
    status -- a disabled template is never selected even if Meta still shows it approved.
    """
    base = db.query(WhatsappTemplate).filter(
        WhatsappTemplate.purpose == "FOLLOW_UP",
        WhatsappTemplate.status == "APPROVED",
        WhatsappTemplate.is_active == 1,
    )
    if product_id:
        product_specific = (
            base.filter(WhatsappTemplate.product_id == product_id)
            .order_by(WhatsappTemplate.updated_at.desc())
            .first()
        )
        if product_specific:
            return product_specific
    return (
        base.filter(WhatsappTemplate.product_id.is_(None))
        .order_by(WhatsappTemplate.updated_at.desc())
        .first()
    )


def find_template_improvement_reason(db, purpose=None):
    """Step 9.6 sub-step 4 -- real signal detection for the manual "ask AI to draft a
    template" trigger. Never fabricates a need: returns (reason, context, purpose) only
    when a real, data-backed gap exists, or None otherwise -- an admin pressing the
    button on a healthy system should get an honest "nothing to propose", not a forced
    draft.

    `purpose` (Step 9.6 follow-up, 2026-08-21) -- optional, "FIRST_TOUCH" or "FOLLOW_UP".
    The admin picks which one they want a template for; this scopes the SEARCH for a
    real signal to that purpose (never forces a fabricated one) -- an honest "nothing to
    propose for FIRST_TOUCH right now" is a completely valid, expected outcome if every
    real FIRST_TOUCH template is already performing fine.

    Checks two real gaps, in order:
    1. An existing WhatsApp template (of the requested purpose, if one was given) with a
       real, statistically meaningful reply rate below LOW_REPLY_RATE_THRESHOLD (Step
       9.2's own performance rollup -- the exact real data this step was built to use).
    2. If nothing is underperforming AND purpose isn't "FIRST_TOUCH" (TEMPLATE_LIBRARY's
       GENERIC entry is always a real, available FIRST_TOUCH fallback, so that gap can
       never genuinely exist), whether NO approved FOLLOW_UP template exists at all yet
       -- the real gap Step 9.3 found live (GameZone Visnagar's follow-up being
       byte-identical to its first touch).
    """
    from services.analytics_service import get_variant_performance

    perf = get_variant_performance(db)
    whatsapp_variants = [
        v for v in perf["variants"]
        if v["channel"] == "WHATSAPP" and v["sent"] >= MIN_SAMPLE_FOR_SIGNAL and v["reply_rate"] is not None
    ]
    # Each variant's OWN real purpose -- checked, never assumed. A real bug here (found
    # live, 2026-08-21) always proposed FOLLOW_UP regardless of which template actually
    # underperformed, so a weak FIRST_TOUCH template could never trigger a FIRST_TOUCH
    # candidate. Variants whose purpose can't be honestly determined (matches neither a
    # DB row nor TEMPLATE_LIBRARY) are dropped rather than guessed at.
    candidates = []
    for v in whatsapp_variants:
        existing_row = db.query(WhatsappTemplate).filter(WhatsappTemplate.name == v["variant_id"]).first()
        real_purpose = existing_row.purpose if existing_row else None
        if not real_purpose:
            real_purpose = next(
                ("FIRST_TOUCH" for spec in TEMPLATE_LIBRARY.values() if spec["name"] == v["variant_id"]),
                None,
            )
        if real_purpose and (purpose is None or real_purpose == purpose):
            candidates.append((v, real_purpose, existing_row))

    if candidates:
        worst, real_purpose, existing_row = min(candidates, key=lambda c: c[0]["reply_rate"])
        if worst["reply_rate"] < LOW_REPLY_RATE_THRESHOLD:
            reason = (
                f"The existing WhatsApp template '{worst['variant_id']}' (purpose="
                f"{real_purpose}) has a real {worst['reply_rate'] * 100:.1f}% reply rate "
                f"over {worst['sent']} real sends (all-time) -- below a healthy baseline. "
                f"Propose a genuinely different angle for the SAME purpose."
            )
            context = {"variant_id": worst["variant_id"], "sent": worst["sent"],
                       "replied": worst["replied"], "reply_rate": worst["reply_rate"]}
            product_id = existing_row.product_id if existing_row else None
            return reason, context, real_purpose, product_id

    # TEMPLATE_LIBRARY's GENERIC entry is always a real, available FIRST_TOUCH fallback
    # (select_template() falls back to it unconditionally) -- a "no FIRST_TOUCH template"
    # gap can never genuinely exist, so this check only ever applies to FOLLOW_UP.
    if purpose != "FIRST_TOUCH" and get_approved_followup_template(db) is None:
        reason = ("No approved FOLLOW_UP WhatsApp template exists yet -- every follow-up "
                  "touch currently has to resend the first-touch template verbatim.")
        # This gap has no real performance numbers behind it (unlike the underperformer
        # branch above), which left the drafting agent writing in the dark and producing
        # vague, generic candidates that QC correctly rejected (found live, 2026-08-21).
        # A real sample pain point gives it something concrete to write a specific,
        # non-generic template around -- never fabricated, sourced from a real lead.
        sample_pain_point = _sample_real_pain_point(db)
        context = {"sample_pain_point": sample_pain_point} if sample_pain_point else {}
        return reason, context, "FOLLOW_UP", None

    return None


def _sample_real_pain_point(db):
    """One real, verified pain point from actual lead data (most recently analyzed),
    used only to ground the coverage-gap signal's context in something concrete. Never
    invented -- returns None on a genuinely fresh install with no real lead data yet,
    in which case the drafting agent gets no example and may reasonably decline."""
    row = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.pain_points_extracted.isnot(None))
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    if not row:
        return None
    try:
        points = json.loads(row.pain_points_extracted or "[]")
    except (TypeError, ValueError):
        return None
    return points[0].get("evidence_quote") if points else None


def _existing_templates_summary(db):
    """Real, current template inventory (built-in + DB) for the drafting/QC agents to
    check distinctness against -- built-in wording is fetched live (Step 9.5 follow-up),
    same as the dashboard's Built-in tab."""
    summary = []
    for spec in TEMPLATE_LIBRARY.values():
        details = fetch_template_wording(spec["name"])
        summary.append({
            "name": spec["name"], "purpose": "FIRST_TOUCH",
            "body_text": (details or {}).get("body_text") or "",
        })
    for row in db.query(WhatsappTemplate).filter(WhatsappTemplate.status != "ADMIN_REJECTED").all():
        summary.append({"name": row.name, "purpose": row.purpose, "body_text": row.body_text})
    return summary


def propose_new_template(db, reason, context, purpose="FOLLOW_UP", product_id=None):
    """Step 9.6 sub-step 4 -- the full safe pipeline: gather the real existing-template
    inventory, ask the drafting agent (sub-step 2), QC-gate the result (sub-step 3), and
    only then persist it as a DRAFT (sub-step 1) -- never a real Meta call anywhere in
    this function. Returns the created DRAFT row, or None if the agent declined or QC
    rejected (both already logged via their own AgentEvent calls, nothing silent).
    """
    from agents.template_agent import draft_template
    from agents.quality_controller_agent import review_template_draft

    existing_templates = _existing_templates_summary(db)

    candidate = draft_template(db, reason, context, existing_templates)
    if not candidate:
        return None

    qc_result = review_template_draft(db, candidate, reason, existing_templates)
    if not qc_result["approved"]:
        return None

    return create_draft_template(
        db, candidate["name"], "en", candidate["category"], candidate["purpose"] or purpose,
        candidate["body_text"], candidate["variable_labels"], product_id=product_id,
        reasoning=candidate.get("reasoning"),
    )
