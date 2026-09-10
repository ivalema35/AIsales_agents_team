"""2026-09-10, real user ask -- the public one-click landing for the "approve real
outreach" links embedded in a campaign's test preview email. Same "plain GET link, no
page/JS/confirmation step" posture as api/interest.py -- clicking the link IS the
action. Mounted under "/api/v1/" (not a bare prefix) because production's real
webserver only proxies that prefix to Flask -- see the interest/unsubscribe bug fixed
earlier this same day for exactly why a bare prefix would silently never be reached.
"""
from __future__ import annotations
from datetime import datetime

from flask import Blueprint

from database.db_config import SessionLocal
from database.models import Campaign
from services.outreach.outreach_approval_links import verify_outreach_approval_token

outreach_approval_bp = Blueprint("outreach_approval", __name__, url_prefix="/api/v1/outreach-approval")


@outreach_approval_bp.route("/<campaign_id>/<channel>/<token>", methods=["GET"])
def approve_outreach(campaign_id, channel, token):
    if not verify_outreach_approval_token(campaign_id, channel, token):
        return "Invalid or expired link.", 404

    db = SessionLocal()
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return "Invalid or expired link.", 404

        if channel == "EMAIL":
            campaign.email_outreach_approved_at = datetime.utcnow()
        else:
            campaign.whatsapp_outreach_approved_at = datetime.utcnow()
        db.commit()

        channel_label = "EMAIL" if channel == "EMAIL" else "WhatsApp"
        return f"Real {channel_label} outreach for \"{campaign.name}\" is now live.", 200
    finally:
        db.close()
