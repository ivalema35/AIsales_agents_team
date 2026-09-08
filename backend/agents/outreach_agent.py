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
from cognition.prompts import (
    OUTREACH_AGENT_SYSTEM_PROMPT, OUTREACH_SECTIONS_SYSTEM_PROMPT,
    FOLLOWUP_LEVEL_SYSTEM_PROMPT, FOLLOWUP_LEVEL_1_WITH_ASSET, FOLLOWUP_LEVEL_1_NO_ASSET,
    FOLLOWUP_LEVEL_2, FOLLOWUP_LEVEL_3, DRAFT_IMPROVEMENT_SUGGESTION_SYSTEM_PROMPT,
)

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
        prompt += f"""
YOUR PREVIOUS DRAFT(S) WERE REJECTED BY QUALITY CONTROL. {qc_feedback}
If more than one correction is numbered above, apply ALL of them together -- they are
corrections from separate earlier attempts, and fixing a later one must never silently
undo an earlier one (e.g. don't re-add something attempt 1 already told you to remove).
"""

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


# Phase 16 Step 16.4 -- the model chooses WHICH pre-built, email-safe layout to render a
# bullet section with, never raw markup itself. Any value outside this set (including a
# missing key -- every caller/prompt that predates this field) coerces to the exact
# rendering this project already had, so nothing changes when the model doesn't choose.
_VALID_LAYOUTS = {"BADGE_LIST", "PROSE"}


def _clean_layout(value) -> str:
    value = str(value or "").strip().upper()
    return value if value in _VALID_LAYOUTS else "BADGE_LIST"


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


def _asset_sections(content_assets) -> list[dict]:
    """Every optional asset-backed section (ASSET_SECTIONS table above), same rule for
    all of them: no approved asset of that type -> nothing appended. Factored out of
    _assemble_sections() (Phase 13 Step 13.1) so the follow-up Level 1 path can
    "re-present" the exact same real asset touch 1 would have shown, via the identical
    deterministic selection (_pick_asset always returns the first matching real asset,
    so calling it again naturally reproduces touch 1's own choice) -- without duplicating
    this loop a second time.
    """
    sections = []
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
    return sections


