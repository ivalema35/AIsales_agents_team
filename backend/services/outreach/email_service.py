"""Compliant email sending via Resend (MASTER Phase 3 / Step 3.3).

Every email gets a footer with the company's physical address and a working
unsubscribe link, appended HERE -- not by the Outreach Agent -- so compliance can never
depend on an LLM remembering to include it. This is the only module in the project that
calls Resend, matching the pattern already used for other single-purpose external
integrations (b2b_provider.py for Hunter, etc.).
"""
import html
import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def _build_footer(unsubscribe_url: str) -> str:
    return (
        f"\n\n---\n{Config.COMPANY_PHYSICAL_ADDRESS}\n"
        f"Don't want these emails? Unsubscribe here: {unsubscribe_url}"
    )


def _build_html(body_text: str, unsubscribe_url: str) -> str:
    """HTML variant so the unsubscribe link renders as an actual button, not a bare
    URL string, while the plain-`text` part (still sent alongside) stays the compliance
    fallback for clients that don't render HTML."""
    body_html = html.escape(body_text.rstrip()).replace("\n", "<br>")
    address_html = html.escape(Config.COMPANY_PHYSICAL_ADDRESS)
    return f"""
<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1a1a1a; line-height: 1.5;">
  <p>{body_html}</p>
  <hr style="border: none; border-top: 1px solid #ddd; margin: 24px 0;">
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


def send_email(to_email: str, subject: str, body_text: str, unsubscribe_url: str) -> dict:
    """Sends via Resend's REST API directly (plain `requests`, no SDK dependency --
    consistent with every other external call in this project). Raises on failure
    rather than swallowing it: the caller is a job handler that already has the job
    queue's retry/DEAD handling, so an exception here is the correct way to signal
    "this send did not happen, please retry" rather than silently returning a failure
    dict that a caller might forget to check.
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
            "html": _build_html(body_text, unsubscribe_url),
            "headers": {"List-Unsubscribe": f"<{unsubscribe_url}>"},
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("email sent to %s (resend id=%s)", to_email, data.get("id"))
    return data
