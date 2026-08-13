"""Quality Controller & Compliance Supervisor (MASTER §6 / Intelligence PRD §9.1).

Absolute veto over any outbound message -- MASTER's non-negotiable rule, and the top of
the governance hierarchy right after the CEO agent (§8.7): a QC rejection cannot be
overridden by any other agent's rank.
"""
import json

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import QUALITY_CONTROLLER_SYSTEM_PROMPT


def review_draft(db, lead_id, draft: dict, pain_points: list) -> dict:
    """Always returns {approved, confidence_score, rejection_reasons, suggested_corrections}.

    Fails CLOSED: if the QC call itself fails (LLM error, malformed response), that is
    NOT treated as approval -- a QC that can't run must never be mistaken for a QC that
    said yes. `approved` is only ever True when the model explicitly returned `true`,
    not merely a truthy value (defends against e.g. a stray "approved": "yes" string).
    """
    prompt = QUALITY_CONTROLLER_SYSTEM_PROMPT + f"""
DRAFT: {json.dumps(draft, ensure_ascii=False)}
VERIFIED_PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
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
