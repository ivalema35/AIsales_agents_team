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
from cognition.prompts import OUTREACH_AGENT_SYSTEM_PROMPT, OUTREACH_SECTIONS_SYSTEM_PROMPT

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
FORMAT: the admin has defined this shape for the email -- write the sections in THIS
EXACT ORDER below, section 1 first, then section 2, and so on. Do not reorder them
(e.g. do not open with a greeting unless section 1 IS the greeting) and do not fall
back to a generic "greeting, then pain point" structure -- these are guidelines for
what each section should accomplish, not literal text to insert; write your own
natural, adaptive, personalized copy that fulfils each point in your own words, in
this order, exactly as you would without a format:
{numbered}
"""
    if content_assets:
        prompt += f"""
AVAILABLE_CONTENT_ASSETS: {json.dumps(content_assets, ensure_ascii=False)}
If the FORMAT above includes a section calling for one of these (e.g. a demo link),
you MUST include a genuinely relevant one from this list by its exact "value" -- do
not silently drop that section just because the email reads more smoothly without it.
Only omit it if truly no listed asset fits this lead, or the format has no such
section; never invent a URL not in this list.
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


# ---------------------------------------------------------------------------
# Phase 11 Step 11.1 -- structured section contract.
#
# Deliberately a SEPARATE function from draft_email() above rather than a flag on it:
# every caller live today keeps running the exact code path it runs now, so the day this
# ships nothing already in production changes behaviour. The two converge later, once the
# structured path has been proven on real sends.
#
# The safety-critical design decision here is WHO writes a URL. The model authors only
# prose (hook, bullets, CTA copy) and is told explicitly not to write any URL at all;
# every real link -- video, demo button -- is inserted by _assemble_sections() below from
# the approved content_assets list. That makes a fabricated URL structurally impossible
# rather than prompt-discouraged, which is the same posture the project already took with
# the content library itself: the boundary does the safety work, not the instruction.
# ---------------------------------------------------------------------------

MAX_BULLETS = 4
MAX_BULLET_CHARS = 160

# Every asset-backed section, declared in the order it appears between SOLUTION and CTA.
#
# This is a table rather than a chain of if-statements for a specific reason: the rule
# "a section whose asset does not exist is not rendered at all" must hold for EVERY
# optional section, not just the two that happened to be asked for first. Adding a new
# one later -- a testimonial, a case study, a price sheet -- is one row here, and it
# inherits the omission behaviour automatically instead of needing someone to remember
# to re-implement it.
#
# `kind` is how the asset's own `value` should be read: "url" means the value is a link
# the renderer turns into a button/thumbnail; "text" means the value IS the content.
# Asset types come from content_assets.asset_type (schema.sql Table 23).
ASSET_SECTIONS = (
    # (section_type,  asset_type,     kind,   fallback_label)
    ("VIDEO",         "VIDEO_URL",    "url",  "Watch the video"),
    ("CASE_STUDY",    "CASE_STUDY",   "url",  "Read the case study"),
    ("TESTIMONIAL",   "TESTIMONIAL",  "text", "What our clients say"),
    ("TEXT_BLOCK",    "TEXT_BLOCK",   "text", ""),
)

# The demo link is deliberately NOT in the table above: it is a button inside the CTA
# section (the operator's own spec: "cta start for 1 month free aur usme hoga demo link
# btn"), not a section of its own. It follows the identical rule anyway -- no approved
# DEMO_URL asset means the CTA renders with no button rather than a fabricated one.
CTA_BUTTON_ASSET_TYPE = "DEMO_URL"


def _clean_line(value, limit=300) -> str:
    return str(value or "").strip()[:limit]


def _clean_bullets(value) -> list[str]:
    """A bullet list is a real list. A model that returns a newline-joined string instead
    (which happens) is coerced rather than dropped -- losing a whole section to a
    formatting slip would be a worse failure than accepting a recoverable one."""
    if isinstance(value, str):
        value = [line for line in value.splitlines() if line.strip()]
    if not isinstance(value, list):
        return []
    bullets = []
    for item in value:
        text = str(item or "").strip().lstrip("-•*").strip()
        if text:
            bullets.append(text[:MAX_BULLET_CHARS])
    return bullets[:MAX_BULLETS]


