"""Shared pain-point confidence filter (2026-09-08).

Every place that hands a lead's real, review-extracted pain points to an LLM call that
either DRAFTS or JUDGES outbound content (fresh touch-1, follow-ups, an inbound auto-reply,
QC's review of any of those) reads through here first, so every one of them works from the
identical, already-vetted set -- QUALITY_CONTROLLER_SYSTEM_PROMPT is explicitly told it can
trust that whatever it's shown already cleared this bar, instead of having to judge
"is this specific claim confidently enough evidenced" itself on every call. Real live case
(2026-09-08): a QC rejection loop oscillated -- fixing "too generic" by adding a real but
weakly-evidenced pain point ("a few reviewers" mentioned it, severity 0.57) then got
rejected as "overstated" -- because a thin signal reached the drafting agent at all. Cutting
it at the source removes the ambiguity for both agents, rather than asking either one to
calibrate hedge-language nuance on every call.

review_analyst_agent.py itself is UNCHANGED -- the full extracted list, weak signals
included, still gets stored (LeadReviewInsight.pain_points_extracted); this only filters
what's handed onward for an outbound message.
"""
from __future__ import annotations

CONFIDENT_PAIN_POINT_SEVERITY = 0.65


def confident_pain_points(pain_points: list) -> list:
    """Pain points strong enough to state as fact in an outbound message. Never returns an
    empty list when real pain points exist at all -- if none clear the bar, the single
    highest-severity one is kept (some real signal beats none), letting the drafting
    prompt's own hedging guidance (GUARDRAIL_PREAMBLE) phrase it appropriately softly."""
    if not pain_points:
        return []
    confident = [p for p in pain_points if float(p.get("severity_0_1") or 0) >= CONFIDENT_PAIN_POINT_SEVERITY]
    if confident:
        return confident
    return [max(pain_points, key=lambda p: float(p.get("severity_0_1") or 0))]
