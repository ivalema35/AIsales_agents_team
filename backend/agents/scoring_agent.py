"""Lead Scoring & Fit Agent (MASTER §6 / §4.2). The first place a real SCORING
confidence value actually drives Decision Engine routing: <0.70 -> a human looks at it,
0.70-0.85 -> QC reviews it, >=0.85 -> the lead advances on its own.
"""
from __future__ import annotations
import json

from cognition.agent_events import log_agent_event
from cognition.decision_engine import route_action
from cognition.llm_client import call_json, LLMError
from cognition.prompts import SCORING_AGENT_SYSTEM_PROMPT

VALID_TIERS = {"HOT", "WARM", "COLD"}


def score_lead(db, lead_id, product_brief: dict, lead_profile: dict, pain_points: list):
    prompt = SCORING_AGENT_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.2)
    except LLMError as exc:
        result = {"score": 0, "tier": "COLD", "scoring_breakdown": {},
                  "justification": "scoring failed", "confidence": 0.0}
        log_agent_event(db, "SCORING", lead_id, "SCORE", 0.0, "LOW", "LLM_FAILED",
                        payload={"error": str(exc)})
        return result, "HUMAN_ESCALATION"

    # never trust blindly -- clamp/coerce every field the MASTER blueprint calls out
    try:
        score = max(0, min(100, int(data.get("score"))))
    except (TypeError, ValueError):
        score = 0

    tier = data.get("tier")
    if tier not in VALID_TIERS:
        tier = "COLD"

    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    breakdown = data.get("scoring_breakdown")
    if not isinstance(breakdown, dict):
        breakdown = {}

    justification = str(data.get("justification", ""))[:300]

    result = {
        "score": score,
        "tier": tier,
        "scoring_breakdown": breakdown,
        "justification": justification,
        "confidence": confidence,
    }

    route = route_action("SCORING", confidence)
    log_agent_event(db, "SCORING", lead_id, "SCORE", confidence, "LOW", route,
                    payload={"score": score, "tier": tier})
    return result, route
