"""Phase 10 Step 10.3 -- LinkedIn/Instagram/Facebook draft-and-queue orchestration. AI
drafts, QC gates it, and ONLY a QC-approved draft is ever saved to social_message_queue
for a human to review and send manually -- mirrors whatsapp_template_service.py's
DRAFT-never-reaches-review-unless-QC-approved pattern for AI-authored WhatsApp templates
(Step 9.6). No function in this file (or anywhere else in the codebase) ever sends a
LinkedIn/IG/FB message automatically -- MASTER PRD Step 10.3's DoD gate verifies this by
absence, deliberately.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime

from agents.social_draft_agent import draft_social_message, VALID_PLATFORMS
from agents.quality_controller_agent import review_social_draft
from database.models import Lead, LeadReviewInsight, Product, SocialMessageQueue

MAX_DRAFT_ATTEMPTS = 2  # one retry with QC's feedback if rejected, then give up honestly

PLATFORM_URL_FIELD = {
    "LINKEDIN": "linkedin_url",
    "INSTAGRAM": "instagram_url",
    "FACEBOOK": "facebook_url",
}


def request_social_draft(db, lead_id: str, platform: str) -> dict:
    """Drafts + QC-gates a social message for one lead+platform. Returns exactly one of:
    {"queued": <SocialMessageQueue row>} on success,
    {"rejected": [...]} if QC never approved after MAX_DRAFT_ATTEMPTS,
    {"error": "..."} for a hard precondition failure (bad platform, no profile URL on
    file for that platform, lead/product not found).
    """
    platform = (platform or "").upper()
    if platform not in VALID_PLATFORMS:
        return {"error": f"platform must be one of {sorted(VALID_PLATFORMS)}"}

    lead = db.get(Lead, lead_id)
    if not lead:
        return {"error": "lead not found"}

    url_field = PLATFORM_URL_FIELD[platform]
    if not getattr(lead, url_field):
        return {"error": f"lead has no {url_field} on file -- nothing to message"}

    product = db.get(Product, lead.product_id)
    if not product:
        return {"error": "product not found for this lead"}

    insight = (
        db.query(LeadReviewInsight)
        .filter(LeadReviewInsight.lead_id == lead.id)
        .order_by(LeadReviewInsight.analyzed_at.desc())
        .first()
    )
    pain_points = json.loads(insight.pain_points_extracted) if insight and insight.pain_points_extracted else []

    product_brief = {
        "title": product.title,
        "description": product.description,
        "value_proposition": product.value_proposition,
    }
    lead_profile = {
        "company_name": lead.company_name,
        "contact_person_name": lead.contact_person_name,
        "contact_person_role": lead.contact_person_role,
    }

    draft = None
    qc_result = None
    qc_feedback = None
    for _ in range(MAX_DRAFT_ATTEMPTS):
        draft = draft_social_message(db, lead.id, platform, product_brief, lead_profile,
                                     pain_points, qc_feedback=qc_feedback)
        if not draft:
            break
        qc_result = review_social_draft(db, lead.id, draft, pain_points, product_brief=product_brief)
        if qc_result["approved"]:
            break
        qc_feedback = qc_result["suggested_corrections"] or "; ".join(qc_result["rejection_reasons"])
        draft = None

    if not draft or not qc_result or not qc_result["approved"]:
        reasons = qc_result["rejection_reasons"] if qc_result else ["drafting failed -- LLM unavailable or empty output"]
        return {"rejected": reasons}

    row = SocialMessageQueue(
        id=str(uuid.uuid4()),
        lead_id=lead.id,
        platform=platform,
        message_text=draft["message_text"],
        reasoning=draft.get("reasoning") or "",
        status="QUEUED",
    )
    db.add(row)
    db.commit()
    return {"queued": row}


def mark_sent(db, queue_id: str):
    """A human confirms they sent this message manually from their own account. Only a
    QUEUED row can be marked sent -- an already-SENT or DISMISSED row is a stale click
    (e.g. a double-submit), not something to silently re-process."""
    row = db.get(SocialMessageQueue, queue_id)
    if not row or row.status != "QUEUED":
        return None
    row.status = "SENT"
    row.sent_at = datetime.utcnow()
    db.commit()
    return row


def dismiss(db, queue_id: str):
    """A human decides not to send this draft (stale, no longer relevant, etc.)."""
    row = db.get(SocialMessageQueue, queue_id)
    if not row or row.status != "QUEUED":
        return None
    row.status = "DISMISSED"
    db.commit()
    return row
