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
    return True


def draft_template(db, reason: str, context: dict, existing_templates: list[dict]):
    """Returns a validated candidate dict {name, category, purpose, body_text,
    variable_labels, reasoning}, or None if the model declined or produced something
    that doesn't satisfy Meta's real constraints -- every outcome is logged via
    log_agent_event so a silent decline is still visible, same as draft_email()'s
    LLM_FAILED/EMPTY_DRAFT events. Never raises on a bad/declined draft; only an LLM
    transport failure is caught internally (also logged, also returns None).
    """
    prompt = TEMPLATE_AGENT_SYSTEM_PROMPT + f"""
REASON: {reason}
CONTEXT: {json.dumps(context, ensure_ascii=False)}
EXISTING_TEMPLATES: {json.dumps(existing_templates, ensure_ascii=False)}
"""
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
        "reasoning": str(data.get("reasoning", ""))[:200],
    }
    log_agent_event(db, "TEMPLATE_AGENT", None, "DRAFT_TEMPLATE", 0.8, "MEDIUM", "DRAFTED",
                    payload={"name": candidate["name"], "reasoning": candidate["reasoning"]})
    return candidate
