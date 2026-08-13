"""Compliant email sending via Resend (MASTER Phase 3 / Step 3.3).

Every email gets a footer with the company's physical address and a working
unsubscribe link, appended HERE -- not by the Outreach Agent -- so compliance can never
depend on an LLM remembering to include it. This is the only module in the project that
calls Resend, matching the pattern already used for other single-purpose external
integrations (b2b_provider.py for Hunter, etc.).
"""
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
            "from": Config.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": full_body,
            "headers": {"List-Unsubscribe": f"<{unsubscribe_url}>"},
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("email sent to %s (resend id=%s)", to_email, data.get("id"))
    return data
