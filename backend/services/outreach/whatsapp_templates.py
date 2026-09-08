"""WhatsApp template library -- MASTER's non-negotiable rule (first-contact only via a
pre-approved template) means the Outreach Agent can't freely draft WhatsApp copy the way
it does for email. Instead it picks the best-fitting ALREADY-APPROVED template from this
library and fills in its variables deterministically.

This library starts small and is meant to grow over time. Per the plan agreed with the
user: rather than creating a new template per lead (impossible -- Meta approval isn't
instant, and submitting too many templates too fast risks looking spammy to Meta), the
system maintains a small, curated library. New entries get added here once a proposed
template clears Meta's approval -- today that's done ad hoc (created live via the API,
see tracker.md Step 3.4); a periodic "propose a new template when an existing one is
stale or a pain-point category has no good match" process is a natural extension once
per-template performance tracking exists (campaign_variants table), not built yet.
"""
from __future__ import annotations

# key -> a lead-facing template. "GENERIC" is a last-resort fallback, kept only for the
# case where PAIN_POINT_HOOK somehow isn't APPROVED -- select_template() below no longer
# reaches for it just because a lead has no pain point (2026-09-08, real typo-ridden sends).
TEMPLATE_LIBRARY = {
    "GENERIC": {
        "name": "marketing_gen",
        "language": "en",
        "variables": ["contact_name"],  # {{1}}
        # Phase 14 Step 14.2 -- the REAL approved wording, fetched directly from Meta
        # (fetch_template_wording()), kept verbatim including its own real typos. Needed
        # so the conversation view can show the real filled-in text a lead actually
        # received, not just the template name -- TEMPLATE_LIBRARY entries (unlike
        # WhatsappTemplate DB rows, which already store their own real body_text) never
        # had this recorded locally before.
        "body_text": "hello {{1}},  we hear about you. make your buisness simpale.",
    },
    # Submitted live via the Create Template API (2026-08-13), Meta approval confirmed
    # APPROVED on 2026-08-13 -- this stays the real, button-less, product-agnostic
    # fallback for select_template() below.
    #
    # 2026-08-25 correction: a button-carrying sibling of this template
    # (ivinfotech_pain_point_outreach_btn, same approved body text + a real demo link)
    # was briefly wired in here as a second TEMPLATE_LIBRARY entry and preferred by
    # default -- real bug, caught by the operator ("agar kisi product me demo url na ho
    # to?"): a button baked into ONE shared template at Meta-approval time would show
    # EVERY product's leads the same one product's real demo link, since TEMPLATE_LIBRARY
    # has no product concept at all. Reverted: that button template now lives as a real,
    # PRODUCT-SCOPED row in the `whatsapp_templates` DB table instead (get_approved_
    # first_touch_template() in whatsapp_template_service.py, same tiered product-first
    # lookup already proven for follow-up templates) -- checked BEFORE this hardcoded
    # library, real per-product buttons never end up shared across unrelated products.
    "PAIN_POINT_HOOK": {
        "name": "ivinfotech_pain_point_outreach",
        "language": "en",
        "variables": ["company_name", "pain_point_phrase"],  # {{1}}, {{2}}
        "status": "APPROVED",
        "body_text": ("Hi {{1}}, we noticed {{2}} - this is exactly the kind of problem "
                     "IVinfotech's software and IT solutions are built to fix. Open to a quick chat?"),
    },
}

# Maps a Review Analyst weakness code (free-form -- see cognition/prompts.py's
# REVIEW_ANALYST_SYSTEM_PROMPT) to a template library key. Empty today: codes are
# freely invented per-lead by the LLM (no fixed list), so an exact code->key map isn't
# viable yet. PAIN_POINT_HOOK's wording is category-agnostic (it just quotes whatever
# pain point was found), so select_template() below uses it for ANY known pain point
# rather than waiting for a per-code match. This map stays reserved for a future
# category-SPECIFIC template (e.g. a template phrased only for staffing issues).
PAIN_POINT_CATEGORY_MAP: dict = {}


