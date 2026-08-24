"""Quality Controller & Compliance Supervisor (MASTER §6 / Intelligence PRD §9.1).

Absolute veto over any outbound message -- MASTER's non-negotiable rule, and the top of
the governance hierarchy right after the CEO agent (§8.7): a QC rejection cannot be
overridden by any other agent's rank.
"""
from __future__ import annotations
import json

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import (
    QUALITY_CONTROLLER_SYSTEM_PROMPT, TEMPLATE_QC_SYSTEM_PROMPT, SOCIAL_QC_SYSTEM_PROMPT,
)



# Which real asset TYPE a format section's own wording is calling for -- deliberately
# keyword-based, not LLM-judged (the whole point is a check that doesn't depend on a
# model reliably noticing its own omission). A section saying "video url" means the real
# VIDEO_URL asset specifically, not "any asset will do" -- a product with BOTH a demo
# link and a video available (real case, 2026-08-21) needs the format's own wording
# respected, not an arbitrary pick between them.
_SECTION_ASSET_TYPE_KEYWORDS = {
    "DEMO_URL": ("demo",),
    "VIDEO_URL": ("video",),
    "CASE_STUDY": ("case study", "case-study"),
    "TESTIMONIAL": ("testimonial",),
}


def _required_asset_types(format_sections):
    """The real asset TYPES the format's own wording actually names -- a format that
    never mentions an asset-like word requires nothing."""
    required = set()
    for section in format_sections or []:
        section_lower = str(section).lower()
        for asset_type, keywords in _SECTION_ASSET_TYPE_KEYWORDS.items():
            if any(kw in section_lower for kw in keywords):
                required.add(asset_type)
    return required


def _missing_required_asset(body: str, format_sections, content_assets):
    """Deterministic backstop, not just a prompt instruction (2026-08-21, found live --
    a real production email's admin-set format called for a "demo url" section, a real
    matching DEMO_URL asset was available and correctly passed to the drafting prompt,
    yet the real LLM output omitted it anyway, twice, even after the prompt was already
    strengthened to say the asset MUST be included). Same "never trust blindly, add a
    deterministic check" posture as outreach_agent.py's own _strip_signature regex.

    Type-aware (2026-08-21 follow-up): only checks for the SPECIFIC asset type each
    format section actually names -- "video url" requires the real VIDEO_URL asset, not
    just any real link. A required type with no real asset of that type available is
    NOT flagged (nothing to include, correctly omitted per the drafting prompt's own
    carve-out) -- this only fires when a real, available, matching-type asset exists and
    genuinely isn't in the body.

    Returns the real asset value that should have been included, or None if compliant.
    """
    required_types = _required_asset_types(format_sections)
    if not required_types or not content_assets:
        return None
    body_text = body or ""
    assets_by_type = {}
    for asset in content_assets:
        if isinstance(asset, dict) and asset.get("asset_type") in required_types:
            assets_by_type.setdefault(asset["asset_type"], asset.get("value"))
    for asset_type in required_types:
        value = assets_by_type.get(asset_type)
        if not value:
            continue  # no real asset of this exact type available -- omitting it is correct
        if value not in body_text:
            return value
    return None


