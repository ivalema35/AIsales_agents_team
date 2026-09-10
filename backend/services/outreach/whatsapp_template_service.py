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



# Real, plausible sample values for each {{n}} placeholder -- Meta's Create Template API
# requires an "example" on the BODY component whenever it has variables, so its real
# reviewers/classifier have something concrete to check the template against. A real
# rejection (2026-08-21, pain_point_follow_up, no reason given by Meta) traced back to
# this being missing entirely -- confirmed by comparing against this same WABA's own
# already-APPROVED templates, both of which carry a real "example" block. "Sparrk Gaming
# Zone" / "some customers mentioned slow response times" are the exact example values
# already on file for ivinfotech_pain_point_outreach, reused here for consistency.
_EXAMPLE_VALUES = {
    "contact_name": "Rahul",
    "company_name": "Sparrk Gaming Zone",
    "pain_point_phrase": "some customers mentioned slow response times",
}


def _create_on_meta(name, language, category, body_text, variable_labels=None,
                    button_url=None, button_label=None,
                    button_2_url=None, button_2_label=None):
    """The actual real Meta Create Template API call, shared by every path that ends in
    a real submission (a direct admin submit, or an admin approving an AI draft --
    Step 9.6). Raises on failure -- same contract as every other real send in this
    codebase (email_service.send_email, whatsapp_service.send_template_message); the
    caller decides how to surface that. Returns Meta's raw response dict.

    `button_url` (real feature, added after the operator asked "WhatsApp me demo URL
    kyun nahi" during a live Phase 13 test) -- a STATIC call-to-action button, baked into
    the template at submission time. Deliberately static, not a {{1}}-suffixed dynamic
    URL: this system's content assets are scoped per PRODUCT, not per lead, so every real
    send of a given template already points at the same real, admin-approved link -- no
    per-send parameter is needed, and Meta requires none for a button with no variable.

    `button_2_url`/`button_2_label` (2026-09-10, real user ask): a second, independent
    static URL button -- Meta's own real limit is up to 2 URL buttons per template
    (verified against Meta's live documentation before building this, not assumed). Both
    buttons live in the SAME single BUTTONS component's `buttons` array -- Meta rejects
    two separate BUTTONS components in one template.
    """
    if not Config.WHATSAPP_TOKEN:
        raise RuntimeError("WHATSAPP_TOKEN not configured")
    if not Config.WHATSAPP_WABA_ID:
        raise RuntimeError("WHATSAPP_WABA_ID not configured")

    body_component = {"type": "BODY", "text": body_text}
    if variable_labels:
        body_component["example"] = {
            "body_text": [[_EXAMPLE_VALUES.get(v, "example") for v in variable_labels]]
        }
    components = [body_component]
    buttons = []
    if button_url:
        buttons.append({"type": "URL", "text": (button_label or "View")[:25], "url": button_url})
    if button_2_url:
        buttons.append({"type": "URL", "text": (button_2_label or "View")[:25], "url": button_2_url})
    if buttons:
        components.append({"type": "BUTTONS", "buttons": buttons})
    payload = {
        "name": name,
        "language": language,
        "category": category,
        "components": components,
    }
    resp = requests.post(
        _templates_url(),
        headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def submit_template(db, name, language, category, purpose, body_text, variable_labels,
                    product_id=None, followup_level=None, button_url=None, button_label=None,
                    button_2_url=None, button_2_label=None):
    """Real Meta Create Template API call, for a template an admin is submitting
    directly from the dashboard form -- creates the row AND submits it to Meta in one
    step, exactly like before Step 9.6. Stores the new row as PENDING with Meta's own
    returned template id, never guesses an approval state.

    product_id is optional (tracker.md Step 9.5 follow-up) -- None keeps the template
    shared/usable by every product (today's default, and the only option before this),
    set means only that one product may use it. Deliberately optional rather than
    mandatory: a new product-specific template still needs its own separate Meta
    approval, so defaulting to shared keeps that real cost down.

    followup_level (Phase 13 Step 13.2) is REQUIRED when purpose="FOLLOW_UP" -- validated
    by the caller (api/whatsapp_templates.py), not here, so this stays a plain write.

    button_url/button_label -- a real, static call-to-action button baked into this
    template (see _create_on_meta's own docstring for why static, not per-lead dynamic).
    """
    data = _create_on_meta(name, language, category, body_text, variable_labels,
                           button_url=button_url, button_label=button_label,
                           button_2_url=button_2_url, button_2_label=button_2_label)

    row = WhatsappTemplate(
        name=name,
        language=language,
        category=category,
        purpose=purpose,
        followup_level=followup_level if purpose == "FOLLOW_UP" else None,
        button_url=button_url,
        button_label=button_label,
        button_2_url=button_2_url,
        button_2_label=button_2_label,
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
                          product_id=None, reasoning=None, followup_level=None,
                          button_url=None, button_label=None, button_2_url=None, button_2_label=None,
                          qc_caution=None, draft_context=None):
    """Step 9.6 -- an AI-authored candidate template, stored as DRAFT. Deliberately makes
    NO real Meta call: nothing an AI writes reaches Meta (or a real business) without an
    explicit admin approve action first (approve_draft_and_submit below). `reasoning` is
    the drafting agent's own explanation of why this candidate addresses the real signal
    it was given -- shown to the admin so an approve/reject decision is informed, not blind.

    followup_level (Phase 13 Step 13.2) -- the level this draft was requested for, only
    meaningful when purpose="FOLLOW_UP" (propose_new_template's own caller already knows
    which level triggered the real signal this was drafted from).

    button_url/button_label (2026-09-09) -- a real, static call-to-action button resolved
    from this product's own content assets (never invented by the drafting agent itself).
    qc_caution (2026-09-09) -- set only when this draft is being saved despite QC raising a
    concern (see propose_new_template's `guarantee` mode) -- kept separate from `reasoning`
    so the admin sees "what the AI believes" and "what QC flagged" as two distinct things.
    draft_context (2026-09-09) -- JSON {"reason","campaign_strategy_angle"}, kept so a later
    human feedback revision (revise_draft_template) stays grounded in the same real signal.
    """
    row = WhatsappTemplate(
        name=name,
        language=language,
        category=category,
        purpose=purpose,
        followup_level=followup_level if purpose == "FOLLOW_UP" else None,
        button_url=button_url,
        button_label=button_label,
        button_2_url=button_2_url,
        button_2_label=button_2_label,
        body_text=body_text,
        variable_labels=json.dumps(variable_labels),
        status="DRAFT",
        product_id=product_id,
        origin="AI",
        reasoning=reasoning,
        qc_caution=qc_caution,
        draft_context=json.dumps(draft_context) if draft_context else None,
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

    variable_labels = json.loads(template.variable_labels or "[]")
    data = _create_on_meta(template.name, template.language, template.category,
                           template.body_text, variable_labels,
                           button_url=template.button_url, button_label=template.button_label,
                           button_2_url=template.button_2_url, button_2_label=template.button_2_label)
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

    if real_status == "REJECTED":
        _propose_replacement_after_meta_rejection(db, template)
    return True


def _propose_replacement_after_meta_rejection(db, rejected_template):
    """2026-09-08, real user ask: "reject ho to naya try kare" (if Meta rejects, try a new
    one) -- so a rejection doesn't just dead-end waiting for an admin to notice and click
    Ask AI again. Drafts ONE fresh candidate for the SAME purpose/product/level, informed
    by exactly why Meta said no, and stores it as a DRAFT -- same as every AI-authored
    candidate, it still needs an explicit admin approve before it ever reaches Meta again.
    Never raises: a failed auto-retry must not break the poll loop that called this.
    """
    try:
        reason = (
            f'A previously-submitted template ("{rejected_template.name}", purpose='
            f'{rejected_template.purpose}) was REJECTED by Meta'
            + (f' with reason: "{rejected_template.rejection_reason}"' if rejected_template.rejection_reason else " (no reason given)")
            + ". Propose a genuinely different candidate for the SAME purpose that avoids "
              "whatever caused that rejection -- different wording, not just a minor tweak."
        )
        context = {
            "rejected_body_text": rejected_template.body_text,
            "rejected_reason": rejected_template.rejection_reason,
        }
        result = propose_new_template(
            db, reason, context, purpose=rejected_template.purpose,
            product_id=rejected_template.product_id, followup_level=rejected_template.followup_level,
        )
        if result:
            logger.info("auto-drafted replacement '%s' after Meta rejected '%s'",
                       result.name, rejected_template.name)
        else:
            logger.info("auto-retry after Meta rejection of '%s' declined (agent or QC said no)",
                       rejected_template.name)
    except Exception:  # noqa: BLE001 - a failed auto-retry must never break the poll loop
        logger.exception("auto-retry template proposal failed after rejection of '%s'", rejected_template.name)


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


def get_approved_followup_template(db, followup_level, product_id=None):
    """The real gap Step 9.3 found live: a WhatsApp follow-up had no choice but to
    resend the exact same first-touch template word for word. Phase 13 Step 13.2
    tightened this further: returns the approved, active FOLLOW_UP template for THIS
    EXACT level, or None -- never a different level's template, and never falls back to
    resending touch 1's own template the way this function used to. Sending the wrong
    level's real, approved text is worse than sending nothing (MASTER §5B Step 13.2's
    own rule); the caller (jobs/outreach_wa_handler.py) skips the WhatsApp send entirely
    when this returns None.

    Tiered: a template scoped to THIS product wins over a shared one, so a product with
    a genuinely distinct pitch can override the shared default without disabling it for
    everyone else. is_active is a manual kill-switch independent of Meta's own APPROVED
    status -- a disabled template is never selected even if Meta still shows it approved.
    """
    base = db.query(WhatsappTemplate).filter(
        WhatsappTemplate.purpose == "FOLLOW_UP",
        WhatsappTemplate.followup_level == followup_level,
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


def get_approved_first_touch_template(db, product_id=None):
    """Real gap the operator found live (2026-08-25): a demo/video button on a WhatsApp
    template is baked in at Meta-approval time, unlike email's CTA (resolved fresh from
    live content_assets on every real send) -- so a button pointing at ONE product's real
    demo, submitted only ever as a single SHARED template, would show every other
    product's leads a link that isn't theirs. TEMPLATE_LIBRARY (services/outreach/
    whatsapp_templates.py) has no product concept at all and never will (it's the
    generic/button-less fallback); a real product-specific pitch belongs here instead,
    in the same admin-managed table + tiered lookup already proven for FOLLOW_UP
    (get_approved_followup_template above) -- product-scoped wins over shared, exactly
    the same rule, same reasoning.

    Returns None (not an error) when no real FIRST_TOUCH template exists in this table
    yet for this product or shared -- the caller falls back to TEMPLATE_LIBRARY, which
    stays a fully valid, tested, button-less real send; this table is additive, not a
    replacement for that hardcoded library.
    """
    base = db.query(WhatsappTemplate).filter(
        WhatsappTemplate.purpose == "FIRST_TOUCH",
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


FOLLOWUP_LEVEL_JOB = {
    1: "Level 1 (RE-PRESENT): assume the first touch's real asset/pitch was skimmed, not "
       "read -- a short reminder tied to their pain point, pointing back to it.",
    2: "Level 2 (ASK): a short, genuine open question inviting a reply -- nothing else, "
       "no pitch, no new claim. The goal is a reply, not another sell.",
    3: "Level 3 (STANDING OFFER): the last touch. A low-pressure, warm note that we're "
       "available if this becomes useful later -- never urgency, never a final push.",
}


def find_template_improvement_reason(db, purpose=None, followup_level=None, product_id=None, want_button=False):
    """Step 9.6 sub-step 4 -- real signal detection for the manual "ask AI to draft a
    template" trigger. Never fabricates a need: returns (reason, context, purpose,
    product_id, followup_level) only when a real, data-backed gap exists, or None
    otherwise -- an admin pressing the button on a healthy system should get an honest
    "nothing to propose", not a forced draft.

    `purpose` (Step 9.6 follow-up, 2026-08-21) -- optional, "FIRST_TOUCH" or "FOLLOW_UP".
    The admin picks which one they want a template for; this scopes the SEARCH for a
    real signal to that purpose (never forces a fabricated one) -- an honest "nothing to
    propose for FIRST_TOUCH right now" is a completely valid, expected outcome if every
    real FIRST_TOUCH template is already performing fine.

    `followup_level` (Phase 13 Step 13.2) -- REQUIRED whenever purpose="FOLLOW_UP" (the
    caller validates this, not this function): each of the 3 real levels is its own
    coverage gap now, matching get_approved_followup_template()'s own strict per-level
    matching -- a healthy Level 1 says nothing about whether Level 2 has ever been
    covered.

    `product_id` (2026-09-08, real live gap): a product with no product-specific
    FIRST_TOUCH template falls back to the shared library, which is real and functional
    but generic (mentions "IVinfotech's software and IT solutions", never this product's
    own name/pitch) -- a genuine coverage gap for THAT product, even though the shared
    library means a "no FIRST_TOUCH template at all" gap can never exist system-wide.
    Only checked when the caller explicitly names a product (Campaign Detail's own
    Daily Review, which knows which product it's reviewing) -- omitted, this behaves
    exactly as before.

    `want_button` (2026-09-09, real user ask): a human already has an approved
    product-specific FIRST_TOUCH template but explicitly wants a button-enabled version.
    Only counted as a real gap if a real content asset now exists for this product AND
    the existing template has no button yet -- asking again with no real asset available
    would just repeat the same honest "no button" outcome, so that's deliberately NOT
    treated as a signal here (the caller shows a direct, specific message instead of
    running the drafting pipeline for nothing).

    Checks four real gaps, in order:
    1. An existing WhatsApp template (of the requested purpose+level, if given) with a
       real, statistically meaningful reply rate below LOW_REPLY_RATE_THRESHOLD (Step
       9.2's own performance rollup -- the exact real data this step was built to use).
    2. If `product_id` is given and purpose is "FIRST_TOUCH" (or unset), whether this
       PRODUCT has its own approved FIRST_TOUCH template -- the shared library always
       covers the system-wide case, but a specific product genuinely may not have one.
    2b. If this product DOES have its own approved FIRST_TOUCH template but it has no
        button, `want_button` is set, and a real content asset exists for this product now.
    3. If nothing is underperforming AND purpose isn't "FIRST_TOUCH" (TEMPLATE_LIBRARY's
       GENERIC/PAIN_POINT_HOOK entries are always a real, available system-wide FIRST_TOUCH
       fallback, so THAT gap can never genuinely exist), whether NO approved template
       exists yet for THIS SPECIFIC follow-up level -- the real gap Step 9.3 found live
       (GameZone Visnagar's follow-up being byte-identical to its first touch), now scoped
       per level rather than per purpose.
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
            # A FOLLOW_UP candidate only counts as a real signal for THIS level -- a
            # weak Level 1 template must never trigger a Level 2 proposal.
            if real_purpose == "FOLLOW_UP" and followup_level:
                row_level = existing_row.followup_level if existing_row else None
                if row_level != followup_level:
                    continue
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
            if real_purpose == "FOLLOW_UP" and followup_level:
                reason += f" This must be written for {FOLLOWUP_LEVEL_JOB[followup_level]}"
            context = {"variant_id": worst["variant_id"], "sent": worst["sent"],
                       "replied": worst["replied"], "reply_rate": worst["reply_rate"]}
            variant_product_id = existing_row.product_id if existing_row else None
            return reason, context, real_purpose, variant_product_id, followup_level

    if product_id and purpose in (None, "FIRST_TOUCH"):
        existing_first_touch = get_approved_first_touch_template(db, product_id=product_id)
        if existing_first_touch is None:
            from database.models import Product
            product = db.get(Product, product_id)
            reason = (
                f'No approved WhatsApp FIRST_TOUCH template exists yet for the product '
                f'"{product.title if product else product_id}" specifically -- its real WhatsApp '
                f'sends currently use the shared, product-agnostic fallback template instead of a '
                f'pitch written for this product. Propose one written specifically for this product, '
                f'using its own real title/description/value proposition below, tied to a real pain '
                f'point when one is available.'
            )
            context = {
                "product_title": product.title if product else None,
                "product_description": product.description if product else None,
                "sample_pain_point": _sample_real_pain_point(db),
            }
            return reason, context, "FIRST_TOUCH", product_id, None
        if want_button and not existing_first_touch.button_url:
            button_asset = _resolve_button_asset(db, product_id)
            if button_asset:
                from database.models import Product
                product = db.get(Product, product_id)
                reason = (
                    f'This product already has its own approved FIRST_TOUCH template '
                    f'("{existing_first_touch.name}"), but it has no call-to-action button, and a '
                    f'human explicitly wants a button-enabled version now that a real demo/video '
                    f'asset exists for this product. Propose a button-enabled version of the SAME '
                    f'core pitch (same message, add the button) -- not a different angle.'
                )
                context = {
                    "product_title": product.title if product else None,
                    "product_description": product.description if product else None,
                    "existing_template_name": existing_first_touch.name,
                    "existing_body_text": existing_first_touch.body_text,
                }
                return reason, context, "FIRST_TOUCH", product_id, None

    # TEMPLATE_LIBRARY's GENERIC/PAIN_POINT_HOOK entries are always a real, available FIRST_TOUCH fallback
    # (select_template() falls back to it unconditionally) -- a "no FIRST_TOUCH template"
    # gap can never genuinely exist, so this check only ever applies to FOLLOW_UP.
    if purpose == "FOLLOW_UP" and followup_level and get_approved_followup_template(db, followup_level) is None:
        reason = (
            f"No approved WhatsApp template exists yet for Level {followup_level} of the "
            f"3-level follow-up sequence -- that touch currently sends nothing on WhatsApp. "
            f"This must be written for {FOLLOWUP_LEVEL_JOB[followup_level]}"
        )
        # This gap has no real performance numbers behind it (unlike the underperformer
        # branch above), which left the drafting agent writing in the dark and producing
        # vague, generic candidates that QC correctly rejected (found live, 2026-08-21).
        # A real sample pain point gives it something concrete to write a specific,
        # non-generic template around -- never fabricated, sourced from a real lead.
        sample_pain_point = _sample_real_pain_point(db)
        context = {"sample_pain_point": sample_pain_point} if sample_pain_point else {}
        return reason, context, "FOLLOW_UP", None, followup_level

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


MAX_TEMPLATE_DRAFT_ATTEMPTS = 2  # one retry with QC's feedback, same pattern as email
# drafting's MAX_DRAFT_ATTEMPTS -- 2026-09-08, real live case: the first candidate for a
# genuinely real product coverage gap (IV Classes) was QC-rejected for being too close to
# an existing template's structure -- a one-shot draft-then-give-up wasted that real signal
# instead of trying again with the exact reason it failed.

BUTTON_ASSET_TYPES = ("DEMO_URL", "VIDEO_URL")  # preferred order -- a live demo beats a video


def _resolve_button_asset(db, product_id):
    """A REAL, admin-managed content asset to use as a template's button link -- never
    invented by the drafting agent (see template_agent.draft_template's own docstring).
    Returns {"title","value"} for the first matching asset (product-scoped preferred over
    shared, DEMO_URL preferred over VIDEO_URL), or None if this product has no such asset
    yet -- a legitimate "can't add a button" outcome, not an error."""
    from services.message_format_service import get_available_assets
    assets = get_available_assets(db, product_id)
    for asset_type in BUTTON_ASSET_TYPES:
        for asset in assets:
            if asset["asset_type"] == asset_type:
                return {"title": asset["title"], "value": asset["value"]}
    return None


def propose_new_template(db, reason, context, purpose="FOLLOW_UP", product_id=None, followup_level=None,
                         campaign_strategy_angle=None, want_button=False, guarantee=False):
    """Step 9.6 sub-step 4 -- the full safe pipeline: gather the real existing-template
    inventory, ask the drafting agent (sub-step 2), QC-gate the result (sub-step 3), and
    only then persist it as a DRAFT (sub-step 1) -- never a real Meta call anywhere in
    this function. Returns the created DRAFT row, or None if the agent declined on every
    attempt (already logged via its own AgentEvent calls, nothing silent).

    `campaign_strategy_angle` (2026-09-09) -- when this proposal is for one specific
    campaign's own explicit "Ask AI for a template" click, ground the draft in that real
    campaign's strategy, same as email/outreach copy already does.

    `want_button` (2026-09-09) -- the human asked for a call-to-action button. Resolves a
    REAL content asset for this product (never invented) and passes it through; if no such
    asset exists yet, the draft still proceeds text-only (a legitimate outcome, logged in
    the draft's own reasoning, not a failure).

    `guarantee` (2026-09-09, real user ask: "user mange to AI ko template dena hi hoga" --
    when a human explicitly asks for a template for a real, confirmed gap, they must get a
    real candidate to review). REAL LIVE BUG this fixes: QC vetoed 4/4 genuinely distinct
    candidates for a real coverage gap (2026-09-09, "Ai automaion Push" campaign) purely on
    a "too similar to the shared template" judgment call -- the human never even saw them,
    even though nothing reaches Meta without their own explicit approve regardless. With
    guarantee=True, QC's rejection reasons on the LAST attempt no longer discard the
    candidate -- they're stored as a visible `qc_caution` on the DRAFT instead, so the human
    decides with full information rather than the AI silently deciding on their behalf.
    Only used for a human-initiated, campaign-scoped ask; the system-wide background
    signal-scan (no campaign_id) keeps the original honest "declined" behavior.
    """
    from agents.template_agent import draft_template
    from agents.quality_controller_agent import review_template_draft

    existing_templates = _existing_templates_summary(db)

    # 2026-09-08, real live bug: QC was never shown the product's own brief, so it had no
    # ground truth to tell a real, brief-supported capability from an invented one -- the
    # same class of gap already fixed for email QC on 2026-08-13. Fetched fresh here
    # (rather than trusting `context` to already carry it) so this holds for every reason
    # type that names a real product_id, not just the coverage-gap signal.
    product_brief = None
    if product_id:
        from database.models import Product
        product = db.get(Product, product_id)
        if product:
            product_brief = {"title": product.title, "description": product.description,
                             "value_proposition": product.value_proposition}

    button_asset = _resolve_button_asset(db, product_id) if (want_button and product_id) else None

    qc_feedback = None
    last_candidate = None
    last_qc_result = None
    for _attempt in range(1, MAX_TEMPLATE_DRAFT_ATTEMPTS + 1):
        candidate = draft_template(
            db, reason, context, existing_templates, qc_feedback=qc_feedback,
            campaign_strategy_angle=campaign_strategy_angle, want_button=want_button,
            button_asset=button_asset,
        )
        if not candidate:
            if guarantee and _attempt < MAX_TEMPLATE_DRAFT_ATTEMPTS:
                qc_feedback = ("You declined last time, but a human has explicitly requested a "
                              "template for this real, confirmed gap -- produce your best "
                              "reasonable candidate from the given CONTEXT instead of declining.")
                continue
            return None

        qc_result = review_template_draft(db, candidate, reason, existing_templates,
                                          product_brief=product_brief)
        last_candidate, last_qc_result = candidate, qc_result
        if qc_result["approved"]:
            button_url = button_asset["value"] if (button_asset and candidate.get("button_label")) else None
            return create_draft_template(
                db, candidate["name"], "en", candidate["category"], candidate["purpose"] or purpose,
                candidate["body_text"], candidate["variable_labels"], product_id=product_id,
                reasoning=candidate.get("reasoning"), followup_level=followup_level,
                button_url=button_url, button_label=candidate.get("button_label"),
                draft_context={"reason": reason, "campaign_strategy_angle": campaign_strategy_angle},
            )
        qc_feedback = "; ".join(qc_result["rejection_reasons"])

    if guarantee and last_candidate:
        button_url = button_asset["value"] if (button_asset and last_candidate.get("button_label")) else None
        caution = "; ".join((last_qc_result or {}).get("rejection_reasons") or [])
        return create_draft_template(
            db, last_candidate["name"], "en", last_candidate["category"], last_candidate["purpose"] or purpose,
            last_candidate["body_text"], last_candidate["variable_labels"], product_id=product_id,
            reasoning=last_candidate.get("reasoning"), followup_level=followup_level,
            button_url=button_url, button_label=last_candidate.get("button_label"),
            qc_caution=caution or None,
            draft_context={"reason": reason, "campaign_strategy_angle": campaign_strategy_angle},
        )
    return None


def revise_draft_template(db, template, instruction, want_button=None):
    """2026-09-09, real user ask: "user review kar sake feedback dekar sudhar sake usme" --
    a human reviewing an AI-drafted (still DRAFT, never yet sent to Meta) template can give
    a free-text instruction and get a revised candidate, same "current state + one
    instruction" conversational pattern already proven for outreach/kickoff draft
    revisions elsewhere in this codebase. Never QC-gated into silence for the same reason
    `guarantee=True` isn't in propose_new_template: the human is looking at this right now
    and will decide whether to approve it -- QC's concerns become a visible `qc_caution`,
    never a reason to withhold the revision they explicitly asked for.

    `want_button` -- tri-state: None keeps the template's current button as-is, True/False
    explicitly adds/removes one (resolving a real content asset the same way a fresh
    proposal does; explicitly requesting a button with no real asset available is a no-op,
    same honest "can't invent a link" rule as propose_new_template).
    """
    from agents.template_agent import draft_template
    from agents.quality_controller_agent import review_template_draft
    from database.models import Product

    if template.status != "DRAFT":
        raise ValueError(f"template {template.name!r} is not a DRAFT (status={template.status!r})")

    try:
        stored_context = json.loads(template.draft_context) if template.draft_context else {}
    except (TypeError, ValueError):
        stored_context = {}
    reason = stored_context.get("reason") or f"Revising the existing draft '{template.name}' per human feedback."
    campaign_strategy_angle = stored_context.get("campaign_strategy_angle")

    resolved_want_button = template.button_url is not None if want_button is None else bool(want_button)
    button_asset = _resolve_button_asset(db, template.product_id) if (resolved_want_button and template.product_id) else None

    product_brief = None
    if template.product_id:
        product = db.get(Product, template.product_id)
        if product:
            product_brief = {"title": product.title, "description": product.description,
                             "value_proposition": product.value_proposition}

    existing_templates = [t for t in _existing_templates_summary(db) if t.get("name") != template.name]
    previous_candidate = {
        "name": template.name,
        "body_text": template.body_text,
        "variable_labels": json.loads(template.variable_labels or "[]"),
        "button_label": template.button_label,
    }

    candidate = draft_template(
        db, reason, {}, existing_templates, campaign_strategy_angle=campaign_strategy_angle,
        want_button=resolved_want_button, button_asset=button_asset,
        human_instruction=instruction, previous_candidate=previous_candidate,
    )
    if not candidate:
        raise RuntimeError("template revision failed -- the AI could not produce a revised candidate")

    qc_result = review_template_draft(db, candidate, reason, existing_templates, product_brief=product_brief)

    template.name = candidate["name"]
    template.category = candidate["category"]
    template.body_text = candidate["body_text"]
    template.variable_labels = json.dumps(candidate["variable_labels"])
    template.reasoning = candidate.get("reasoning")
    template.button_url = button_asset["value"] if (button_asset and candidate.get("button_label")) else None
    template.button_label = candidate.get("button_label")
    template.qc_caution = None if qc_result["approved"] else "; ".join(qc_result["rejection_reasons"]) or None
    template.draft_context = json.dumps({"reason": reason, "campaign_strategy_angle": campaign_strategy_angle})
    db.commit()
    db.refresh(template)
    logger.info("whatsapp template draft '%s' revised by human feedback", template.name)
    return template