def _assemble_sections(data: dict, content_assets, cross_sell_products=None) -> list[dict]:
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
        sections.append({"type": "PAIN_POINTS", "items": pain_points,
                         "layout": _clean_layout(data.get("pain_points_layout"))})

    solution_points = _clean_bullets(data.get("solution_points"))
    if solution_points:
        sections.append({"type": "SOLUTION", "items": solution_points,
                         "layout": _clean_layout(data.get("solution_points_layout"))})

    sections += _asset_sections(content_assets)

    cta_headline = _clean_line(data.get("cta_headline"), 120)
    cta_subtext = _clean_line(data.get("cta_subtext"), 240)
    demo = _pick_asset(content_assets, CTA_BUTTON_ASSET_TYPE)
    if cta_headline or cta_subtext or demo:
        cta = {"type": "CTA", "headline": cta_headline, "subtext": cta_subtext}
        if demo:
            cta["button_url"] = demo["value"]
            cta["button_label"] = _clean_line(demo.get("title"), 40) or "See the demo"
        sections.append(cta)

    # Phase 11 Step 11.5 -- only ever appended when the model wrote a real line that (a)
    # opens with the required "We also offer/build <product>" announcement and (b) names
    # one of the admin's own approved products there. This is a NAME + OPENING check, not
    # a content check: everything after that opening is allowed to be genuinely
    # personalized, tying that product's real capabilities to this lead's actual pain
    # point (the operator's own explicit ask -- a bare "we also offer X" with nothing
    # after it was too generic; a benefit line with no "we also offer" opening didn't
    # clearly announce this was a second, additional service). What IS still checked here
    # deterministically, same "never trust blindly" posture as _strip_signature/
    # _missing_required_asset/_strip_placeholder_signoff elsewhere in this codebase: the
    # line must literally start with the mandatory opening naming an approved product, and
    # must carry no URL (this section gets no button/link of its own -- a URL here would
    # be either a broken promise or a fabricated one). Whether the CAPABILITY claim inside
    # the rest of the line is genuinely grounded in that product's own brief is QC's job
    # (review_draft()), the same way QC already grounds the main pitch's own capability
    # claims -- that judgment needs real reasoning about what the brief says, which a
    # name/URL check cannot do.
    cross_sell = _clean_line(data.get("cross_sell_line"), 300)
    if cross_sell and cross_sell_products:
        named_product = next(
            (p for p in cross_sell_products
             if re.match(rf"we also (offer|build) {re.escape(p['title'])}\b", cross_sell, re.IGNORECASE)),
            None)
        if named_product and not re.search(r"https?://", cross_sell):
            # The matched product's own real brief travels WITH the section (not as a
            # separate parameter QC would need threaded through) -- review_draft() reads
            # it straight out of the draft it already receives, to ground this section's
            # capability claim the same way it grounds the main pitch's, against a real
            # source it was actually shown.
            sections.append({"type": "CROSS_SELL", "text": cross_sell,
                            "named_product": named_product})

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
            if section.get("layout") == "PROSE":
                parts.append(" ".join(item.rstrip(".") + "." for item in section["items"]))
            else:
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
                           cross_sell_products: list | None = None, tone_directive: str | None = None,
                           format_directive: str | None = None,
                           human_revision_instruction: str | None = None,
                           previous_draft_text: str | None = None,
                           kickoff_template_preview: bool = False,
                           recent_rejection_patterns: list | None = None):
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

    `tone_directive`/`format_directive` (Phase 16 Step 16.4): the product's optional
    `default_tone`/`default_format` free-text guidelines (e.g. "Urgent & ROI-driven" /
    "short, plain text, no bullets") -- changes HOW the email is written, never WHAT it
    claims (facts still come only from PRODUCT/PAIN_POINTS as already required). Both
    None for every product until an admin sets one, in which case the prompt below is
    byte-identical to before this parameter existed.

    `human_revision_instruction` (Phase 16 Step 16.5): a reviewer's own free-text edit
    request on an existing preview ("isko formal karo") -- regenerates the WHOLE draft
    with that one instruction applied, same "targeted fix, not a blind re-roll" posture
    as `qc_feedback`, but from a human's stylistic ask rather than QC's rejection.

    `previous_draft_text` -- the subject+body of the draft this instruction is editing,
    when this is the SECOND (or later) round of feedback in the same session. Without
    it, every revision call regenerates from PRODUCT/PAIN_POINTS/LEAD fresh and only
    knows about the CURRENT instruction -- a real gap the operator caught live
    (2026-09-01): asking for "make it casual" then, separately, "add an emoji" silently
    dropped the casual tone the first edit had already applied, because the second call
    had no memory of it. When provided, the model edits THAT text in place instead of
    re-deriving a new draft from the underlying facts, so every earlier accepted change
    survives every later one.

    `kickoff_template_preview` (2026-09-05, Step 18.1b intent): when True, LEAD/PAIN_POINTS
    carry literal [Business Name]/[Pain Point] tokens for a campaign with no real leads
    yet -- the model must keep those tokens, never invent a fictional business or pain.
    lead_id may be None in that path (events log without a lead).

    `recent_rejection_patterns` (2026-09-08, real user pushback: "AI Manager ko adaptive
    banna hoga" -- an AI with the whole DB in front of it shouldn't need a human to
    notice a recurring QC rejection pattern across a campaign's OTHER leads and hand-patch
    a prompt): real, current rejection reasons QC gave for OTHER leads in this SAME
    campaign recently (services/campaign_service.py's recent_qc_rejection_reasons()) --
    this lead's own draft learns from what's been tripping up its neighbors, not just its
    own retry attempts.
    """
    prompt = OUTREACH_SECTIONS_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
CHANNEL: EMAIL
"""
    if recent_rejection_patterns:
        prompt += f"""
RECENT_REJECTION_PATTERNS_IN_THIS_CAMPAIGN -- QC's real rejection reasons for OTHER
leads in this same campaign, most recent first. This is a DIFFERENT lead, but avoid
repeating the same mistake if one of these applies here too (e.g. if these say drafts
kept overstating an empty/weak PAIN_POINTS list, make sure yours doesn't do that either):
{json.dumps(recent_rejection_patterns, ensure_ascii=False)}
"""
    if kickoff_template_preview:
        prompt += """
KICKOFF_TEMPLATE_PREVIEW -- this is NOT a real lead. LEAD.company_name is the literal
token "[Business Name]" and PAIN_POINTS contain the literal token "[Pain Point]". Keep
those exact tokens in the draft wherever a real send would put that lead's company name
or pain. Do NOT invent a fictional business name, city, person, or pain claim. Every
PRODUCT fact still comes only from PRODUCT above. Real sends later substitute each lead's
own real name and pain -- this preview only shows shape/tone/angle for human review.
"""
    if tone_directive or format_directive:
        prompt += f"""
TONE_AND_FORMAT: the admin has set a preferred style for this product's outreach.
{f"TONE: {tone_directive}" if tone_directive else ""}
{f"FORMAT: {format_directive}" if format_directive else ""}
Write the email in this style throughout (word choice, sentence length), while keeping
every fact grounded in PRODUCT/PAIN_POINTS/LEAD exactly as already required -- this
changes HOW it's said, never WHAT is claimed. If FORMAT above asks for something
short/plain-text/no-bullets, that is exactly when to choose "PROSE" for
pain_points_layout/solution_points_layout instead of the default "BADGE_LIST".
"""
    if cross_sell_products:
        prompt += f"""
CROSS_SELL_PRODUCTS -- other real services this company offers, chosen by the admin for
this specific product. You may mention AT MOST ONE of these, only if it is genuinely
relevant to THIS lead, and you may never name a service outside this list:
{json.dumps(cross_sell_products, ensure_ascii=False)}
"""
    if qc_feedback:
        prompt += f"""
YOUR PREVIOUS DRAFT(S) WERE REJECTED BY QUALITY CONTROL. {qc_feedback}
If more than one correction is numbered above, apply ALL of them together -- they are
corrections from separate earlier attempts, and fixing a later one must never silently
undo an earlier one (e.g. don't re-add something attempt 1 already told you to remove).
"""
    if human_revision_instruction:
        if previous_draft_text:
            prompt += f"""
CURRENT_DRAFT -- this already reflects every earlier edit the human has asked for in this
session (tone, format, additions, everything):
{previous_draft_text}

A HUMAN REVIEWER asked for this ADDITIONAL, NEW change, on top of CURRENT_DRAFT above:
{human_revision_instruction}
Start from CURRENT_DRAFT and apply ONLY this new instruction to it -- do not regenerate
from PRODUCT/PAIN_POINTS/LEAD as if this were the first draft. Every earlier accepted
change (tone, emojis, structure, anything) must still be present in your output unless
this new instruction specifically contradicts it. Apply the new instruction precisely and
LITERALLY, including style choices you might not default to (emojis, exclamation marks, a
more casual/bold voice) if that is what was asked -- a request applied only partially is a
failure to follow it. Keep every FACT and grounding exactly as already required; only
style/tone/format changes at the reviewer's explicit request.
"""
        else:
            prompt += f"""
A HUMAN REVIEWER asked for this specific change to the draft: {human_revision_instruction}
Apply it precisely and LITERALLY -- this is a targeted edit, not a full rewrite from
scratch, and not a suggestion you may soften or partially apply. This overrides any
default stylistic instinct elsewhere in this prompt that would normally pull the other
way (e.g. if asked for emojis, exclamation marks, or a more casual/bold style than you
would otherwise choose, use them for real -- a request applied only partially is a
failure to follow the instruction). Keep every FACT and grounding exactly as already
required; only style/tone/format changes at the reviewer's explicit request.
"""

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

    sections = _assemble_sections(data, content_assets, cross_sell_products)
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


def suggest_draft_improvement(db, lead_id, product_brief: dict, pain_points: list, sections: list) -> str:
    """Phase 16 Step 16.5 -- called AFTER a human's own revision (draft_structured_email's
    `human_revision_instruction`) has already been applied. Proposes ONE further, concrete
    improvement the human did not ask for -- shown as a separate, dismissible card, never
    auto-applied. Returns "" on any LLM error or when the model genuinely has nothing to
    add (both treated the same by the caller: no suggestion shown)."""
    prompt = DRAFT_IMPROVEMENT_SUGGESTION_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
CURRENT_DRAFT_SECTIONS: {json.dumps(sections, ensure_ascii=False)}
"""
    try:
        data = call_json(prompt, temperature=0.5)
    except LLMError as exc:
        log_agent_event(db, "OUTREACH", lead_id, "SUGGEST_IMPROVEMENT", 0.0, "LOW", "LLM_FAILED",
                        payload={"error": str(exc)})
        return ""
    return str(data.get("suggestion", ""))[:250]


# ---------------------------------------------------------------------------
# Phase 13 Step 13.1 -- level-aware follow-up drafting. Replaces draft_email()'s old
# is_followup=True path: that path wrote one generic "brief nudge" instruction regardless
# of which touch this was, so touch 2 and touch 3 differed only by delay and LLM variance.
# Each level here has exactly one stated job (tracker.md A.11) and renders through this
# SAME structured section engine touch 1 uses, not the old free-form path.
#
# What stays deliberately AI-authored (reviewed by QC below) vs. system-appended after
# QC (never reviewed, because there is nothing in it for QC to judge) follows the exact
# same split touch 1 already established for CONTACT/INTEREST: Level 3's real products
# list is 100% deterministic (straight from the products table), so it is appended by
# jobs/outreach_handler.py post-QC, not drafted here -- inventing a second AI-written
# version of "what we sell" would immediately risk drifting from the real one.
# ---------------------------------------------------------------------------

def draft_followup_email(db, lead_id, product_brief: dict, lead_profile: dict, pain_points: list,
                         followup_level: int, qc_feedback: str | None = None,
                         content_assets: list | None = None, tone_directive: str | None = None,
                         format_directive: str | None = None,
                         recent_rejection_patterns: list | None = None):
    """followup_level: 1 (re-present the asset), 2 (ask an open question), or 3 (standing
    offer -- the products list itself is appended by the caller, not drafted here).
    Returns {subject, subject_candidates, body, sections, hook_type, confidence}, or None.

    `tone_directive`/`format_directive` (Phase 16 Step 16.4) -- see draft_structured_
    email()'s own docstring; same optional style guideline, applied consistently across
    every touch of this product's sequence, not just touch 1.
    """
    has_asset = bool(_pick_asset(content_assets, "VIDEO_URL") or _pick_asset(content_assets, CTA_BUTTON_ASSET_TYPE))
    level_instruction = {
        1: FOLLOWUP_LEVEL_1_WITH_ASSET if has_asset else FOLLOWUP_LEVEL_1_NO_ASSET,
        2: FOLLOWUP_LEVEL_2,
        3: FOLLOWUP_LEVEL_3,
    }[followup_level]

    prompt = FOLLOWUP_LEVEL_SYSTEM_PROMPT + f"""
PRODUCT: {json.dumps(product_brief, ensure_ascii=False)}
LEAD: {json.dumps(lead_profile, ensure_ascii=False)}
PAIN_POINTS: {json.dumps(pain_points, ensure_ascii=False)}
CHANNEL: EMAIL
""" + level_instruction
    if recent_rejection_patterns:
        prompt += f"""
RECENT_REJECTION_PATTERNS_IN_THIS_CAMPAIGN -- QC's real rejection reasons for OTHER
leads in this same campaign, most recent first. Avoid repeating the same mistake if one
of these applies here too:
{json.dumps(recent_rejection_patterns, ensure_ascii=False)}
"""
    if tone_directive or format_directive:
        prompt += f"""
TONE_AND_FORMAT: the admin has set a preferred style for this product's outreach.
{f"TONE: {tone_directive}" if tone_directive else ""}
{f"FORMAT: {format_directive}" if format_directive else ""}
Write in this style throughout, while keeping every fact grounded exactly as already
required -- this changes HOW it's said, never WHAT is claimed.
"""
    if qc_feedback:
        prompt += f"""
YOUR PREVIOUS DRAFT(S) WERE REJECTED BY QUALITY CONTROL. {qc_feedback}
If more than one correction is numbered above, apply ALL of them together -- they are
corrections from separate earlier attempts, and fixing a later one must never silently
undo an earlier one (e.g. don't re-add something attempt 1 already told you to remove).
"""

    try:
        data = call_json(prompt, temperature=0.4)
    except LLMError as exc:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_FOLLOWUP_EMAIL", 0.0, "MEDIUM", "LLM_FAILED",
                        payload={"error": str(exc), "followup_level": followup_level})
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

    hook = _clean_line(data.get("hook"))
    sections = [{"type": "HOOK", "text": hook}] if hook else []
    if followup_level == 1:
        # Same real, approved asset touch 1 would have shown -- _pick_asset's own
        # determinism (always the first matching real asset) is what makes this a
        # genuine "re-presentation" rather than a coincidence.
        sections += _asset_sections(content_assets)
        demo = _pick_asset(content_assets, CTA_BUTTON_ASSET_TYPE)
        if demo:
            sections.append({"type": "CTA", "headline": "", "subtext": "",
                            "button_url": demo["value"],
                            "button_label": _clean_line(demo.get("title"), 40) or "See the demo"})

    body = _sections_to_text(sections)
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = 0.0

    has_hook = any(s["type"] == "HOOK" for s in sections)
    if not subject or not has_hook:
        log_agent_event(db, "OUTREACH", lead_id, "DRAFT_FOLLOWUP_EMAIL", confidence, "MEDIUM",
                        "EMPTY_DRAFT", payload={"followup_level": followup_level,
                                                "section_types": [s["type"] for s in sections]})
        return None

    draft = {
        "subject": subject,
        "subject_candidates": subject_candidates or [subject],
        "body": body,
        "sections": sections,
        "hook_type": f"FOLLOWUP_LEVEL_{followup_level}",
        "confidence": confidence,
    }
    log_agent_event(db, "OUTREACH", lead_id, "DRAFT_FOLLOWUP_EMAIL", confidence, "MEDIUM", "DRAFTED",
                    payload={"followup_level": followup_level,
                            "section_types": [s["type"] for s in sections]})
    return draft