def review_draft(db, lead_id, draft: dict, pain_points: list, product_brief: dict | None = None,
                 is_followup: bool = False, format_sections=None, content_assets=None) -> dict:
    """Always returns {approved, confidence_score, rejection_reasons, suggested_corrections}.

    Fails CLOSED: if the QC call itself fails (LLM error, malformed response), that is
    NOT treated as approval -- a QC that can't run must never be mistaken for a QC that
    said yes. `approved` is only ever True when the model explicitly returned `true`,
    not merely a truthy value (defends against e.g. a stray "approved": "yes" string).

    `product_brief` is what QC checks capability claims against for the zero-hallucination
    rule -- without it, QC has no ground truth to tell a real capability from an invented
    one, and (found live, 2026-08-13) ends up flagging genuine, product-description-backed
    claims as "unsupported" simply because it was never shown the product at all.

    `is_followup` (Phase 9 Step 9.3): a real conflict, found live testing the follow-up
    sequencer -- this prompt's own existing specificity rule ("clearly and specifically
    tie to a verified pain point") was BUILT for a first-touch pitch, and correctly
    caught a deliberately brief, low-pressure follow-up nudge as failing that same bar,
    even though the follow-up isn't trying to re-pitch. Same conflict shape as the
    escalation-reply carve-out already in the prompt below for its own closing line --
    an old rule and a new, legitimate requirement disagreeing, not a bug in either.

    `format_sections`/`content_assets` (2026-08-21 follow-up): when the admin's format
    calls for a real content asset (a demo link, etc.) and one was genuinely available,
    a real production draft still dropped it -- twice, even after the drafting prompt
    was strengthened. This checks that deterministically, before ever asking the LLM,
    and rejects (with the missing value named in suggested_corrections, feeding the
    existing retry loop) rather than hoping the model notices its own omission.

    A `draft` carrying `sections` (Phase 11 Step 11.6) gets an extra prompt block and two
    extra structural checks. Found live on the first real structured send: QC only ever
    sees the flat-text preview of the sections, in which the CTA's closing line sits at
    the end and reads exactly like an agent-written sign-off -- so check (d) rejected two
    consecutive drafts for "footer/signature-style closing content" that was in fact a
    defined template section rendered in its own panel. QC was applying a correct rule to
    a shape it had never been told about.
    """
    missing_asset = _missing_required_asset(draft.get("body", ""), format_sections, content_assets)
    if missing_asset:
        reasons = [f"The format calls for a content asset (e.g. a demo link) but the draft "
                  f"doesn't include one of the real available ones."]
        log_agent_event(db, "QC", lead_id, "REVIEW_DRAFT", 0.0, "HIGH", "REJECTED",
                        payload={"reasons": reasons, "check": "missing_required_asset"})
        return {"approved": False, "confidence_score": 0.0, "rejection_reasons": reasons,
                "suggested_corrections": f"Include this exact real link/value in the email: {missing_asset}"}

    # A structured draft carries BOTH `sections` (the real source of truth) and `body`
    # (the same content, pre-flattened to plain text, kept only so non-QC consumers like
    # outreach_logs need no change). Sending both to QC put the identical content in front
    # of it twice, in two different shapes, and it kept reading the second copy as
    # something extra to police -- "duplicated section-like lines", "text outside the
    # approved sections" -- rejecting real, already-correct drafts for content that was
    # never actually duplicated, just redundantly represented. Found live, several
    # consecutive real rejections in a row, all citing this same confusion. QC now never
    # sees `body` at all when `sections` is present -- one representation, nothing to
    # cross-check against itself.
    if draft.get("sections"):
        # Same fix, same reasoning, applied again: `named_product` (the CROSS_SELL
        # section's grounding brief) gets shown separately as NAMED_PRODUCT_BRIEF below --
        # leaving it inline here too would be the identical redundant-representation
        # confusion `body` caused, just on a smaller scale.
        draft_for_qc = {
            k: v for k, v in draft.items() if k != "body"
        }
        draft_for_qc["sections"] = [
            {k: v for k, v in s.items() if k != "named_product"} for s in draft["sections"]
        ]
    else:
        draft_for_qc = draft

    prompt = QUALITY_CONTROLLER_SYSTEM_PROMPT + f"""
DRAFT: {json.dumps(draft_for_qc, ensure_ascii=False)}
VERIFIED_PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
PRODUCT_BRIEF (the ground truth for judging capability claims -- a claim consistent with
this is NOT hallucination, even if worded differently than the brief itself):
{json.dumps(product_brief or {}, ensure_ascii=False)}
"""
    if content_assets:
        prompt += f"""
APPROVED_CONTENT_ASSETS (2026-08-21 follow-up -- found live: without this block QC had
no way to tell a real, pre-approved link from a hallucinated one, and wrongly rejected
genuine demo/video links as "unauthorized external URLs"). Any URL in the draft that
exactly matches one of these "value" fields is a REAL, admin-approved asset -- NOT an
unsupported claim or an unauthorized link, and must never be rejected on that basis
alone. Only flag a URL if it does NOT match any of these:
{json.dumps(content_assets, ensure_ascii=False)}
"""
    if draft.get("sections"):
        prompt += f"""
STRUCTURED_DRAFT (Phase 11 Step 11.6). This draft is NOT free-form prose. `DRAFT.sections`
below is the complete and ONLY content that will ever be sent -- the system assembled it
from typed sections and will RENDER each one itself, as a separate visual block, with
proper spacing between them. There is no other, longer version of this email anywhere;
what you are reading in `sections` is everything, review it exactly as given, and do not
infer or assume any additional prose surrounds it. The section list, in order:
{json.dumps([s.get("type") for s in draft["sections"]], ensure_ascii=False)}

Three consequences for your checks, all of them carve-outs, not relaxations:
(1) The CTA section's headline and subtext are a DEFINED PART OF THE TEMPLATE, rendered
    inside their own panel. They are not an agent-written sign-off or signature and must
    NOT be rejected under check (d). A closing line offering to follow up or share a next
    step belongs to that section by design.
(2) The compliance footer, physical address and unsubscribe link are appended by the
    system AFTER this review. Their absence here is correct, not a defect -- and the
    draft containing its own would still be a real violation of check (d).
(3) Every URL in a VIDEO/CTA/CASE_STUDY section was inserted by the system from the
    approved asset list -- the agent is structurally unable to write a URL at all -- so a
    link in those sections is never a hallucinated one.

ALSO CHECK, in addition to (a)-(d): the sections are in a sensible order, and no section
is present but empty (a heading with nothing under it, a bullet list with no bullets).
"""
        cross_sell_section = next((s for s in draft["sections"] if s.get("type") == "CROSS_SELL"), None)
        if cross_sell_section:
            # `named_product` is the SPECIFIC product's real brief, resolved and attached
            # to this section already (outreach_agent.py's _assemble_sections) -- it is
            # mechanically guaranteed to be one of the admin's own pre-approved products,
            # so that part is never in question here. What genuinely needs real judgment,
            # and could not be checked in code, is whether the CAPABILITY this line claims
            # for that product is actually grounded in ITS OWN brief below (not the main
            # PRODUCT_BRIEF above -- a different product, a different ground truth).
            prompt += f"""
CROSS_SELL section (Phase 11 Step 11.5). A short, personalized line naming another real
service this company offers and tying it to one of this lead's own verified pain points.
The product it names is ALREADY mechanically verified, in code, to be one of the admin's
own pre-approved products -- never reject it for naming an unapproved service, and never
reject it under check (c) merely for naming a real product; that is a fact about this
company's catalogue, not an unsupported claim.

What you DO need to judge, using real reasoning: is every capability this line claims for
that product ACTUALLY STATED in that product's own real brief below (not invented, not
borrowed from the main PRODUCT_BRIEF above)? And does it genuinely tie to a real entry in
VERIFIED_PAIN_POINTS, not a vague, generic tie?

NAMED_PRODUCT_BRIEF (the ground truth for THIS section's capability claim only):
{json.dumps(cross_sell_section.get("named_product") or {}, ensure_ascii=False)}

REJECT this section specifically if: it claims a capability that product's own brief does
not support, it merely names the product with no real pain-point tie, it contains a link,
or it reads as a second pitch with its own call to action. Otherwise approve it.
"""
    if is_followup:
        prompt += """
THIS IS A FOLLOW-UP nudge to a lead who already received a full first-touch pitch and
hasn't replied. It is DELIBERATELY brief and does not need to re-state the pain point
with the same specificity you would require of a first-touch draft -- a light reference
to "the earlier note" or a general nudge is acceptable here. Still enforce every other
rule unchanged (no buzzwords, no unsupported claims, no fabricated timelines/pricing).
"""
    try:
        data = call_json(prompt, temperature=0.1)
    except LLMError as exc:
        log_agent_event(db, "QC", lead_id, "REVIEW_DRAFT", 0.0, "HIGH", "LLM_FAILED",
                        payload={"error": str(exc)})
        return {"approved": False, "confidence_score": 0.0,
                "rejection_reasons": ["QC agent unavailable -- failing closed, not sending"],
                "suggested_corrections": ""}

    approved = data.get("approved") is True
    try:
        confidence_score = max(0.0, min(1.0, float(data.get("confidence_score"))))
    except (TypeError, ValueError):
        confidence_score = 0.0

    reasons = data.get("rejection_reasons")
    if not isinstance(reasons, list):
        reasons = []
    reasons = [str(r)[:200] for r in reasons]
    corrections = str(data.get("suggested_corrections", ""))[:300]

    result = {"approved": approved, "confidence_score": confidence_score,
              "rejection_reasons": reasons, "suggested_corrections": corrections}

    log_agent_event(db, "QC", lead_id, "REVIEW_DRAFT", confidence_score, "HIGH",
                    "APPROVED" if approved else "REJECTED", payload={"reasons": reasons})
    return result


