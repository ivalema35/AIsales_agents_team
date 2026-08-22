"""Social Outreach Drafting Agent (Phase 10 Step 10.3 -- LinkedIn/Instagram/Facebook
draft-and-queue). Never sends anything itself -- MASTER PRD's own straight answer to
LinkedIn/IG/FB cold-messaging: LinkedIn has no official cold-messaging API at all (the
only way to automate it is browser-driving a real logged-in account, a ToS/permanent-ban
risk and a direct contradiction of this project's own evasion-free rule); Instagram/
Facebook's official APIs only permit messaging someone who has already messaged us first.
So this agent only ever DRAFTS -- a human reviews the draft, sends it manually from their
own account, and marks it sent (services/outreach/social_queue_service.py).
"""
from __future__ import annotations
import json
import re

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import SOCIAL_DRAFT_AGENT_SYSTEM_PROMPT

VALID_PLATFORMS = {"LINKEDIN", "INSTAGRAM", "FACEBOOK"}

# Deterministic backstop, not just a prompt instruction -- same "never trust blindly"
# posture as outreach_agent.py's own _strip_signature. Found live (2026-08-22, first
# real test run): the prompt already told the model never to sign off with a name or
# placeholder, and it still ended a real draft with "— [Your Name]" -- a literal
# bracketed placeholder that would have gone straight into the human-send queue as-is.
# Matches a trailing dash/em-dash + bracketed placeholder ("[Your Name]", "[Name]", etc.)
# at the very end of the message.
_PLACEHOLDER_SIGNOFF_RE = re.compile(r"[\s\-–—]*\[[A-Za-z ]{0,30}\]\s*$")


def _strip_placeholder_signoff(text: str) -> str:
    return _PLACEHOLDER_SIGNOFF_RE.sub("", text).rstrip()


def draft_social_message(db, lead_id, platform: str, product_brief: dict, lead_profile: dict,
                         pain_points: list, qc_feedback: str | None = None):
    """Returns {platform, message_text, hook_type, reasoning, confidence}, or None if
    drafting failed or produced an empty result."""
    prompt = SOCIAL_DRAFT_AGENT_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
PLATFORM: {platform}
"""
    if qc_feedback:
        prompt += f"\nYOUR PREVIOUS DRAFT WAS REJECTED BY QUALITY CONTROL. Fix this: {qc_feedback}\n"

    try:
        data = call_json(prompt, temperature=0.4)
    except LLMError as exc:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_SOCIAL", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc), "platform": platform})
        return None

    message_text = _strip_placeholder_signoff(str(data.get("message_text", "")).strip())
    hook_type = str(data.get("hook_type", ""))[:40]
    reasoning = str(data.get("reasoning", ""))[:300]
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    if not message_text:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_SOCIAL", confidence, "MEDIUM", "EMPTY_DRAFT",
                        payload={"platform": platform})
        return None

    draft = {"platform": platform, "message_text": message_text, "hook_type": hook_type,
            "reasoning": reasoning, "confidence": confidence}
    log_agent_event(db, "OUTREACH", lead_id, "DRAFT_SOCIAL", confidence, "MEDIUM", "DRAFTED",
                    payload={"platform": platform, "hook_type": hook_type})
    return draft
