"""One-click unsubscribe (MASTER's compliant-email requirement, QC checklist rule 4).

Deliberately a plain GET link, not a form/POST -- the whole point of "one-click" is that
clicking the link in an email client is enough, no page/JS/confirmation step required.
"""
from __future__ import annotations
from flask import Blueprint

from database.db_config import SessionLocal
from database.models import Lead
from services.outreach.suppression import add_suppression

unsubscribe_bp = Blueprint("unsubscribe", __name__, url_prefix="/unsubscribe")


@unsubscribe_bp.route("/<lead_id>", methods=["GET"])
def unsubscribe(lead_id):
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead or not lead.primary_email:
            return "Invalid or expired unsubscribe link.", 404
        add_suppression(db, "EMAIL", lead.primary_email, "UNSUBSCRIBE")
        return "You've been unsubscribed and won't receive further emails from us.", 200
    finally:
        db.close()