def review_template_draft(db, candidate: dict, reason: str, existing_templates: list[dict]) -> dict:
    """QC gate for an AI-drafted WhatsApp template candidate (Phase 9 Step 9.6 sub-step 3)
    -- runs BEFORE an admin ever sees the draft, so a bad candidate never even reaches
    the review queue. Same fails-CLOSED contract as review_draft(): a QC that can't run
    is never mistaken for a QC that said yes.

    Deliberately a separate prompt/function from review_draft() -- a template candidate
    has no lead-specific personalization to check against (it's reused across many real
    leads via {{n}} variables, unlike a one-off email draft) and no footer/signature
    concept; instead it's judged against Meta's real constraints, the stated drafting
    REASON, and distinctness from EXISTING_TEMPLATES.
    """
    prompt = TEMPLATE_QC_SYSTEM_PROMPT + f"""
CANDIDATE: {json.dumps(candidate, ensure_ascii=False)}
REASON: {reason}
EXISTING_TEMPLATES: {json.dumps(existing_templates, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.1)
    except LLMError as exc:
        log_agent_event(db, "QC", None, "REVIEW_TEMPLATE_DRAFT", 0.0, "HIGH", "LLM_FAILED",
                        payload={"error": str(exc)})
        return {"approved": False, "confidence_score": 0.0,
                "rejection_reasons": ["QC agent unavailable -- failing closed, not shown to admin"]}

    approved = data.get("approved") is True
    try:
        confidence_score = max(0.0, min(1.0, float(data.get("confidence_score"))))
    except (TypeError, ValueError):
        confidence_score = 0.0

    reasons = data.get("rejection_reasons")
    if not isinstance(reasons, list):
        reasons = []
    reasons = [str(r)[:200] for r in reasons]

    result = {"approved": approved, "confidence_score": confidence_score, "rejection_reasons": reasons}
    log_agent_event(db, "QC", None, "REVIEW_TEMPLATE_DRAFT", confidence_score, "HIGH",
                    "APPROVED" if approved else "REJECTED", payload={"reasons": reasons})
    return result


def review_social_draft(db, lead_id, draft: dict, pain_points: list, product_brief: dict | None = None) -> dict:
    """QC gate for a social-platform draft (Phase 10 Step 10.3 -- LinkedIn/Instagram/
    Facebook) before it's ever queued for a human to review and send manually. Deliberately
    a separate prompt from review_draft(), same reason review_template_draft() already is:
    there is no system-appended footer/unsubscribe concept on these platforms (a human
    sends this from their own real account), so platform-length/tone norms replace that
    check instead. Same fails-CLOSED contract as review_draft()/review_template_draft().
    """
    prompt = SOCIAL_QC_SYSTEM_PROMPT + f"""
