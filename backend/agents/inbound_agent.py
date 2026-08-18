from __future__ import annotations
from __future__ import annotations
"""Inbound Reply Intent Classifier (MASTER §6 / Phase 4 Step 4.3). Only called for a
message that Step 4.2's deterministic hard classifiers didn't already resolve (STOP/
AUTO_REPLY) -- this is the first (and so far only) LLM call anywhere in the inbound path.
"""
import json

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import INBOUND_CLASSIFIER_SYSTEM_PROMPT, REPLY_REDRAFT_SYSTEM_PROMPT

VALID_INTENTS = {"INTERESTED", "DEMO_REQUESTED", "OBJECTION", "STOP", "AUTO_REPLY"}


def classify_intent(db, lead_id, message: str, history: list, product_brief: dict, pain_points: list = None):
    """Returns {intent, confidence, suppress_immediately, escalate_to_human,
    suggested_reply}. Fails toward caution on any LLM error: intent falls back to
    OBJECTION (never a silent INTERESTED/DEMO_REQUESTED guess) with confidence 0.0 and
    escalate_to_human forced True -- an unreadable reply always goes to a human, never
    gets auto-replied to.

    `pain_points` grounds suggested_reply in THIS lead's actual verified complaints
    (same data outreach_agent.py drafts from) instead of the AI inferring generic
    problems from the product brief alone -- without it, a reply can invent plausible-
    sounding but unverified framing (see tracker.md Step 4.3 GameZone Visnagar bug).
    """
    prompt = INBOUND_CLASSIFIER_SYSTEM_PROMPT + f"""
MESSAGE: {json.dumps(message, ensure_ascii=False)}
PRIOR_CONVERSATION: {json.dumps(history, ensure_ascii=False)}
PRODUCT_BRIEF: {json.dumps(product_brief, ensure_ascii=False)}
LEAD_PAIN_POINTS: {json.dumps(pain_points or [], ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.2)
    except LLMError as exc:
        log_agent_event(db, "INBOUND", lead_id, "CLASSIFY_INTENT", 0.0, "HIGH", "LLM_FAILED",
                        payload={"error": str(exc)})
        return {"intent": "OBJECTION", "confidence": 0.0, "suppress_immediately": False,
                "escalate_to_human": True, "suggested_reply": ""}

    intent = data.get("intent")
    if intent not in VALID_INTENTS:
        intent = "OBJECTION"

    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    suppress_immediately = data.get("suppress_immediately") is True
    escalate_to_human = data.get("escalate_to_human") is True
    suggested_reply = str(data.get("suggested_reply", ""))[:600]

    result = {
        "intent": intent,
        "confidence": confidence,
        "suppress_immediately": suppress_immediately,
        "escalate_to_human": escalate_to_human,
        "suggested_reply": suggested_reply,
    }

    log_agent_event(db, "INBOUND", lead_id, "CLASSIFY_INTENT", confidence,
                    "HIGH" if escalate_to_human else "MEDIUM",
                    "HUMAN_ESCALATION" if escalate_to_human else "EXECUTE",
                    payload={"intent": intent})
    return result


def redraft_reply(db, lead_id, message: str, prior_draft: str, rejection_reasons: list,
                  suggested_corrections: str, pain_points: list, product_brief: dict) -> str:
    """Asks the model to fix a QC-rejected suggested_reply using QC's own feedback,
    instead of giving up -- a reply must always eventually go out for an escalated
    message (tracker.md Step 4.3: "reply karna jaruri he"). Returns "" on any LLM error
    (the caller falls back to a fixed, non-AI-generated message in that case, never an
    ungrounded/re-guessed reply)."""
    prompt = REPLY_REDRAFT_SYSTEM_PROMPT + f"""
LEAD_MESSAGE: {json.dumps(message, ensure_ascii=False)}
PRIOR_DRAFT: {json.dumps(prior_draft, ensure_ascii=False)}
QC_REJECTION_REASONS: {json.dumps(rejection_reasons, ensure_ascii=False)}
QC_SUGGESTED_CORRECTIONS: {json.dumps(suggested_corrections, ensure_ascii=False)}
LEAD_PAIN_POINTS: {json.dumps(pain_points or [], ensure_ascii=False)}
PRODUCT_BRIEF: {json.dumps(product_brief or {}, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.2)
    except LLMError as exc:
        log_agent_event(db, "INBOUND", lead_id, "REDRAFT_REPLY", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc)})
        return ""
    return str(data.get("reply", ""))[:600]
