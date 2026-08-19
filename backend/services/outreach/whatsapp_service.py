"""WhatsApp Cloud API sending, via a Meta-compatible BSP (waba.fortius.in.net) --
confirmed live (tracker.md, 2026-08-13) to mirror Meta's real Cloud API path structure
exactly (`/{version}/{phoneNumberId}/messages`), just fronted by their own API server
instead of graph.facebook.com. Request/response shape follows Meta's own Cloud API
documentation directly.

Template-based only (MASTER non-negotiable rule: first-contact only via a pre-approved
template, never free-form). Free-form messages are only legal within a 24h reply window
and belong to Phase 4's inbound flow, not here.
"""
from __future__ import annotations
import logging

import requests

from config import Config

logger = logging.getLogger(__name__)


def _messages_url():
    return f"{Config.WHATSAPP_API_BASE_URL}/{Config.WHATSAPP_API_VERSION}/{Config.WHATSAPP_PHONE_ID}/messages"


def extract_wamid(send_response: dict) -> str | None:
    """Meta's send response shape is `{"messages": [{"id": "wamid.XXX"}], ...}` -- this
    id is what a later read-receipt status webhook references, so callers that want
    "Seen" tracking (OutreachLog.provider_message_id) pull it via this helper rather
    than each reaching into the response dict themselves."""
    messages = send_response.get("messages") or []
    return messages[0].get("id") if messages else None


def send_template_message(to_phone: str, template_name: str, language_code: str, variables: list) -> dict:
    """`to_phone` must be full international format with country code, no leading '+'
    (Meta's convention, e.g. '919876543210'). Raises on failure -- same contract as
    email_service.send_email, the caller's job-queue retry/DEAD handling takes over.
    """
    if not Config.WHATSAPP_TOKEN:
        raise RuntimeError("WHATSAPP_TOKEN not configured")
    if not Config.WHATSAPP_PHONE_ID:
        raise RuntimeError("WHATSAPP_PHONE_ID not configured")

    components = []
    if variables:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": str(v)} for v in variables],
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": components,
        },
    }

    resp = requests.post(
        _messages_url(),
        headers={
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("whatsapp template '%s' sent to %s", template_name, to_phone)
    return data


def send_free_form_message(to_phone: str, body_text: str) -> dict:
    """Plain text (non-template) send -- only legal within Meta's 24h customer-service
    window after the recipient's own last inbound message (their MASTER-cited rule, same
    reasoning noted in this module's docstring). Used for Step 4.3's acknowledgment reply,
    sent immediately in response to a message that JUST arrived, so the window is always
    open by construction -- never call this outside that context."""
    if not Config.WHATSAPP_TOKEN:
        raise RuntimeError("WHATSAPP_TOKEN not configured")
    if not Config.WHATSAPP_PHONE_ID:
        raise RuntimeError("WHATSAPP_PHONE_ID not configured")

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": body_text},
    }

    resp = requests.post(
        _messages_url(),
        headers={
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("whatsapp free-form message sent to %s", to_phone)
    return data
