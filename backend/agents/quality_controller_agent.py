"""Quality Controller & Compliance Supervisor (MASTER §6 / Intelligence PRD §9.1).

Absolute veto over any outbound message -- MASTER's non-negotiable rule, and the top of
the governance hierarchy right after the CEO agent (§8.7): a QC rejection cannot be
overridden by any other agent's rank.
"""
from __future__ import annotations
import json

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import QUALITY_CONTROLLER_SYSTEM_PROMPT, TEMPLATE_QC_SYSTEM_PROMPT


def review_draft(db, lead_id, draft: dict, pain_points: list, product_brief: dict | None = None,
                 is_followup: bool = False) -> dict:
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
    """
    prompt = QUALITY_CONTROLLER_SYSTEM_PROMPT + f"""
DRAFT: {json.dumps(draft, ensure_ascii=False)}
VERIFIED_PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
PRODUCT_BRIEF (the ground truth for judging capability claims -- a claim consistent with
this is NOT hallucination, even if worded differently than the brief itself):
{json.dumps(product_brief or {}, ensure_ascii=False)}
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
