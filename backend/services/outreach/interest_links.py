"""Phase 12 Step 12.2 -- HMAC-signed one-click Yes/No interest links.

Same unauthenticated public-route class as the existing one-click unsubscribe link
(Config.PUBLIC_BASE_URL) -- but a forged unsubscribe link's worst case is harmless in
the wrong direction (someone gets opted out who didn't ask to be), while a forged Yes/No
here would falsely escalate a lead and fire a real admin alert. So this one is signed:
HMAC-SHA256 over lead_id+outreach_log_id+response, keyed by a secret only this server
knows. Deliberately no token table (same reasoning as the unsubscribe link) -- signing
makes forging one require the secret, not a database lookup, and needs no new storage.
A bad, expired, or altered token is refused outright in api/interest.py -- never
partially trusted, never resolved to a "probably this lead" guess.
"""
from __future__ import annotations
import hashlib
import hmac

from config import Config

VALID_RESPONSES = ("YES", "NO")


def _sign(lead_id: str, outreach_log_id: str, response: str) -> str:
    message = f"{lead_id}:{outreach_log_id}:{response}".encode()
    return hmac.new(Config.INTEREST_LINK_SECRET.encode(), message, hashlib.sha256).hexdigest()


def verify_interest_token(lead_id: str, outreach_log_id: str, response: str, token: str) -> bool:
    if response not in VALID_RESPONSES or not token:
        return False
    expected = _sign(lead_id, outreach_log_id, response)
    return hmac.compare_digest(expected, token)


def build_interest_urls(lead_id: str, outreach_log_id: str) -> dict:
    """Called at send time, once the sending OutreachLog's id is already known (it's
    pre-generated in jobs/outreach_handler.py specifically so these links can be built
    and embedded BEFORE the row itself is inserted)."""
    base = f"{Config.PUBLIC_BASE_URL}/interest/{lead_id}/{outreach_log_id}"
    return {
        "yes_url": f"{base}/YES/{_sign(lead_id, outreach_log_id, 'YES')}",
        "no_url": f"{base}/NO/{_sign(lead_id, outreach_log_id, 'NO')}",
    }
