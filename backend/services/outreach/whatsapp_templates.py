from __future__ import annotations
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

# key -> a lead-facing template. "GENERIC" is the always-available fallback used when no
# pain point is known, or no category-specific template exists (yet) for the one found.
TEMPLATE_LIBRARY = {
    "GENERIC": {
        "name": "marketing_gen",
        "language": "en",
        "variables": ["contact_name"],  # {{1}}
    },
    # Submitted live via the Create Template API (2026-08-13), Meta approval confirmed
    # APPROVED on 2026-08-13 (GET /message_templates) -- live for use.
    "PAIN_POINT_HOOK": {
        "name": "ivinfotech_pain_point_outreach",
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

    if pain_points and TEMPLATE_LIBRARY.get("PAIN_POINT_HOOK", {}).get("status") == "APPROVED":
        return "PAIN_POINT_HOOK"

    return "GENERIC"


def fill_variables(template_key: str, lead_profile: dict, pain_points: list) -> list:
    """Deterministic filling for known simple fields -- WhatsApp template variables are
    plain substitutions into Meta-approved fixed wording, not open-ended generation, so
    this doesn't need (and per MASTER's rules, shouldn't invent via) an LLM call.
    """
    spec = TEMPLATE_LIBRARY[template_key]
    values = []
    for var in spec["variables"]:
        if var == "contact_name":
            values.append(lead_profile.get("contact_person_name") or lead_profile.get("company_name") or "there")
        elif var == "company_name":
            values.append(lead_profile.get("company_name") or "there")
        elif var == "pain_point_phrase":
            quote = pain_points[0].get("evidence_quote") if pain_points else ""
            values.append(quote[:80] if quote else "some recent challenges")
        else:
            values.append("")
    return values


def validate_variables(values: list) -> bool:
    """Sanity-check filled variables before send. The template BODY is already
    Meta-approved and fixed, so this isn't a creative-writing QC review like email's --
    it just guards against sending an empty/garbage/placeholder variable value.
    """
    return all(v and str(v).strip() and str(v).strip().lower() != "none" for v in values)
