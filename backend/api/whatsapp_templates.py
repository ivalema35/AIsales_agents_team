from __future__ import annotations
import json
import re

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import WhatsappTemplate, Product, Campaign
from services.outreach.whatsapp_template_service import (
    submit_template,
    poll_template_status,
    fetch_template_wording,
    approve_draft_and_submit,
    reject_draft,
    find_template_improvement_reason,
    propose_new_template,
    revise_draft_template,
    get_approved_first_touch_template,
    _resolve_button_asset,
)
from services.outreach.whatsapp_templates import TEMPLATE_LIBRARY

whatsapp_templates_bp = Blueprint("whatsapp_templates", __name__, url_prefix="/api/v1/whatsapp-templates")

VALID_CATEGORIES = {"MARKETING", "UTILITY", "AUTHENTICATION"}
VALID_PURPOSES = {"FIRST_TOUCH", "FOLLOW_UP"}
# Meta's own naming rule for a template `name`: lowercase letters, digits, underscores only.
NAME_RE = re.compile(r"^[a-z0-9_]+$")


def _serialize(row, product_titles=None):
    return {
        "id": row.id,
        "name": row.name,
        "language": row.language,
        "category": row.category,
        "purpose": row.purpose,
        # Phase 13 Step 13.2 -- which of the 3 real follow-up levels this is written for.
        # Only meaningful when purpose="FOLLOW_UP"; null for FIRST_TOUCH and for any
        # FOLLOW_UP row that predates this column.
        "followup_level": row.followup_level,
        # A real, static call-to-action button baked into the approved template. Null =
        # no button (today's default, unchanged).
        "button_url": row.button_url,
        "button_label": row.button_label,
        "body_text": row.body_text,
        "variable_labels": json.loads(row.variable_labels or "[]"),
        "status": row.status,
        "rejection_reason": row.rejection_reason,
        "meta_template_id": row.meta_template_id,
        # None/null = shared, usable by every product (tracker.md Step 9.5 follow-up).
        "product_id": row.product_id,
        "product_title": (product_titles or {}).get(row.product_id) if row.product_id else None,
        "is_active": bool(row.is_active),
        # ADMIN (dashboard form, real Meta call immediately) or AI (Step 9.6 draft,
        # starts as DRAFT, never reaches Meta without an explicit admin approve).
        "origin": row.origin,
        "reasoning": row.reasoning,
        # 2026-09-09 -- set only when a human-requested draft was saved despite QC raising
        # a concern (see propose_new_template's `guarantee` mode) -- shown separately from
        # the AI's own `reasoning` so an admin sees both what the AI believes and what QC
        # flagged, instead of the draft being silently withheld over a judgment call.
        "qc_caution": row.qc_caution,
        "created_at": str(row.created_at),
        "updated_at": str(row.updated_at),
    }


def _product_titles_for(db, row):
    if not row.product_id:
        return {}
    product = db.get(Product, row.product_id)
    return {row.product_id: product.title} if product else {}


@whatsapp_templates_bp.route("/builtin", methods=["GET"])
def list_builtin_templates():
    """Read-only view of TEMPLATE_LIBRARY (services/outreach/whatsapp_templates.py) --
    the 2 templates already live and actively used for real first-touch sends today,
    submitted by hand outside this admin flow before Step 9.5 existed (tracker.md Step
    3.4). Not editable/deletable here -- this library is code-managed, not DB-managed.

    Their approved wording was never stored in this codebase (only name/language/
    variables were), so each one's real body_text is fetched live from Meta on every
    call -- display-only, a failed fetch just leaves body_text null rather than
    breaking the page (fetch_template_wording()'s own contract).
    """
    out = []
    for key, spec in TEMPLATE_LIBRARY.items():
        details = fetch_template_wording(spec["name"])
        out.append({
            "key": key,
            "name": spec["name"],
            "language": spec["language"],
            "variable_labels": spec["variables"],
            "status": spec.get("status", "APPROVED"),
            "body_text": details["body_text"] if details else None,
        })
    return jsonify(out)


@whatsapp_templates_bp.route("", methods=["GET"])
def list_templates():
    db = SessionLocal()
    try:
        query = db.query(WhatsappTemplate)
        status = request.args.get("status")
        if status:
            query = query.filter(WhatsappTemplate.status == status)
        purpose = request.args.get("purpose")
        if purpose:
            query = query.filter(WhatsappTemplate.purpose == purpose)
        product_id = request.args.get("product_id")
        if product_id:
            query = query.filter(WhatsappTemplate.product_id == product_id)
        # 2026-09-09, real bug found live: this ordered by created_at, while
        # get_approved_first_touch_template() (the REAL selection logic behind every real
        # preview/send) tie-breaks by updated_at -- two different rules for "which one is
        # current" meant a Daily Review dropdown built from this list could genuinely name
        # a different template than the actual preview above it. Matching the same column
        # here means any future consumer of this list agrees with the real selection logic
        # by construction, not by coincidence.
        rows = query.order_by(WhatsappTemplate.updated_at.desc()).all()
        product_titles = {p.id: p.title for p in db.query(Product).all()}
        return jsonify([_serialize(r, product_titles) for r in rows])
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>", methods=["GET"])
def get_template(template_id):
    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        product_titles = _product_titles_for(db, row)
        return jsonify(_serialize(row, product_titles))
    finally:
        db.close()


