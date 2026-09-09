"""WhatsApp Template Drafting Agent (Phase 9 Step 9.6 sub-step 2).

Pure drafting: given a real reason + supporting data, proposes ONE new WhatsApp template
candidate via a real LLM call, validated against Meta's real template constraints. Does
NOT touch the database or call Meta -- the caller decides what happens to the returned
candidate (QC review is sub-step 3; persisting it as a DRAFT row and wiring a real
trigger is sub-step 4). Keeping this a pure function makes each stage of the pipeline
independently testable, matching every other multi-stage agent flow in this codebase.
"""
from __future__ import annotations
import json
import re

from cognition.agent_events import log_agent_event
from cognition.llm_client import call_json, LLMError
from cognition.prompts import TEMPLATE_AGENT_SYSTEM_PROMPT

NAME_RE = re.compile(r"^[a-z0-9_]+$")
VALID_CATEGORIES = {"MARKETING", "UTILITY", "AUTHENTICATION"}
VALID_PURPOSES = {"FIRST_TOUCH", "FOLLOW_UP"}
VALID_VARIABLES = {"contact_name", "company_name", "pain_point_phrase"}


def _is_valid_candidate(data: dict, existing_names: set) -> bool:
    name = str(data.get("name", ""))
    if not name or not NAME_RE.match(name) or name in existing_names:
        return False
    if data.get("category") not in VALID_CATEGORIES:
        return False
    if data.get("purpose") not in VALID_PURPOSES:
        return False
    body_text = str(data.get("body_text", "")).strip()
    if not body_text:
        return False
    variable_labels = data.get("variable_labels")
    if not isinstance(variable_labels, list) or not all(v in VALID_VARIABLES for v in variable_labels):
        return False
    placeholder_count = len(re.findall(r"\{\{\d+\}\}", body_text))
    if placeholder_count != len(variable_labels):
        return False
    button_label = data.get("button_label")
    if button_label is not None and (not isinstance(button_label, str) or not button_label.strip() or len(button_label) > 25):
        return False
    return True


def draft_template(db, reason: str, context: dict, existing_templates: list[dict],
                   qc_feedback: str | None = None, campaign_strategy_angle: str | None = None,
                   want_button: bool = False, button_asset: dict | None = None,
                   human_instruction: str | None = None, previous_candidate: dict | None = None):
    """Returns a validated candidate dict {name, category, purpose, body_text,
    variable_labels, button_label, reasoning}, or None if the model declined or produced
    something that doesn't satisfy Meta's real constraints -- every outcome is logged via
    log_agent_event so a silent decline is still visible, same as draft_email()'s
    LLM_FAILED/EMPTY_DRAFT events. Never raises on a bad/declined draft; only an LLM
    transport failure is caught internally (also logged, also returns None).

    `qc_feedback` (2026-09-08, same "regenerate with feedback" pattern email drafting
    already used): a prior candidate's real QC rejection reasons, fed back so a retry
    isn't a blind re-roll -- see propose_new_template()'s own retry loop.

    `campaign_strategy_angle` (2026-09-09, real user ask): when this draft is for one
    specific campaign's own "Ask AI for a template" click, ground the tone/angle in that
    campaign's real, human-set strategy -- the same way email/outreach copy already does.

    `want_button`/`button_asset` (2026-09-09, real user ask: "button wala template bhi
    de sake"): `button_asset` is a REAL content asset {"title","value"(url)} for this
    product, resolved by the caller -- never invented here. The model may only propose a
    `button_label`; the real URL is attached by the caller from `button_asset`, never
    written by the model itself.

    `human_instruction`/`previous_candidate` (2026-09-09, real user ask: "user review kar
    sake feedback dekar sudhar sake") -- a human reviewing an existing DRAFT gave a
    revision instruction; the model edits FROM `previous_candidate` rather than starting
    fresh, same "current state + one instruction" pattern already used for outreach/
    kickoff draft revisions elsewhere in this codebase.
    """
    prompt = TEMPLATE_AGENT_SYSTEM_PROMPT + f"""
REASON: {reason}
CONTEXT: {json.dumps(context, ensure_ascii=False)}
EXISTING_TEMPLATES: {json.dumps(existing_templates, ensure_ascii=False)}
"""
    if campaign_strategy_angle:
        prompt += f"\nCAMPAIGN_STRATEGY_ANGLE: {campaign_strategy_angle}\n"
    if want_button:
        if button_asset:
            prompt += f"""
BUTTON: a human asked for a call-to-action button on this template. A real asset is
available: {json.dumps(button_asset, ensure_ascii=False)}. Include "button_label" (<=25
characters, based on this real asset's title) in your output JSON. The actual URL is
attached by the system, not by you -- never write a URL into body_text.
"""
        else:
            prompt += (
                "\nBUTTON: a human asked for a call-to-action button, but no real demo/video "
                "asset exists yet for this product -- do NOT invent a URL or a button_label; "
                "draft the message text only and say so briefly in your reasoning.\n"
            )
    if previous_candidate and human_instruction:
        prompt += f"""
PREVIOUS_CANDIDATE (what a human already reviewed): {json.dumps(previous_candidate, ensure_ascii=False)}
HUMAN'S FEEDBACK ON THAT CANDIDATE: {human_instruction}
Revise the previous candidate to genuinely address this feedback. Keep the same "name"
unless the feedback clearly asks for a different approach that warrants a new one.
"""
    if qc_feedback:
        prompt += f"\nYOUR PREVIOUS CANDIDATE WAS REJECTED BY QUALITY CONTROL. Fix this: {qc_feedback}\n"
    try:
        data = call_json(prompt, temperature=0.5)
    except LLMError as exc:
        log_agent_event(db, "TEMPLATE_AGENT", None, "DRAFT_TEMPLATE", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc)})
        return None

    if not data.get("drafted"):
        log_agent_event(db, "TEMPLATE_AGENT", None, "DRAFT_TEMPLATE", 0.0, "MEDIUM", "DECLINED",
                        payload={"reasoning": data.get("reasoning", "")})
        return None

    existing_names = {t["name"] for t in existing_templates if "name" in t}
    if not _is_valid_candidate(data, existing_names):
        log_agent_event(db, "TEMPLATE_AGENT", None, "DRAFT_TEMPLATE", 0.0, "MEDIUM", "INVALID_CANDIDATE",
                        payload={"raw": data})
        return None

    candidate = {
        "name": data["name"],
        "category": data["category"],
        "purpose": data["purpose"],
        "body_text": str(data["body_text"]).strip(),
        "variable_labels": data["variable_labels"],
        "button_label": (str(data["button_label"]).strip() if want_button and button_asset and data.get("button_label") else None),
        "reasoning": str(data.get("reasoning", ""))[:200],
    }
    log_agent_event(db, "TEMPLATE_AGENT", None, "DRAFT_TEMPLATE", 0.8, "MEDIUM", "DRAFTED",
                    payload={"name": candidate["name"], "reasoning": candidate["reasoning"]})
    return candidate