def _pick_asset(content_assets, asset_type):
    """The first genuinely usable approved asset of this type, or None. None is a normal,
    expected outcome -- it means this section is dropped (Step 11.3), never fabricated."""
    for asset in content_assets or []:
        if isinstance(asset, dict) and asset.get("asset_type") == asset_type and asset.get("value"):
            return asset
    return None


def _assemble_sections(data: dict, content_assets) -> list[dict]:
    """Ordered, typed sections. A section is appended ONLY when it has real content, so
    graceful omission is a property of the structure itself rather than something the
    renderer has to remember to check for -- and it applies uniformly to every optional
    section (ASSET_SECTIONS above), not just the ones that existed first.

    INTEREST / CONTACT / FOOTER are deliberately absent here: they carry no AI-authored
    content at all and are added downstream from real system data (Step 11.4 settings,
    Phase 12 signed interest links, the renderer's own compliance footer).
    """
    sections = []

    hook = _clean_line(data.get("hook"))
    if hook:
        sections.append({"type": "HOOK", "text": hook})

    pain_points = _clean_bullets(data.get("pain_points"))
    if pain_points:
        sections.append({"type": "PAIN_POINTS", "items": pain_points})

    solution_points = _clean_bullets(data.get("solution_points"))
    if solution_points:
        sections.append({"type": "SOLUTION", "items": solution_points})

    # Every optional asset-backed section, same rule for all of them: no approved asset
    # of that type -> the section is not appended at all.
    for section_type, asset_type, kind, fallback_label in ASSET_SECTIONS:
        asset = _pick_asset(content_assets, asset_type)
        if not asset:
            continue
        title = _clean_line(asset.get("title"), 120) or fallback_label
        section = {"type": section_type, "title": title}
        if kind == "url":
            section["url"] = asset["value"]
        else:
            section["text"] = _clean_line(asset["value"], 1000)
            if not section["text"]:
                continue  # an asset row that exists but is empty is still "no content"
        sections.append(section)

    cta_headline = _clean_line(data.get("cta_headline"), 120)
    cta_subtext = _clean_line(data.get("cta_subtext"), 240)
    demo = _pick_asset(content_assets, CTA_BUTTON_ASSET_TYPE)
    if cta_headline or cta_subtext or demo:
        cta = {"type": "CTA", "headline": cta_headline, "subtext": cta_subtext}
        if demo:
            cta["button_url"] = demo["value"]
            cta["button_label"] = _clean_line(demo.get("title"), 40) or "See the demo"
        sections.append(cta)

    # Phase 11 Step 11.5 -- only ever appended when the model actually wrote one. An empty
    # string is the documented, expected answer when nothing in the admin's cross-sell list
    # genuinely fits this lead, and it drops the section by the same rule as every other
    # optional one rather than forcing a weak offer into a real email.
    cross_sell = _clean_line(data.get("cross_sell_line"), 240)
    if cross_sell:
        sections.append({"type": "CROSS_SELL", "text": cross_sell})

    return sections


