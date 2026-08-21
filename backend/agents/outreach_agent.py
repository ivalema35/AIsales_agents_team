"""Hyper-Personalized Outreach Agent (MASTER §6 / Intelligence PRD §2.1.G).

Drafts short, one-to-one-sounding outreach copy. Never writes its own footer/signature --
the system appends a compliant footer (physical address + unsubscribe link) so a draft
can never accidentally omit one or invent a non-compliant one.
"""
from __future__ import annotations
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
                qc_feedback: str | None = None, format_sections: list | None = None,
                content_assets: list | None = None, is_followup: bool = False):
    """Returns a dict {subject, body, hook_type, confidence}, or None if drafting failed
    or produced an unusable (empty) result. `qc_feedback` carries a prior rejection's
    `suggested_corrections` into a retry attempt -- "regenerate with feedback", not a
    blind re-roll (MASTER §10 self-evaluation loop).

    `format_sections`/`content_assets` (Phase 8 Steps 8.1/8.2, tracker.md A.7) are both
    optional and both None by every caller that hasn't resolved a format yet -- when
    both are absent the prompt built below is byte-identical to before this parameter
    existed, so an unset product/channel behaves exactly as today. `format_sections` is
    a GUIDELINE list (an outline the model follows while still writing its own natural,
    adaptive, personalized copy), never literal text substituted into slots -- see this
    module's own admin-authored-STRUCTURE-not-final-copy design note. `content_assets`
    is the closed set of demo links/case studies the model may select from; it must
    never invent a URL that isn't in this list.

    `is_followup` (Phase 9 Step 9.3): True only when jobs/discovery_scheduler.py's
    follow-up tick is drafting touch 2+ for a lead who hasn't replied yet -- tells the
    model to write a brief nudge referencing the earlier outreach, not repeat the full
    pitch. False (default) for every touch-1 caller, unchanged from before this existed.
    """
    prompt = OUTREACH_AGENT_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
CHANNEL: EMAIL
"""
    if is_followup:
        prompt += """
THIS IS A FOLLOW-UP: an earlier first-touch message was already sent to this same lead
about this same product and has not been replied to yet. Write a SHORT, low-pressure
nudge (well under the usual length) that references you reached out before without
repeating the full pitch or the same pain-point framing verbatim -- a brief new angle or
a simple "still worth a look?" is enough. Never guilt-trip or imply urgency that isn't
real (no fake scarcity/deadlines).
"""
    if format_sections:
        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(format_sections, 1))
        prompt += f"""
FORMAT: the admin has defined this shape for the email -- follow this ORDER and INTENT,
but these are guidelines, not literal text to insert. Write your own natural, adaptive,
personalized copy that fulfils each point in your own words, exactly as you would
without a format:
{numbered}
"""
    if content_assets:
        prompt += f"""
AVAILABLE_CONTENT_ASSETS: {json.dumps(content_assets, ensure_ascii=False)}
If the format calls for one of these (e.g. a demo link) and a genuinely relevant asset
is listed above, you may reference it by its exact "value". If none is relevant, or the
format doesn't call for one, omit it entirely -- never invent a URL not in this list.
"""
    if qc_feedback:
        prompt += f"\nYOUR PREVIOUS DRAFT WAS REJECTED BY QUALITY CONTROL. Fix this: {qc_feedback}\n"

    try:
        data = call_json(prompt, temperature=0.4)
    except LLMError as exc:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc)})
        return None

    # Phase 8 Step 8.4 -- N subject candidates, one selected. Selection is still AI
    # judgment here (no send-performance data exists yet to learn from -- that's
    # Phase 9); ALL candidates are kept on the returned draft so the caller can persist
    # them for Phase 9 to measure retrospectively, not just the one that got sent.
    raw_candidates = data.get("subject_candidates")
    subject_candidates = (
        [str(s).strip()[:150] for s in raw_candidates if str(s).strip()]
        if isinstance(raw_candidates, list) else []
    )
    selected_subject = str(data.get("selected_subject") or data.get("subject") or "").strip()[:150]
    if subject_candidates and selected_subject not in subject_candidates:
        # model didn't echo one of its own candidates back cleanly -- don't trust a
        # mismatched value, fall back to its own first candidate instead
        selected_subject = subject_candidates[0]
    subject = selected_subject or (subject_candidates[0] if subject_candidates else "")

    body = _strip_signature(str(data.get("body", "")).strip())
    hook_type = str(data.get("hook_type", ""))[:40]
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    if not subject or not body:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL", confidence, "MEDIUM", "EMPTY_DRAFT")
        return None

    draft = {
        "subject": subject,
        "subject_candidates": subject_candidates or [subject],
        "body": body,
        "hook_type": hook_type,
        "confidence": confidence,
    }
    log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL", confidence, "MEDIUM", "DRAFTED",
                    payload={"hook_type": hook_type})
    return draft
