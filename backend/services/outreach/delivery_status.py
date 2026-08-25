"""Phase 14 Step 14.1 -- a real, honest per-message delivery state, derived from data
this project already collects (Step 14.1's own premise: nothing new collected, only
surfaced). "Replied" beats every other signal (undeniable proof the lead actually
received it, regardless of what a status webhook separately reported); then "Seen"
(read_at, set by Resend's open-tracking pixel for EMAIL or Meta's own read receipt for
WHATSAPP); then whatever OutreachLog.status itself says (SENT/DELIVERED/FAILED/BOUNCED).
No state is ever guessed -- a channel/event this project genuinely has no signal for
falls through to the caller's own "--" display, never an optimistic label.
"""
from __future__ import annotations

_FAILURE_STATUSES = {"FAILED", "BOUNCED"}


def derive_delivery_state(log, has_reply: bool) -> str:
    if has_reply:
        return "Replied"
    if log.read_at is not None:
        return "Seen"
    if log.status in _FAILURE_STATUSES:
        return "Failed"
    if log.status == "DELIVERED":
        return "Delivered"
    return "Sent"


def resolve_whatsapp_display_text(log) -> str:
    """Step 14.2 -- every send from here forward already stores the real filled-in text
    directly in `message_body` (jobs/outreach_wa_handler.py). This exists purely for
    BACKWARD COMPATIBILITY with real rows sent before that change, which stored a
    `{"template": ..., "variables": [...]}` JSON blob instead -- reconstructed here for
    display only, the stored row itself is never rewritten (this project never silently
    rewrites real historical records). Falls back to the raw stored value unchanged if
    it isn't that old JSON shape, or if the real template's wording can no longer be
    resolved (e.g. a template deleted since) -- never raises on a real, already-sent row.
    """
    import json as _json
    from services.outreach.whatsapp_templates import TEMPLATE_LIBRARY, interpolate_template

    raw = log.message_body or ""
    if not raw.startswith("{"):
        return raw  # already the real text (current format) -- nothing to reconstruct
    try:
        blob = _json.loads(raw)
    except (TypeError, ValueError):
        return raw
    if not isinstance(blob, dict) or "template" not in blob:
        return raw

    template_name = blob.get("template")
    variables = blob.get("variables") or []

    body_text = next(
        (spec.get("body_text") for spec in TEMPLATE_LIBRARY.values() if spec.get("name") == template_name),
        None,
    )
    if not body_text:
        from database.db_config import SessionLocal
        from database.models import WhatsappTemplate
        db = SessionLocal()
        try:
            row = db.query(WhatsappTemplate).filter(WhatsappTemplate.name == template_name).first()
            body_text = row.body_text if row else None
        finally:
            db.close()

    if not body_text:
        return raw  # real template wording no longer resolvable -- show the raw stored value, not a guess
    return interpolate_template(body_text, variables)