DRAFT: {json.dumps(draft, ensure_ascii=False)}
VERIFIED_PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
PRODUCT_BRIEF: {json.dumps(product_brief or {}, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.1)
    except LLMError as exc:
        log_agent_event(db, "QC", lead_id, "REVIEW_SOCIAL_DRAFT", 0.0, "HIGH", "LLM_FAILED",
                        payload={"error": str(exc)})
        return {"approved": False, "confidence_score": 0.0,
                "rejection_reasons": ["QC agent unavailable -- failing closed, not queued"],
                "suggested_corrections": ""}

    approved = data.get("approved") is True
    try:
        confidence_score = max(0.0, min(1.0, float(data.get("confidence_score"))))
    except (TypeError, ValueError):
        confidence_score = 0.0

    reasons = data.get("rejection_reasons")
    if not isinstance(reasons, list):
        reasons = []
    reasons = [str(r)[:200] for r in reasons]
    corrections = str(data.get("suggested_corrections", ""))[:300]

    result = {"approved": approved, "confidence_score": confidence_score,
              "rejection_reasons": reasons, "suggested_corrections": corrections}
    log_agent_event(db, "QC", lead_id, "REVIEW_SOCIAL_DRAFT", confidence_score, "HIGH",
                    "APPROVED" if approved else "REJECTED", payload={"reasons": reasons})
    return result
