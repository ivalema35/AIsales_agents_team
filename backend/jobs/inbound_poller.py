"""Inbound email poller (MASTER Phase 4 / Step 4.1). IMAP-polls the reply-monitored
mailbox instead of a webhook -- a real reply to our outreach lands via normal SMTP/MX
routing at Hostinger, not through Resend (Resend only handles what WE send), so there is
no webhook Resend could push to us even if we had a public URL. Polling the mailbox
directly needs no public URL at all (tracker.md Step 4.1 discussion, 2026-08-13).

Run as `python -m jobs.inbound_poller`, alongside the other always-on processes.
"""
from __future__ import annotations
import email
import imaplib
import logging
import re
import time
from datetime import datetime, timedelta
from email.utils import parseaddr

from config import Config
from database.db_config import SessionLocal
from services.inbound_service import record_inbound
from services.heartbeat import beat_standalone

logger = logging.getLogger(__name__)

HEARTBEAT_NAME = "jobs.inbound_poller"


def _extract_body(msg) -> str:
    """Prefers the plain-text part; falls back to a naive HTML-tag strip if a message
    only has an HTML body (common from webmail clients)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    return re.sub(r"<[^>]+>", " ", html)
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


IMAP_TIMEOUT_SECONDS = 30  # well under the 120s poll interval -- fail fast, retry next cycle


def check_inbox() -> int:
    """One poll cycle: connect, pull recent messages, record each (record_inbound's own
    DB-level UNIQUE constraint is what actually guarantees idempotency -- this only
    bounds how much IMAP fetches per cycle, it is not itself the dedup mechanism, so a
    message can never be silently missed by an IMAP-flag race).

    Real incident, 2026-08-22: found live on the VPS -- the poller's own systemd unit
    stayed "active (running)" and every heartbeat/log line simply stopped for ~17 hours,
    with zero exception ever logged, zero crash. Root cause: `imaplib.IMAP4_SSL()` (and
    every socket op on the connection it returns) blocks with NO timeout by default -- a
    silently-dropped TCP connection (no FIN/RST received) hangs the read forever, so
    run_forever()'s own `except Exception` safety net below never even fires; the process
    just sits frozen inside this function, invisible from the outside. A bare restart
    fixes the symptom for a while but not the recurrence. Fix: pass a real timeout so a
    hung connection raises `socket.timeout` instead of hanging -- run_forever() already
    catches that, logs it, reports ERROR status (visible on the dashboard), and retries
    next cycle, instead of dying silently for hours."""
    if not Config.INBOUND_EMAIL_HOST:
        logger.warning("INBOUND_EMAIL_HOST not configured -- skipping this cycle")
        return 0

    conn = imaplib.IMAP4_SSL(Config.INBOUND_EMAIL_HOST, Config.INBOUND_EMAIL_PORT,
                             timeout=IMAP_TIMEOUT_SECONDS)
    try:
        conn.login(Config.INBOUND_EMAIL_USER, Config.INBOUND_EMAIL_PASSWORD)
        conn.select("INBOX")

        since = (datetime.utcnow() - timedelta(days=3)).strftime("%d-%b-%Y")
        status, data = conn.search(None, f'(SINCE "{since}")')
        if status != "OK" or not data or not data[0]:
            return 0

        db = SessionLocal()
        recorded = 0
        try:
            for msg_id in data[0].split():
                status, msg_data = conn.fetch(msg_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])

                message_id = msg.get("Message-ID") or f"no-msgid-{msg_id.decode()}"
                _, sender_email = parseaddr(msg.get("From", ""))
                sender_email = sender_email.lower().strip()
                body = _extract_body(msg).strip()[:5000]

                if not sender_email or not body:
                    continue
                # Real auto-reply headers (RFC 3834 etc.) are far more reliable than
                # body-text guessing when present -- Step 4.2's is_autoreply() checks
                # these first, only falls back to body text if none are set.
                headers = {k: msg.get(k) for k in
                          ("Auto-Submitted", "X-Autoreply", "X-Autorespond", "X-Auto-Response-Suppress")
                          if msg.get(k)}
                if record_inbound(db, "EMAIL", sender_email, message_id, body, email_headers=headers):
                    recorded += 1
        finally:
            db.close()
        return recorded
    finally:
        conn.logout()


def run_forever(poll_interval=None):
    poll_interval = poll_interval or Config.INBOUND_POLL_INTERVAL_SECONDS
    logger.info("inbound email poller started (poll=%ds, mailbox=%s)",
               poll_interval, Config.INBOUND_EMAIL_USER)
    beat_standalone(HEARTBEAT_NAME, status="RUNNING", is_startup=True,
                    expected_interval_seconds=poll_interval)

    while True:
        status, detail = "RUNNING", None
        try:
            recorded = check_inbox()
            if recorded:
                logger.info("inbound poller -> recorded %d new message(s)", recorded)
                detail = {"last_recorded": recorded}
        except Exception:  # noqa: BLE001 - one bad IMAP cycle must not kill the poller
            logger.exception("inbound poller tick failed")
            # A poller whose IMAP connection is broken keeps looping and looks perfectly alive
            # from the outside -- inbound replies just silently stop arriving. Reporting ERROR
            # is the only way that failure becomes visible without reading logs.
            status = "ERROR"
        beat_standalone(HEARTBEAT_NAME, status=status, detail=detail,
                        force=(status == "ERROR"),
                        expected_interval_seconds=poll_interval)
        time.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_forever()
