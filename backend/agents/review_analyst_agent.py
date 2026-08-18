from __future__ import annotations
from __future__ import annotations
"""Review & Weakness Detection Agent (MASTER §6 / Intelligence PRD §2.1.E).

Turns public-web text snippets about a business into structured pain-point codes an
outreach agent can later open a message with. Snippets are NOT guaranteed to contain
genuine review text -- verified live that only about 1 in 3 sampled businesses had
anything real indexed at all -- so this must degrade to "no pain points found" cleanly,
never force one into existence.
"""
import json

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import REVIEW_ANALYST_SYSTEM_PROMPT


def _clamp(value, lo, hi, default):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def analyze_reviews(db, lead_id, company_name, snippets: list[str]):
    """Returns (result_dict, outcome). result_dict always has the same shape, even on
    empty input or a total LLM failure, so callers never special-case "the agent broke".
    """
    if not snippets:
        result = {"pain_points": [], "sentiment_score": 0.0, "confidence": 0.0}
        log_agent_event(db, "REVIEW", lead_id, "ANALYZE_REVIEWS", 0.0, "LOW", "NO_INPUT",
                        payload={"snippet_count": 0})
        return result, "NO_INPUT"

    prompt = REVIEW_ANALYST_SYSTEM_PROMPT + f"""
COMPANY: {company_name}
SNIPPETS:
{json.dumps(snippets, ensure_ascii=False, indent=2)}
"""
    try:
        data = call_json(prompt, temperature=0.2)
    except LLMError as exc:
        result = {"pain_points": [], "sentiment_score": 0.0, "confidence": 0.0}
        log_agent_event(db, "REVIEW", lead_id, "ANALYZE_REVIEWS", 0.0, "LOW", "LLM_FAILED",
                        payload={"snippet_count": len(snippets), "error": str(exc)})
        return result, "LLM_FAILED"

    # never trust blindly -- coerce anything malformed into a safe shape rather than
    # crash the job or silently store garbage
    raw_points = data.get("pain_points")
    cleaned_points = []
    if isinstance(raw_points, list):
        for p in raw_points:
            if not isinstance(p, dict) or not p.get("code"):
                continue
            cleaned_points.append({
                "code": str(p["code"])[:64],
                "evidence_quote": str(p.get("evidence_quote", ""))[:500],
                "severity_0_1": _clamp(p.get("severity_0_1"), 0.0, 1.0, 0.5),
            })

    result = {
        "pain_points": cleaned_points,
        "sentiment_score": _clamp(data.get("sentiment_score"), -1.0, 1.0, 0.0),
        "confidence": _clamp(data.get("confidence"), 0.0, 1.0, 0.0),
    }

    log_agent_event(db, "REVIEW", lead_id, "ANALYZE_REVIEWS", result["confidence"], "LOW",
                    "ANALYZED", payload={"snippet_count": len(snippets),
                                        "pain_point_count": len(cleaned_points)})
    return result, "ANALYZED"
