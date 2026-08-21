"""Compliant email sending via Resend (MASTER Phase 3 / Step 3.3).

Every email gets a footer with the company's physical address and a working
unsubscribe link, appended HERE -- not by the Outreach Agent -- so compliance can never
depend on an LLM remembering to include it. This is the only module in the project that
calls Resend, matching the pattern already used for other single-purpose external
integrations (b2b_provider.py for Hunter, etc.).
"""
from __future__ import annotations
import html
import logging
import re

import requests

from config import Config

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"

_URL_RE = re.compile(r"(https?://[^\s<]+)")


def extract_resend_id(send_response: dict) -> str | None:
    """Resend's send response is `{"id": "..."}` -- this is what a later `email.opened`
    webhook event references (`data.email_id`), so callers that want "Seen" tracking
    (OutreachLog.provider_message_id) pull it via this helper rather than reaching into
    the response dict themselves."""
    return send_response.get("id")


def _build_footer(unsubscribe_url: str) -> str:
    return (
        f"\n\n---\n{Config.COMPANY_PHYSICAL_ADDRESS}\n"
        f"Don't want these emails? Unsubscribe here: {unsubscribe_url}"
    )


def _linkify(escaped_text: str) -> str:
    """Turns a bare URL (already HTML-escaped, so no raw '&', '<', '>' to worry about
    inside the match) into a real clickable link -- the AI writes URLs as plain text in
    its draft, and until now that stayed plain text in the sent HTML too."""
    return _URL_RE.sub(r'<a href="\1" style="color: #2563eb;">\1</a>', escaped_text)


def _fetch_video_thumbnail(video_url: str) -> str | None:
    """Real oEmbed lookup (YouTube/Vimeo's own public, no-auth-needed endpoints) for a
    real thumbnail image of a real video URL -- never fabricated, never a generic
    placeholder. Returns None for any unsupported provider or a failed lookup; a missing
    thumbnail must never block or break a real send, it just means no image block."""
    try:
        if "youtube.com" in video_url or "youtu.be" in video_url:
            resp = requests.get("https://www.youtube.com/oembed",
                                params={"url": video_url, "format": "json"}, timeout=5)
            resp.raise_for_status()
            return resp.json().get("thumbnail_url")
        if "vimeo.com" in video_url:
            resp = requests.get("https://vimeo.com/api/oembed.json",
                                params={"url": video_url}, timeout=5)
            resp.raise_for_status()
            return resp.json().get("thumbnail_url")
    except Exception as exc:  # noqa: BLE001 - display-only, must never break a real send
        logger.warning("video thumbnail lookup failed for %s: %s", video_url, exc)
    return None


def _build_video_block(body_text: str, content_assets) -> str:
    """A real, clickable thumbnail image for a VIDEO_URL asset the draft actually
    references -- only ever built from a real asset genuinely mentioned in this specific
    draft, never from an asset merely available for the product but unused this time."""
    for asset in content_assets or []:
        if asset.get("asset_type") != "VIDEO_URL":
            continue
        video_url = asset.get("value")
        if not video_url or video_url not in body_text:
            continue
        thumbnail_url = _fetch_video_thumbnail(video_url)
        if not thumbnail_url:
            return ""
        safe_url, safe_thumb = html.escape(video_url), html.escape(thumbnail_url)
        return f"""
  <p>
    <a href="{safe_url}">
      <img src="{safe_thumb}" alt="Watch video" style="max-width: 320px; border-radius: 8px; display: block;">
    </a>
    <a href="{safe_url}" style="font-size: 13px; color: #2563eb;">&#9654; Watch the video</a>
  </p>
"""
    return ""


def _build_html(body_text: str, unsubscribe_url: str, content_assets=None) -> str:
    """HTML variant so the unsubscribe link renders as an actual button, not a bare
    URL string, while the plain-`text` part (still sent alongside) stays the compliance
    fallback for clients that don't render HTML. Any URL in the body is now a real
    clickable link (2026-08-21 follow-up), and a VIDEO_URL asset the draft actually
    references gets a real thumbnail image beneath the text -- video itself still can't
    play inside an email (no email client supports that), so this is a real, clickable
    preview, not fabricated playback.
    """
    body_html = _linkify(html.escape(body_text.rstrip())).replace("\n", "<br>")
    video_html = _build_video_block(body_text, content_assets)
    address_html = html.escape(Config.COMPANY_PHYSICAL_ADDRESS)
    return f"""
<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1a1a1a; line-height: 1.5;">
  <p>{body_html}</p>
{video_html}  <hr style="border: none; border-top: 1px solid #ddd; margin: 24px 0;">
  <p style="color: #666; font-size: 12px;">{address_html}</p>
  <a href="{unsubscribe_url}"
     style="display: inline-block; padding: 8px 16px; background: #f2f2f2; color: #333;
            border: 1px solid #ccc; border-radius: 4px; text-decoration: none; font-size: 12px;">
    Unsubscribe
  </a>
</div>
""".strip()


def _from_header() -> str:
    """'Display Name <email>' when RESEND_FROM_NAME is set -- reads as a real person in
    the recipient's inbox rather than a bare address (Resend's documented from format)."""
    if Config.RESEND_FROM_NAME:
        return f"{Config.RESEND_FROM_NAME} <{Config.RESEND_FROM_EMAIL}>"
    return Config.RESEND_FROM_EMAIL


def send_email(to_email: str, subject: str, body_text: str, unsubscribe_url: str,
               content_assets=None) -> dict:
    """Sends via Resend's REST API directly (plain `requests`, no SDK dependency --
    consistent with every other external call in this project). Raises on failure
    rather than swallowing it: the caller is a job handler that already has the job
    queue's retry/DEAD handling, so an exception here is the correct way to signal
    "this send did not happen, please retry" rather than silently returning a failure
    dict that a caller might forget to check.

    `content_assets` (2026-08-21 follow-up) is the same list already resolved for
    drafting -- passed through here only so a VIDEO_URL asset the draft actually
    references can get a real clickable thumbnail in the HTML version. Optional and
    None-safe: omitting it is identical to today's plain-linkified-text behavior.
    """
    if not Config.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not configured")

    full_body = body_text.rstrip() + _build_footer(unsubscribe_url)

    resp = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {Config.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": _from_header(),
            "to": [to_email],
            "subject": subject,
            "text": full_body,
            "html": _build_html(body_text, unsubscribe_url, content_assets),
            "headers": {"List-Unsubscribe": f"<{unsubscribe_url}>"},
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("email sent to %s (resend id=%s)", to_email, data.get("id"))
    return data


def send_internal_email(to_email: str, subject: str, body_text: str) -> dict:
    """Plain internal email, no compliance footer/unsubscribe link -- this is the
    project's own EOD report (Step 4.5) going to the business owner, not outreach to a
    lead, so send_email()'s mandatory footer doesn't apply and would be confusing here."""
    if not Config.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not configured")

    resp = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {Config.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"from": _from_header(), "to": [to_email], "subject": subject, "text": body_text},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("internal email sent to %s (resend id=%s)", to_email, data.get("id"))
    return data
