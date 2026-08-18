from __future__ import annotations
from __future__ import annotations
from __future__ import annotations
"""Hyper-Personalized Outreach Agent (MASTER §6 / Intelligence PRD §2.1.G).

Drafts short, one-to-one-sounding outreach copy. Never writes its own footer/signature --
the system appends a compliant footer (physical address + unsubscribe link) so a draft
can never accidentally omit one or invent a non-compliant one.
"""
import json
import re

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import OUTREACH_AGENT_SYSTEM_PROMPT

# Deterministic backstop, not just a prompt instruction: the prompt already tells the
# model never to write its own signature/footer, but LLM instruction-following isn't
# 100% reliable (caught live -- a real draft ended with "Best,\n[Your Name]" and QC's
# own LLM judgment missed it too). Matches a trailing sign-off line (+ optional name/
# placeholder line after it) and strips it, same "never trust blindly" posture used
# everywhere else in this codebase (clamp/coerce, don't hope).
_SIGNATURE_RE = re.compile(
    r"\n+\s*(best|regards|sincerely|thanks|thank you|cheers|warm regards|kind regards|"
    r"best regards)[,.]?\s*\n*(\[?[a-z ]{0,30}\]?)?\s*$",
    re.IGNORECASE,
)


def _strip_signature(body: str) -> str:
    return _SIGNATURE_RE.sub("", body).rstrip()


def draft_email(db, lead_id, product_brief: dict, lead_profile: dict, pain_points: list,
                qc_feedback: str | None = None):
    """Returns a dict {subject, body, hook_type, confidence}, or None if drafting failed
    or produced an unusable (empty) result. `qc_feedback` carries a prior rejection's
    `suggested_corrections` into a retry attempt -- "regenerate with feedback", not a
    blind re-roll (MASTER §10 self-evaluation loop).
    """
    prompt = OUTREACH_AGENT_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
CHANNEL: EMAIL
"""
    if qc_feedback:
        prompt += f"\nYOUR PREVIOUS DRAFT WAS REJECTED BY QUALITY CONTROL. Fix this: {qc_feedback}\n"

    try:
        data = call_json(prompt, temperature=0.4)
    except LLMError as exc:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc)})
        return None

    subject = str(data.get("subject", "")).strip()[:150]
    body = _strip_signature(str(data.get("body", "")).strip())
    hook_type = str(data.get("hook_type", ""))[:40]
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    if not subject or not body:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL", confidence, "MEDIUM", "EMPTY_DRAFT")
        return None

    draft = {"subject": subject, "body": body, "hook_type": hook_type, "confidence": confidence}
    log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL", confidence, "MEDIUM", "DRAFTED",
                    payload={"hook_type": hook_type})
    return draft
