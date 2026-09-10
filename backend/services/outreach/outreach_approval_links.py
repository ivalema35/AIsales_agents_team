"""2026-09-10, real user ask -- HMAC-signed one-click links that let an admin approve
real outreach for ONE channel of ONE campaign, straight from the test email
(services/campaign_service.send_test_outreach_preview). Same signing discipline as
services/outreach/interest_links.py (a forged link here would falsely unlock real sends
to real leads, so it's signed, not just an unauthenticated id in a URL) -- deliberately
no token table, same reasoning as interest_links.py: signing needs the secret, not a
database lookup, and needs no new storage. Verified in api/outreach_approval.py; a bad,
expired, or altered token is refused outright, never partially trusted.
"""
from __future__ import annotations
import hashlib
import hmac

from config import Config

VALID_CHANNELS = ("EMAIL", "WHATSAPP")


def _sign(campaign_id: str, channel: str) -> str:
    message = f"{campaign_id}:{channel}".encode()
    return hmac.new(Config.INTEREST_LINK_SECRET.encode(), message, hashlib.sha256).hexdigest()


def verify_outreach_approval_token(campaign_id: str, channel: str, token: str) -> bool:
    if channel not in VALID_CHANNELS or not token:
        return False
    expected = _sign(campaign_id, channel)
    return hmac.compare_digest(expected, token)


def build_outreach_approval_urls(campaign_id: str) -> dict:
    """Called once, right when the test preview is sent -- both links point at the SAME
    campaign, one per channel, so the admin can approve either or both independently."""
    base = f"{Config.PUBLIC_BASE_URL}/api/v1/outreach-approval/{campaign_id}"
    return {
        "email_approve_url": f"{base}/EMAIL/{_sign(campaign_id, 'EMAIL')}",
        "whatsapp_approve_url": f"{base}/WHATSAPP/{_sign(campaign_id, 'WHATSAPP')}",
    }