def _sections_to_text(sections: list[dict]) -> str:
    """Plain-text rendering of the same sections. Not a display format -- it exists so
    QC, `outreach_logs.message_body` and every existing consumer that expects a body
    string keep working unchanged against a structured draft."""
    parts = []
    for section in sections:
        kind = section["type"]
        if kind == "HOOK":
            parts.append(section["text"])
        elif kind in ("PAIN_POINTS", "SOLUTION"):
            parts.append("\n".join(f"- {item}" for item in section["items"]))
        elif kind == "CTA":
            cta = [section.get("headline", ""), section.get("subtext", "")]
            if section.get("button_url"):
                cta.append(f"{section.get('button_label', 'Demo')}: {section['button_url']}")
            parts.append("\n".join(p for p in cta if p))
        elif kind == "CROSS_SELL":
            # Plain text, deliberately with no title prefix -- it's one quiet sentence,
            # not a labelled asset like the sections below.
            parts.append(section["text"])
        # Every asset-backed section renders the same way regardless of which one it is,
        # so a newly-added ASSET_SECTIONS row needs no change here either.
        elif "url" in section:
            parts.append(f"{section.get('title', '')}: {section['url']}".lstrip(": "))
        elif "text" in section:
            parts.append(f"{section.get('title', '')}: {section['text']}".lstrip(": "))
    return "\n\n".join(p for p in parts if p).strip()


def draft_structured_email(db, lead_id, product_brief: dict, lead_profile: dict, pain_points: list,
                           qc_feedback: str | None = None, content_assets: list | None = None,
                           cross_sell_products: list | None = None):
    """Phase 11 Step 11.1. Returns {subject, subject_candidates, body, sections, hook_type,
    confidence}, or None if drafting failed or produced nothing usable.

    `body` is the plain-text equivalent of `sections`, kept so QC and the existing
    outreach_logs contract need no change to accept a structured draft; `sections` is what
    Step 11.2's renderer actually builds the real email from.

    `cross_sell_products` (Step 11.5, tracker.md A.10): the real briefs of the OTHER
    products the admin explicitly chose to cross-sell alongside this one. The model may
    name exactly one of them and nothing outside the list -- which is what makes an
    invented service structurally impossible here, the same boundary the content library
    already provides for URLs. Absent or empty means no cross-sell line at all, and the
    prompt below is then byte-identical to before this parameter existed.
    """
    prompt = OUTREACH_SECTIONS_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
CHANNEL: EMAIL
"""
    if cross_sell_products:
        prompt += f"""
CROSS_SELL_PRODUCTS -- other real services this company offers, chosen by the admin for
this specific product. You may mention AT MOST ONE of these, only if it is genuinely
relevant to THIS lead, and you may never name a service outside this list:
{json.dumps(cross_sell_products, ensure_ascii=False)}
"""
    if qc_feedback:
        prompt += f"\nYOUR PREVIOUS DRAFT WAS REJECTED BY QUALITY CONTROL. Fix this: {qc_feedback}\n"

    try:
        data = call_json(prompt, temperature=0.4)
    except LLMError as exc:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL_SECTIONS", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc)})
        return None

    raw_candidates = data.get("subject_candidates")
    subject_candidates = (
        [str(s).strip()[:150] for s in raw_candidates if str(s).strip()]
        if isinstance(raw_candidates, list) else []
    )
    selected_subject = str(data.get("selected_subject") or data.get("subject") or "").strip()[:150]
    if subject_candidates and selected_subject not in subject_candidates:
        selected_subject = subject_candidates[0]
    subject = selected_subject or (subject_candidates[0] if subject_candidates else "")

    sections = _assemble_sections(data, content_assets)
    body = _sections_to_text(sections)
    hook_type = str(data.get("hook_type", ""))[:40]
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    # A draft with a subject but no hook is not a recoverable partial -- it has no opening
    # line at all, which is the one section this design treats as mandatory.
    has_hook = any(s["type"] == "HOOK" for s in sections)
    if not subject or not has_hook:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL_SECTIONS", confidence, "MEDIUM",
                        "EMPTY_DRAFT", payload={"section_types": [s["type"] for s in sections]})
        return None

    draft = {
        "subject": subject,
        "subject_candidates": subject_candidates or [subject],
        "body": body,
        "sections": sections,
        "hook_type": hook_type,
        "confidence": confidence,
    }
    log_agent_event(db, "OUTREACH", lead_id, "DRAFT_EMAIL_SECTIONS", confidence, "MEDIUM", "DRAFTED",
                    payload={"hook_type": hook_type, "section_types": [s["type"] for s in sections]})
    return draft
