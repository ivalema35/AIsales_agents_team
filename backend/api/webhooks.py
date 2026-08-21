"""Resend email-event webhook -- the "Seen" half of the Sent/Seen/Replied funnel for
EMAIL (WhatsApp's own half lives in api/inbound.py, since Meta delivers it through the
same webhook as inbound messages; Resend needs its own separate endpoint).

Setup this system CANNOT do for itself (needs the user's Resend dashboard):
1. Resend dashboard -> Webhooks -> add endpoint -> this route's full public URL
   (PUBLIC_BASE_URL + /api/v1/webhooks/resend), subscribed to at least "email.opened".
2. Resend account/domain settings -> enable open tracking (off by default on some
   plans) -- without it, Resend never fires email.opened at all, regardless of this
   endpoint existing. Open tracking itself is inherently approximate (depends on the
   recipient's client auto-loading a tracking pixel) -- real signal, just not 1:1 with
   every actual open the way a WhatsApp read receipt is.

Signature verification (Resend signs webhooks via Svix) is NOT implemented here --
same accepted risk posture as the WhatsApp webhook (tracker.md: low risk while the URL
is a random, not-widely-shared address). Worth adding before this is load-bearing for
anything beyond an analytics count.
"""
from __future__ import annotations
import logging

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import OutreachLog
from datetime import datetime

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/v1/webhooks")

# Any of these count as "seen" for the funnel -- an open is the direct signal; a click
# necessarily implies the email was seen even if the open-pixel itself got blocked
# (common with image-blocking clients), so it's a legitimate second path to the same fact.
_SEEN_EVENT_TYPES = {"email.opened", "email.clicked"}


@webhooks_bp.route("/resend", methods=["POST"])
def resend_event():
    """Always returns 200 quickly, same reasoning as the WhatsApp webhook -- a
    processing error here should never make Resend hammer retries."""
    payload = request.get_json(silent=True) or {}
    event_type = payload.get("type")

    db = SessionLocal()
    try:
        if event_type in _SEEN_EVENT_TYPES:
            email_id = (payload.get("data") or {}).get("email_id")
            if email_id:
                log = db.query(OutreachLog).filter(OutreachLog.provider_message_id == email_id).first()
                if log:
                    changed = False
                    if log.read_at is None:
                        log.read_at = datetime.utcnow()
                        changed = True
                    # Phase 9 Step 9.4 -- a real per-open count, distinct from read_at
                    # (which only ever marks the first open). Only "email.opened" counts
                    # here -- "email.clicked" already implies an open but is a different
                    # real event, counting it too would inflate the open count.
                    if event_type == "email.opened":
                        log.open_count = (log.open_count or 0) + 1
                        changed = True
                    if changed:
                        db.commit()
                        logger.info("Resend %s: outreach_log %s marked read (open_count=%s)",
                                   event_type, log.id, log.open_count)
    except Exception:  # noqa: BLE001 - never let a malformed/unexpected payload 500 a webhook
        logger.exception("failed processing Resend webhook payload")
    finally:
        db.close()

    return jsonify({"status": "received"}), 200