@whatsapp_templates_bp.route("", methods=["POST"])
def create_template():
    """Real Meta Create Template API call (services/outreach/whatsapp_template_service.py).
    This is a deliberate, real external action -- submitting a bad/messy template
    repeatedly can affect the WABA's own standing with Meta, so every field is
    validated up front rather than letting a 422-worthy request reach the real API."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    name = str(data.get("name", "")).strip()
    if not name or not NAME_RE.match(name):
        errors.append("name is required and must be lowercase letters/digits/underscores only")

    category = data.get("category")
    if category not in VALID_CATEGORIES:
        errors.append(f"category must be one of {sorted(VALID_CATEGORIES)}")

    purpose = data.get("purpose", "FIRST_TOUCH")
    if purpose not in VALID_PURPOSES:
        errors.append(f"purpose must be one of {sorted(VALID_PURPOSES)}")

    # Phase 13 Step 13.2 -- required whenever purpose=FOLLOW_UP: get_approved_followup_
    # template() matches strictly on this value, so a FOLLOW_UP template with no level
    # could never actually be selected for any real send.
    followup_level = data.get("followup_level")
    if purpose == "FOLLOW_UP":
        if followup_level not in (1, 2, 3):
            errors.append("followup_level must be 1, 2, or 3 when purpose is FOLLOW_UP")
    else:
        followup_level = None

    body_text = str(data.get("body_text", "")).strip()
    if not body_text:
        errors.append("body_text is required")

    variable_labels = data.get("variable_labels", [])
    if not isinstance(variable_labels, list):
        errors.append("variable_labels must be a JSON array")
    else:
        placeholder_count = len(re.findall(r"\{\{\d+\}\}", body_text))
        if placeholder_count != len(variable_labels):
            errors.append(
                f"body_text has {placeholder_count} {{{{n}}}} placeholder(s) but "
                f"variable_labels has {len(variable_labels)} -- these must match"
            )

    language = str(data.get("language") or "en").strip()

    # Optional (tracker.md Step 9.5 follow-up) -- None/omitted keeps the template shared
    # across every product, today's only behavior before this. Validated against a real
    # product row so a typo'd/stale id can't silently produce an unusable scoped template.
    product_id = data.get("product_id") or None

    # A real, static call-to-action button (added after the operator asked why WhatsApp
    # follow-ups had no demo link, mirroring the email side's CTA button). Optional --
    # None keeps today's plain-text-only behavior. Meta caps button text at 25 chars.
    button_url = str(data.get("button_url") or "").strip() or None
    button_label = str(data.get("button_label") or "").strip()[:25] or None
    if button_url and not re.match(r"^https?://", button_url):
        errors.append("button_url must be a real http(s) URL")
    if button_label and not button_url:
        errors.append("button_label requires button_url")

    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        if product_id and not db.get(Product, product_id):
            return jsonify({"error": [f"product {product_id!r} not found"]}), 422
        if db.query(WhatsappTemplate).filter(WhatsappTemplate.name == name).first():
            return jsonify({"error": [f"a template named {name!r} already exists"]}), 422
        try:
            row = submit_template(db, name, language, category, purpose, body_text, variable_labels,
                                  product_id, followup_level=followup_level,
                                  button_url=button_url, button_label=button_label)
        except Exception as exc:  # noqa: BLE001 - a real API failure must surface, not 500 silently
            return jsonify({"error": [f"Meta submission failed: {exc}"]}), 502
        product_titles = _product_titles_for(db, row)
        return jsonify(_serialize(row, product_titles)), 201
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>", methods=["PATCH"])
def update_template(template_id):
    """is_active toggle and/or product_id reassignment -- name/wording/category can't be
    changed post-submission (Meta's own template is immutable once created; editing those
    fields here would silently drift from what Meta actually approved). is_active is a
    manual kill-switch independent of Meta's own status: an admin can pause a template
    (e.g. underperforming) without deleting its real history, and a disabled template is
    never selected by get_approved_followup_template() even if Meta still shows it APPROVED.

    product_id (2026-09-08, real user ask: "agar existing template choose karna ho to kaise
    karenge") -- unlike name/wording, this is a LOCAL-ONLY scoping field Meta never sees,
    so reassigning it is safe: pass a real product id to scope an already-approved (or any)
    template to that product, or null to make it shared/usable by every product again. This
    is how an admin points an existing, already-Meta-approved template at a product that
    doesn't have its own yet, instead of drafting/submitting a brand new one.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or ("is_active" not in data and "product_id" not in data):
        return jsonify({"error": "request body must include is_active and/or product_id"}), 422

    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        if "is_active" in data:
            row.is_active = bool(data["is_active"])
        if "product_id" in data:
            product_id = data["product_id"]
            if product_id and not db.get(Product, product_id):
                return jsonify({"error": [f"product {product_id} not found"]}), 422
            row.product_id = product_id or None
        db.commit()
        db.refresh(row)
        product_titles = _product_titles_for(db, row)
        return jsonify(_serialize(row, product_titles))
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>", methods=["DELETE"])
def delete_template(template_id):
    """Real hard delete -- but ONLY for a template that reached a genuine dead end:
    ADMIN_REJECTED (an admin rejected an AI draft before it ever reached Meta) or
    REJECTED (Meta itself declined a real submission). Never allowed for DRAFT/PENDING/
    APPROVED -- those are either awaiting a real decision or actively usable, and this
    dashboard has no way to un-submit something from Meta anyway. Same real hard-delete
    precedent as api/content_assets.py."""
    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        if row.status not in ("ADMIN_REJECTED", "REJECTED"):
            return jsonify({"error": [f"only a rejected template can be deleted (status={row.status})"]}), 409
        db.delete(row)
        db.commit()
        return "", 204
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>/approve", methods=["POST"])
def approve_template(template_id):
    """Step 9.6 -- an admin approving an AI-authored DRAFT. This is the ONE moment an
    AI-drafted template's wording actually reaches Meta -- same real-external-action
    caution as create_template() above (irreversible, affects the WABA's standing), so
    the frontend must confirm before calling this exactly like it does for a direct
    admin submission."""
    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        if row.status != "DRAFT":
            return jsonify({"error": [f"template is {row.status}, not DRAFT -- nothing to approve"]}), 409
        try:
            row = approve_draft_and_submit(db, row)
        except Exception as exc:  # noqa: BLE001 - a real API failure must surface, not 500 silently
            return jsonify({"error": [f"Meta submission failed: {exc}"]}), 502
        product_titles = _product_titles_for(db, row)
        return jsonify(_serialize(row, product_titles))
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>/reject", methods=["POST"])
def reject_template(template_id):
    """Step 9.6 -- an admin rejecting an AI-authored DRAFT before it ever reaches Meta.
    No real external action here at all -- purely a local status change."""
    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        if row.status != "DRAFT":
            return jsonify({"error": [f"template is {row.status}, not DRAFT -- nothing to reject"]}), 409
        row = reject_draft(db, row)
        product_titles = _product_titles_for(db, row)
        return jsonify(_serialize(row, product_titles))
    finally:
        db.close()


@whatsapp_templates_bp.route("/propose", methods=["POST"])
def propose_template():
    """Step 9.6 sub-step 4 -- manual trigger. An admin asks the AI to look at REAL
    signals (variant performance, follow-up template coverage) and, only if a real one
    exists, draft + QC-review a new candidate, storing it as DRAFT. No real Meta call
    happens here at all -- this endpoint can never mutate anything about the real WABA,
    so unlike create_template()/approve_template() it needs no extra confirmation.

    Optional body {"purpose": "FIRST_TOUCH"|"FOLLOW_UP", "followup_level": 1|2|3,
    "campaign_id": "...", "with_button": true|false}
    (Step 9.6 follow-up; level added Phase 13 Step 13.2) -- the admin picks which one
    they want, scoping the SEARCH for a real signal to that purpose (and, for FOLLOW_UP,
    that exact level -- required, since each level is its own independent coverage gap
    now). This never forces a fabricated need: if nothing real qualifies, the honest
    "nothing to propose" response is expected and valid.

    `campaign_id` (2026-09-09, real user ask): when a specific campaign's own Daily Review
    is the one asking (DailyReviewPanel's "Ask AI for a template for this product"), this
    becomes a MANDATORY, human-requested ask -- once a real signal/gap is confirmed (the
    check above is unchanged and can still honestly say "nothing to propose" when no real
    gap exists), the resulting draft is never silently withheld over QC's own judgment call
    (see propose_new_template's `guarantee` mode) and is grounded in this campaign's own
    real strategy_angle. `with_button` asks for a real call-to-action button, resolved from
    this product's own content assets, never invented.
    """
    data = request.get_json(silent=True) or {}
    requested_purpose = data.get("purpose")
    if requested_purpose not in (None, "FIRST_TOUCH", "FOLLOW_UP"):
        return jsonify({"error": [f"purpose must be one of {sorted(VALID_PURPOSES)}"]}), 422

    requested_level = data.get("followup_level")
    if requested_purpose == "FOLLOW_UP":
        if requested_level not in (1, 2, 3):
            return jsonify({"error": ["followup_level must be 1, 2, or 3 when purpose is FOLLOW_UP"]}), 422
    else:
        requested_level = None

    # 2026-09-08 -- a campaign's own Daily Review knows which product it's reviewing, and
    # can ask specifically "does THIS product have its own FIRST_TOUCH template" rather
    # than only the system-wide reply-rate/coverage checks below.
    requested_product_id = data.get("product_id")
    campaign_id = data.get("campaign_id")
    with_button = bool(data.get("with_button"))

    db = SessionLocal()
    try:
        campaign_strategy_angle = None
        guarantee = False
        if campaign_id:
            campaign = db.get(Campaign, campaign_id)
            if not campaign:
                return jsonify({"error": ["campaign not found"]}), 404
            guarantee = True
            campaign_strategy_angle = campaign.strategy_angle
            requested_product_id = requested_product_id or campaign.product_id

        signal = find_template_improvement_reason(db, purpose=requested_purpose, followup_level=requested_level,
                                                   product_id=requested_product_id, want_button=with_button)
        if not signal:
            # 2026-09-09, real user ask: a human checked "Include a button" for a product
            # that already has its own approved template, but no real demo/video asset
            # exists yet for it -- asking the AI again would just repeat the same honest
            # "no button" outcome, so say exactly why instead of the generic decline.
            if with_button and requested_product_id:
                existing = get_approved_first_touch_template(db, product_id=requested_product_id)
                if existing is not None and not existing.button_url and not _resolve_button_asset(db, requested_product_id):
                    return jsonify({
                        "proposed": False,
                        "message": "This product has no real demo/video link set up yet, so a button "
                                   "can't be added -- add one under Products -> Content Library first, "
                                   "then ask again.",
                    })
            return jsonify({
                "proposed": False,
                "message": (
                    f"No real underperformance signal or coverage gap found for "
                    f"{requested_purpose}" +
                    (f" Level {requested_level}" if requested_level else "") +
                    " right now." if requested_purpose else
                    "No real underperformance signal or coverage gap found right now."
                ),
            })
        reason, context, purpose, product_id, followup_level = signal
        row = propose_new_template(db, reason, context, purpose, product_id, followup_level=followup_level,
                                   campaign_strategy_angle=campaign_strategy_angle, want_button=with_button,
                                   guarantee=guarantee)
        if not row:
            return jsonify({
                "proposed": False,
                "message": "The AI declined to draft anything for this -- see the audit trail "
                           "(agent_events) for details.",
                "reason": reason,
            })
        product_titles = _product_titles_for(db, row)
        return jsonify({"proposed": True, "template": _serialize(row, product_titles)}), 201
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>/revise", methods=["POST"])
def revise_template(template_id):
    """2026-09-09, real user ask: a human reviewing an AI-drafted template can give
    feedback and get a revised candidate, same conversational pattern already used for
    outreach/kickoff draft revisions. No real Meta call here -- still just a DRAFT.

    Body {"instruction": "...", "with_button": true|false} -- `with_button` is optional
    and tri-state: omitted keeps the template's current button as-is, true/false explicitly
    adds/removes one.
    """
    data = request.get_json(silent=True) or {}
    instruction = (data.get("instruction") or "").strip()
    if not instruction:
        return jsonify({"error": ["instruction is required"]}), 422
    want_button = data.get("with_button") if "with_button" in data else None

    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        if row.status != "DRAFT":
            return jsonify({"error": [f"template is {row.status}, not DRAFT -- nothing to revise"]}), 409
        try:
            row = revise_draft_template(db, row, instruction, want_button=want_button)
        except RuntimeError as exc:
            return jsonify({"error": [str(exc)]}), 502
        product_titles = _product_titles_for(db, row)
        return jsonify(_serialize(row, product_titles))
    finally:
        db.close()


@whatsapp_templates_bp.route("/<template_id>/refresh", methods=["POST"])
def refresh_template(template_id):
    """Manual, on-demand poll of this ONE template's real Meta-side status -- the
    scheduler also polls all PENDING templates periodically (jobs/discovery_scheduler.py),
    this is for "check right now" from the dashboard."""
    db = SessionLocal()
    try:
        row = db.get(WhatsappTemplate, template_id)
        if not row:
            return jsonify({"error": "template not found"}), 404
        changed = poll_template_status(db, row)
        db.refresh(row)
        product_titles = _product_titles_for(db, row)
        return jsonify({"changed": changed, "template": _serialize(row, product_titles)})
    finally:
        db.close()