def select_template(pain_points: list) -> str:
    """Returns a TEMPLATE_LIBRARY key. Prefers a category-specific, APPROVED template
    matched via PAIN_POINT_CATEGORY_MAP; then the category-agnostic PAIN_POINT_HOOK
    whenever it's APPROVED (its own `_fill_value("pain_point_phrase", ...)` already
    degrades gracefully to "some recent challenges" with no pain points at all, so it
    doesn't need a real pain point to be usable); GENERIC is the last-resort fallback,
    used only if PAIN_POINT_HOOK itself somehow isn't APPROVED.

    2026-09-08, real live case: GENERIC's own wording ("hello {{1}}, we hear about you.
    make your buisness simpale.") has real typos and went out to 18 real businesses on
    a campaign whose leads mostly had no pain points at all, because the old logic only
    reached for PAIN_POINT_HOOK when `pain_points` was non-empty. PAIN_POINT_HOOK reads
    fine either way, so it's now the default whenever it's approved -- GENERIC should
    almost never fire in practice.
    """
    for point in pain_points or []:
        code = point.get("code") if isinstance(point, dict) else None
        key = PAIN_POINT_CATEGORY_MAP.get(code)
        if key and TEMPLATE_LIBRARY.get(key, {}).get("status") == "APPROVED":
            return key

    if TEMPLATE_LIBRARY.get("PAIN_POINT_HOOK", {}).get("status") == "APPROVED":
        return "PAIN_POINT_HOOK"

    return "GENERIC"


def interpolate_template(body_text: str, variables: list) -> str:
    """Phase 14 Step 14.2 -- substitutes Meta's own {{1}}, {{2}}, ... placeholders with
    the real values actually sent, so a stored/displayed message shows what a lead
    genuinely received rather than a template name + a raw variable list. Never fails on
    a missing/extra value (a placeholder with nothing to fill it just stays literal,
    an extra value is silently unused) -- display-only, must never raise on a real,
    already-sent historical row whose shape drifted from the current template.
    """
    text = body_text or ""
    for i, value in enumerate(variables or [], start=1):
        text = text.replace(f"{{{{{i}}}}}", str(value))
    return text


def _fill_value(var_name: str, lead_profile: dict, pain_points: list) -> str:
    if var_name == "contact_name":
        return lead_profile.get("contact_person_name") or lead_profile.get("company_name") or "there"
    if var_name == "company_name":
        return lead_profile.get("company_name") or "there"
    if var_name == "pain_point_phrase":
        # 2026-09-07, real bug found live: `evidence_quote` is an internal citation (the
        # literal review text proving this pain point is real) -- inserting it verbatim
        # into a real WhatsApp message sent it back at the business as an awkward, blaming
        # direct quote ("we noticed Manager's bad response"). `customer_facing_phrase`
        # (review_analyst_agent.py) is the tactfully-rephrased version meant for exactly
        # this. Falls back to evidence_quote only for pain points scored before this field
        # existed -- never the other way around.
        point = pain_points[0] if pain_points else {}
        phrase = point.get("customer_facing_phrase") or point.get("evidence_quote") or ""
        return phrase[:80] if phrase else "some recent challenges"
    return ""


def fill_variables(template_key: str, lead_profile: dict, pain_points: list) -> list:
    """Deterministic filling for known simple fields -- WhatsApp template variables are
    plain substitutions into Meta-approved fixed wording, not open-ended generation, so
    this doesn't need (and per MASTER's rules, shouldn't invent via) an LLM call.
    """
    spec = TEMPLATE_LIBRARY[template_key]
    return [_fill_value(var, lead_profile, pain_points) for var in spec["variables"]]


def fill_variables_for_labels(variable_labels: list, lead_profile: dict, pain_points: list) -> list:
    """Phase 9 Step 9.5 -- same deterministic filling as fill_variables(), for a
    DB-registered WhatsappTemplate row (services/outreach/whatsapp_template_service.py)
    instead of a hardcoded TEMPLATE_LIBRARY entry. Uses the exact same recognized
    variable-name vocabulary (contact_name/company_name/pain_point_phrase), so an admin
    composing a template from the dashboard uses the same building blocks this file
    already understands, not a new naming scheme.
    """
    return [_fill_value(var, lead_profile, pain_points) for var in variable_labels]


def validate_variables(values: list) -> bool:
    """Sanity-check filled variables before send. The template BODY is already
    Meta-approved and fixed, so this isn't a creative-writing QC review like email's --
    it just guards against sending an empty/garbage/placeholder variable value.
    """
    return all(v and str(v).strip() and str(v).strip().lower() != "none" for v in values)
