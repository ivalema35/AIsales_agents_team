"""One-shot: upgrade PENDING 'Needs manual outreach' todos that have a lead but no
email draft proposal, by drafting once and storing it as Review & send email.

Safe to re-run -- skips cards that already have outreach_email_draft.
Does NOT send. Does NOT flip discovery/outreach switches.
"""
from __future__ import annotations
import json
import logging

from database.db_config import SessionLocal
from database.models import Campaign, Lead, LeadReviewInsight, Product, TodoItem
from agents.outreach_agent import draft_structured_email
from services.campaign_service import (
    resolve_email_render_mode, format_directive_for_mode,
    _REVIEW_SEND_EMAIL_LABEL, _OUTREACH_EMAIL_DRAFT_KIND,
)
from services.message_format_service import get_available_assets
from services.outreach.cross_sell import get_cross_sell_products
from services.outreach.pain_points import confident_pain_points

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_review_send")


def main():
    db = SessionLocal()
    try:
        items = (
            db.query(TodoItem)
            .filter(
                TodoItem.status == "PENDING",
                TodoItem.lead_id.isnot(None),
                TodoItem.label.in_([_REVIEW_SEND_EMAIL_LABEL, "Needs manual outreach"]),
            )
            .all()
        )
        upgraded = 0
        for item in items:
            proposal = json.loads(item.proposal) if item.proposal else None
            if isinstance(proposal, dict) and proposal.get("kind") == _OUTREACH_EMAIL_DRAFT_KIND:
                continue
            lead = db.get(Lead, item.lead_id)
            if not lead or not lead.primary_email:
                logger.info("skip %s -- no lead/email", item.id)
                continue
            product = db.get(Product, lead.product_id)
            if not product:
                continue
            campaign = db.get(Campaign, lead.campaign_id) if lead.campaign_id else None
            tone = (campaign.strategy_angle if campaign and campaign.strategy_angle else None) \
                or product.default_tone
            render_mode = resolve_email_render_mode(campaign) if campaign else "HTML"
            format_directive = format_directive_for_mode(render_mode, product.default_format)
            insight = (
                db.query(LeadReviewInsight)
                .filter(LeadReviewInsight.lead_id == lead.id)
                .order_by(LeadReviewInsight.analyzed_at.desc())
                .first()
            )
            pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []
            pain_points = confident_pain_points(pain_points)
            draft = draft_structured_email(
                db, lead.id,
                {"title": product.title, "description": product.description,
                 "value_proposition": product.value_proposition},
                {"company_name": lead.company_name,
                 "contact_person_name": lead.contact_person_name,
                 "contact_person_role": lead.contact_person_role},
                pain_points,
                content_assets=get_available_assets(db, lead.product_id) or None,
                cross_sell_products=get_cross_sell_products(db, lead.product_id),
                tone_directive=tone,
                format_directive=format_directive,
            )
            if not draft or not draft.get("subject") or not draft.get("body"):
                logger.info("skip %s -- draft failed", lead.company_name)
                continue
            reason = "our AI wasn't sure this email was good enough after a few tries."
            item.label = _REVIEW_SEND_EMAIL_LABEL
            item.text = (
                f'AI wrote an email for "{lead.company_name}" but wasn\'t sure it was '
                "good enough. Read it below — Approve & send if it looks right, or ask "
                f"for a change. ({reason})"
            )
            item.proposal = json.dumps({
                "kind": _OUTREACH_EMAIL_DRAFT_KIND,
                "subject": draft["subject"],
                "body": draft["body"],
                "sections": draft.get("sections"),
                "subject_candidates": draft.get("subject_candidates"),
                "followup_level": None,
                "qc_note": reason,
            })
            item.is_blocker = 1
            db.commit()
            upgraded += 1
            logger.info("upgraded %s", lead.company_name)
        print(f"UPGRADED={upgraded}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
