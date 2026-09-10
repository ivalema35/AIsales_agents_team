"""Phase 12 Step 12.2 -- public one-click Yes/No interest capture.

Same "plain GET link, no page/JS/confirmation step" posture as api/unsubscribe.py --
clicking the link in the email IS the action. Unlike unsubscribe, the token here is
HMAC-verified (see services/outreach/interest_links.py for why): a bad, expired, or
altered token is refused outright, never partially trusted.

2026-09-10 real live bug fix: this used to be mounted at a bare "/interest" prefix.
Production's real webserver (OpenLiteSpeed, see reference_production_static_file_
serving finding) only proxies "/api/" to Flask -- everything else falls through to
the SPA's index.html unless a real file exists at that exact path. That meant every
real lead's "Yes"/"No" click in a real sent email was silently landing on the
dashboard's index.html instead of ever reaching this code -- confirmed live via a
direct fetch of the real production URL returning the SPA shell (821 bytes,
text/html), never this blueprint. Moved under "/api/v1/" so it's actually reachable.
"""
from __future__ import annotations
from flask import Blueprint

from database.db_config import SessionLocal
from database.models import Lead, OutreachLog
from services.outreach.interest_links import verify_interest_token
from services.outreach.interest_service import record_interest_response

interest_bp = Blueprint("interest", __name__, url_prefix="/api/v1/interest")

_THANKS = {
    "YES": "Thanks! We've noted your interest -- someone from our team will reach out shortly.",
    "NO": "Got it -- thanks for letting us know.",
}


@interest_bp.route("/<lead_id>/<outreach_log_id>/<response>/<token>", methods=["GET"])
def interest_response(lead_id, outreach_log_id, response, token):
    if not verify_interest_token(lead_id, outreach_log_id, response, token):
        return "Invalid or expired link.", 404

    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        log = db.get(OutreachLog, outreach_log_id)
        # The token proves lead_id+outreach_log_id+response were signed TOGETHER, but a
        # lead deleted since send, or a log belonging to a different lead, would still
        # pass verification against a stale/mismatched pair -- checked explicitly rather
        # than trusted from the token alone.
        if not lead or not log or log.lead_id != lead.id:
            return "Invalid or expired link.", 404

        record_interest_response(db, lead, log, response)
        return _THANKS[response], 200
    finally:
        db.close()
