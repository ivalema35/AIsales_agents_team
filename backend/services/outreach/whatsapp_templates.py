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

# key -> a lead-facing template. "GENERIC" is the always-available fallback used when no
# pain point is known, or no category-specific template exists (yet) for the one found.
TEMPLATE_LIBRARY = {
    "GENERIC": {
        "name": "marketing_gen",
        "language": "en",
        "variables": ["contact_name"],  # {{1}}
    },
    # Submitted live via the Create Template API (2026-08-13), Meta approval confirmed
    # APPROVED on 2026-08-13. Superseded 2026-08-25 by "..._btn" below (same real
    # approved wording, plus a real demo button) -- kept here, not deleted, only because
    # its own real Meta approval still exists; select_template() never picks it anymore.
    "PAIN_POINT_HOOK": {
        "name": "ivinfotech_pain_point_outreach",
        "language": "en",
        "variables": ["company_name", "pain_point_phrase"],  # {{1}}, {{2}}
        "status": "APPROVED",
    },
    # 2026-08-25 -- same real approved body text as PAIN_POINT_HOOK above, now with a
    # real, static demo button (https://ivinfotech.com), mirroring the button just added
    # to the Level 1 follow-up template (whatsapp_template_service.py). A static URL
    # button needs no {{n}} suffix/no extra send-time parameter -- Meta includes it
    # automatically for every send of this approved template, so send_template_message()
    # needed zero changes to pick this up.
    "PAIN_POINT_HOOK_BTN": {
        "name": "ivinfotech_pain_point_outreach_btn",
        "language": "en",
        "variables": ["company_name", "pain_point_phrase"],  # {{1}}, {{2}}
        "status": "APPROVED",
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
    matched via PAIN_POINT_CATEGORY_MAP; then the category-agnostic PAIN_POINT_HOOK if
    any pain point is known and it's APPROVED; falls back to GENERIC otherwise. Never
    blocks outreach just because no perfect template exists yet -- a generic touch beats
    no touch.
    """
    for point in pain_points or []:
        code = point.get("code") if isinstance(point, dict) else None
        key = PAIN_POINT_CATEGORY_MAP.get(code)
        if key and TEMPLATE_LIBRARY.get(key, {}).get("status") == "APPROVED":
            return key

    # PAIN_POINT_HOOK_BTN (2026-08-25) supersedes the plain PAIN_POINT_HOOK -- same real
    # approved wording, now with a real demo button. Preferred first; PAIN_POINT_HOOK
    # stays as a real fallback only if the button variant's own APPROVED status ever
    # lapses (Meta can revoke/expire a template), never deleted outright.
    if pain_points and TEMPLATE_LIBRARY.get("PAIN_POINT_HOOK_BTN", {}).get("status") == "APPROVED":
        return "PAIN_POINT_HOOK_BTN"
    if pain_points and TEMPLATE_LIBRARY.get("PAIN_POINT_HOOK", {}).get("status") == "APPROVED":
        return "PAIN_POINT_HOOK"

    return "GENERIC"


def _fill_value(var_name: str, lead_profile: dict, pain_points: list) -> str:
    if var_name == "contact_name":
        return lead_profile.get("contact_person_name") or lead_profile.get("company_name") or "there"
    if var_name == "company_name":
        return lead_profile.get("company_name") or "there"
    if var_name == "pain_point_phrase":
        quote = pain_points[0].get("evidence_quote") if pain_points else ""
        return quote[:80] if quote else "some recent challenges"
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
