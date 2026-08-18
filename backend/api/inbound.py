"""WhatsApp inbound webhook (MASTER Phase 4 / Step 4.1). Meta's Cloud API pushes
messages here; email inbound is handled separately by jobs/inbound_poller.py (IMAP
polling, no webhook needed -- see tracker.md's Step 4.1 discussion).
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from config import Config
from database.db_config import SessionLocal
from database.models import InboundConversation, OutreachLog
from services.data_acquisition.website_scraper import normalize_mobile
from services.inbound_service import record_inbound

logger = logging.getLogger(__name__)

inbound_bp = Blueprint("inbound", __name__, url_prefix="/api/v1/inbound")


@inbound_bp.route("/whatsapp", methods=["GET"])
def verify_whatsapp_webhook():
    """Meta's one-time webhook verification handshake -- run when you register this URL
    in the Meta/BSP dashboard. Echoes hub.challenge back only if the verify token matches
    what's configured, so a stranger can't just probe this URL to confirm it's real."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token and Config.WHATSAPP_WEBHOOK_VERIFY_TOKEN and \
            token == Config.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return challenge or "", 200
    return "verification failed", 403


@inbound_bp.route("/whatsapp", methods=["POST"])
def receive_whatsapp():
    """Always returns 200 quickly (Meta retries aggressively on non-200) -- real
    processing errors are logged, not surfaced as a webhook failure Meta would hammer
    retry on. Idempotency (record_inbound's dedup) makes a retried delivery harmless
    anyway."""
    payload = request.get_json(silent=True) or {}

    db = SessionLocal()
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    _handle_one_message(db, msg)
                # Meta's delivery-status callbacks land in a SEPARATE "statuses" array,
                # not "messages" -- previously silently ignored entirely (found live:
                # this is real "Seen" data Meta already sends, just never read).
                for status in value.get("statuses", []):
                    _handle_one_status(db, status)
    except Exception:  # noqa: BLE001 - never let a malformed/unexpected payload 500 a webhook
        logger.exception("failed processing WhatsApp webhook payload")
    finally:
        db.close()

    return jsonify({"status": "received"}), 200


@inbound_bp.route("/<conversation_id>/read", methods=["PATCH"])
def mark_read(conversation_id):
    """Dashboard's Recent Replies grid -- clicking 'Mark as read' drops that reply out
    of the list (the GET /leads/recent-replies query only returns is_read=0 rows)."""
    db = SessionLocal()
    try:
        conv = db.get(InboundConversation, conversation_id)
        if not conv:
            return jsonify({"error": "conversation not found"}), 404
        conv.is_read = 1
        db.commit()
        return jsonify({"id": conv.id, "is_read": True})
    finally:
        db.close()


def _handle_one_status(db, status: dict):
    """Meta's message-status callback ("sent"/"delivered"/"read"/"failed") -- only
    "read" is acted on, since this exists specifically for the Sent/Seen/Replied
    analytics funnel. Matched back to the OutreachLog row we created at send time via
    `provider_message_id` (Meta's own wamid, captured in outreach_wa_handler.py /
    inbound_classify_handler.py's _send_reply_message)."""
    if status.get("status") != "read":
        return
    wamid = status.get("id")
    if not wamid:
        return
    log = db.query(OutreachLog).filter(OutreachLog.provider_message_id == wamid).first()
    if not log:
        # A read receipt for a message sent before this tracking existed, or one this
        # system didn't send -- nothing to attach it to, not an error.
        return
    if log.read_at is None:  # keep the FIRST read timestamp, ignore any re-delivered duplicate
        log.read_at = datetime.utcnow()
        db.commit()
        logger.info("WhatsApp read receipt: outreach_log %s marked read", log.id)


def _handle_one_message(db, msg: dict):
    msg_type = msg.get("type")
    if msg_type != "text":
        logger.info("WhatsApp inbound: skipping non-text message type=%s", msg_type)
        return

    raw_from = msg.get("from", "")
    # Meta sends international format with no '+' (e.g. "919876543210") -- strip the
    # country code so this matches how we store/normalize numbers everywhere else
    # (normalize_mobile() -> bare 10-digit Indian mobile, same as outbound sending).
    sender = normalize_mobile(raw_from[2:] if raw_from.startswith("91") else raw_from)
    message_id = msg.get("id")
    body = (msg.get("text") or {}).get("body", "")

    if not sender or not message_id:
        logger.warning("WhatsApp inbound: unusable message (from=%s, id=%s)", raw_from, message_id)
        return

    record_inbound(db, "WHATSAPP", sender, message_id, body)
