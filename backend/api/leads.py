from __future__ import annotations
import json
import logging

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, or_, func, text

from cognition.hard_classifiers import strip_quoted_reply
from database.db_config import SessionLocal
from database.models import (
    AgentEvent, InboundConversation, Lead, LeadFirmographics, LeadReviewInsight,
    LeadScore, OutreachLog, Product, SuppressionEntry)
from services.lead_service import claim_lead_for_outreach
from services.outreach.suppression import normalize_identifier, is_suppressed as channel_is_suppressed
from jobs.outreach_handler import handle_outreach_email
from jobs.outreach_wa_handler import handle_outreach_wa

logger = logging.getLogger(__name__)

leads_bp = Blueprint("leads", __name__, url_prefix="/api/v1/leads")

VALID_STATUSES = {
    "DISCOVERED", "ENRICHED", "REVIEWED", "SCORED", "OUTREACHING",
    "OUTREACHED", "ENGAGED", "HOT_LEAD", "CONVERTED", "REJECTED",
}
VALID_TIERS = {"HOT", "WARM", "COLD"}


def _apply_filters(db, query, args):
    """Shared by list_leads and get_adjacent_lead so "adjacent" always walks through
    the EXACT same filtered set the list shows -- duplicating this logic in two places
    is exactly how the list/adjacent ordering mismatch happened before (see the id-DESC
    tiebreaker fix above). Returns (query, error_response_or_None)."""
    product_id = args.get("product_id")
    if product_id:
        query = query.filter(Lead.product_id == product_id)

    status = args.get("status")
    if status:
        if status not in VALID_STATUSES:
            return query, (jsonify({"error": [f"status must be one of {sorted(VALID_STATUSES)}"]}), 422)
        query = query.filter(Lead.status == status)

    tier = args.get("tier")
    if tier:
        if tier not in VALID_TIERS:
            return query, (jsonify({"error": [f"tier must be one of {sorted(VALID_TIERS)}"]}), 422)
        # inner join is safe -- LeadScore.lead_id is UNIQUE, so this can only narrow
        # rows, never duplicate a lead that already has exactly one score.
        query = query.join(LeadScore, LeadScore.lead_id == Lead.id).filter(LeadScore.tier == tier)

    search = args.get("search", "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            Lead.company_name.ilike(pattern),
            Lead.primary_email.ilike(pattern),
            Lead.primary_phone.ilike(pattern),
            Lead.contact_person_name.ilike(pattern),
            Lead.region_location.ilike(pattern),
        ))

    return query, None


def _serialize(lead, score=None, latest_reply_intent=None, latest_reply_message=None, is_suppressed=False):
    return {
        "id": lead.id,
        "product_id": lead.product_id,
        "company_name": lead.company_name,
        "website_url": lead.website_url,
        "instagram_url": lead.instagram_url,
        "facebook_url": lead.facebook_url,
        "linkedin_url": lead.linkedin_url,
        "primary_email": lead.primary_email,
        "primary_phone": lead.primary_phone,
        "whatsapp_number": lead.whatsapp_number,
        "contact_person_name": lead.contact_person_name,
        "contact_person_role": lead.contact_person_role,
        "status": lead.status,
        "source": lead.source,
        "region_location": lead.region_location,
        "sales_route": lead.sales_route,
        "created_at": str(lead.created_at),
        "updated_at": str(lead.updated_at),
        "score": None if score is None else {
            "tier": score.tier,
            "score": score.score,
            "confidence": score.confidence,
            "justification": score.justification,
        },
        # Only ever set for HOT_LEAD leads (see list_leads) -- what the lead actually
        # SAID that got them escalated (INTERESTED/DEMO_REQUESTED/etc.), distinct from
        # `score.tier` which is a scoring-time fit judgment, not why this lead is hot
        # RIGHT NOW. The Kanban card shows this instead of the tier badge for HOT_LEAD
        # cards -- "82 · HOT" told you nothing you didn't already know from the column
        # it's sitting in; the actual escalation reason is the useful thing to surface.
        "latest_reply_intent": latest_reply_intent,
        # Cleaned (strip_quoted_reply) message text behind that intent -- "OBJECTION" by
        # itself doesn't say what the lead actually objected to/asked; a hover tooltip on
        # the Kanban card surfaces this without needing to open the lead (user feedback).
        "latest_reply_message": latest_reply_message,
        # True whenever this lead's email OR phone is in suppression_list, for ANY
        # reason (STOP reply, unsubscribe link, bounce, manual) -- regardless of pipeline
        # status. Before this, a lead who explicitly opted out kept sitting in whatever
        # Kanban column it was already in with literally no visible sign anywhere in the
        # CRM that it had opted out (found live -- a real, meaningful gap: the ONLY way
        # to discover it was to open the conversation and notice intent_detected='STOP').
        "is_suppressed": is_suppressed,
    }


@leads_bp.route("", methods=["GET"])
def list_leads():
    db = SessionLocal()
    try:
        query, err = _apply_filters(db, db.query(Lead), request.args)
        if err:
            return err

        try:
            page = max(1, int(request.args.get("page", 1)))
        except ValueError:
            return jsonify({"error": ["page must be an integer"]}), 422
        try:
            # Default 500 (unchanged from the old hardcoded cap) so callers that don't
            # care about paging -- e.g. Dashboard's Kanban board, which needs every lead
            # across every status column at once -- keep getting everything in one call.
            per_page = int(request.args.get("per_page", 500))
        except ValueError:
            return jsonify({"error": ["per_page must be an integer"]}), 422
        per_page = max(1, min(per_page, 500))

        total = query.count()
        # id DESC as an explicit tiebreaker -- created_at alone is NOT unique (discovery
        # inserts a whole batch within the same second), and SQLite doesn't guarantee a
        # stable order for ties on a single-column ORDER BY. Without this, repeated page
        # fetches (or a different LIMIT/OFFSET split) could reshuffle tied rows between
        # pages -- possibly skipping or duplicating a lead across page 1/2. Matches
        # `/adjacent`'s own ordering exactly, so a lead's Prev/Next also walks the exact
        # same sequence this list shows (found live: they disagreed before this fix).
        leads = (
            query.order_by(Lead.created_at.desc(), Lead.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        scores = {
            s.lead_id: s for s in
            db.query(LeadScore).filter(LeadScore.lead_id.in_([l.id for l in leads])).all()
        } if leads else {}

        # Cheap in practice -- HOT_LEAD is a small, actively-worked status, never
        # hundreds deep like SCORED, so this is a handful of rows at most, not a
        # per-lead-in-the-page query.
        hot_lead_ids = [l.id for l in leads if l.status == "HOT_LEAD"]
        latest_intent_by_lead, latest_message_by_lead = {}, {}
        if hot_lead_ids:
            convs = (
                db.query(InboundConversation)
                .filter(InboundConversation.lead_id.in_(hot_lead_ids), InboundConversation.sender_type == "LEAD")
                .order_by(InboundConversation.created_at.asc())
                .all()
            )
            for c in convs:
                # last write wins (ascending order) -- both maps track the SAME latest
                # message per lead, so the intent badge and its hover tooltip always
                # describe the same reply, never two different ones.
                latest_intent_by_lead[c.lead_id] = c.intent_detected
                latest_message_by_lead[c.lead_id] = strip_quoted_reply(c.message_content) or c.message_content

        # Small table in practice (real opt-outs, not bulk data) -- one full read here
        # is cheaper and simpler than an is_suppressed() DB round-trip per lead.
        suppressed_pairs = {(s.channel, s.identifier) for s in db.query(SuppressionEntry).all()}

        def _lead_is_suppressed(lead):
            if suppressed_pairs and lead.primary_email:
                if ("EMAIL", normalize_identifier("EMAIL", lead.primary_email)) in suppressed_pairs:
                    return True
            phone = lead.whatsapp_number or lead.primary_phone
            if suppressed_pairs and phone:
                if ("WHATSAPP", normalize_identifier("WHATSAPP", phone)) in suppressed_pairs:
                    return True
            return False

        return jsonify({
            "leads": [
                _serialize(
                    lead, scores.get(lead.id),
                    latest_intent_by_lead.get(lead.id), latest_message_by_lead.get(lead.id),
                    _lead_is_suppressed(lead),
                )
                for lead in leads
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, -(-total // per_page)),
        })
    finally:
        db.close()


@leads_bp.route("/recent-replies", methods=["GET"])
def recent_replies():
    """Powers the Dashboard's WhatsApp/Email 'recent replies' grids -- which leads have
    actually written back, most recent first, one row per lead (not one row per message;
    a lead that replied 3 times shows once, with its LATEST message). Same
    `strip_quoted_reply()` display cleanup as the Lead Detail conversation panel, for the
    same reason -- the raw stored body includes the quoted original email.

    Only is_read=0 rows are candidates -- "Mark as read" (PATCH /inbound/<id>/read) is
    what makes a reply drop off this list; there's no separate dismissal/archive state.
    """
    try:
        limit = max(1, min(int(request.args.get("limit", 8)), 50))
    except ValueError:
        return jsonify({"error": ["limit must be an integer"]}), 422

    db = SessionLocal()
    try:
        result = {}
        for channel in ("EMAIL", "WHATSAPP"):
            # Sender-side replies only (not the AI's/human's own outbound logged as a
            # conversation row) -- overfetch a bit before dedup-by-lead since a lead can
            # have replied several times and only the newest of those should count.
            convs = (
                db.query(InboundConversation)
                .filter(
                    InboundConversation.channel == channel,
                    InboundConversation.sender_type == "LEAD",
                    InboundConversation.is_read == 0,
                )
                .order_by(InboundConversation.created_at.desc())
                .limit(limit * 5)
                .all()
            )
            seen, rows = set(), []
            for c in convs:
                if c.lead_id in seen:
                    continue
                seen.add(c.lead_id)
                rows.append(c)
                if len(rows) >= limit:
                    break

            leads_by_id = {
                l.id: l for l in db.query(Lead).filter(Lead.id.in_([c.lead_id for c in rows])).all()
            } if rows else {}

            result[channel] = [
                {
                    "id": c.id,
                    "lead_id": c.lead_id,
                    "company_name": leads_by_id[c.lead_id].company_name,
                    "status": leads_by_id[c.lead_id].status,
                    "message": strip_quoted_reply(c.message_content) or c.message_content,
                    "intent_detected": c.intent_detected,
                    "replied_at": str(c.created_at),
                }
                for c in rows if c.lead_id in leads_by_id
            ]
        return jsonify(result)
    finally:
        db.close()


@leads_bp.route("/<lead_id>/adjacent", methods=["GET"])
def get_adjacent_lead(lead_id):
    """Powers the Lead Detail page's own Prev/Next -- lets someone browse straight
    through a list without bouncing back out to it. `product_id`/`status`/`tier`/`search`
    (the same filters the Leads list page uses) scope "adjacent" to whatever list the
    caller is actually walking through; with none of them, it's every lead. Ordering
    matches the list's own (created_at DESC, id DESC as a tiebreaker for ties).
    """
    db = SessionLocal()
    try:
        lead = db.query(Lead).get(lead_id)
        if not lead:
            return jsonify({"error": ["lead not found"]}), 404

        query, err = _apply_filters(db, db.query(Lead), request.args)
        if err:
            return err

        # Both sides of every created_at comparison are normalized through strftime to
        # plain 'YYYY-MM-DD HH:MM:SS' text -- comparing the raw column against a bound
        # Python datetime looked equivalent but wasn't: SQLAlchemy's sqlite driver
        # serializes a bound datetime with an explicit ".000000" microseconds suffix,
        # while this column's existing values are stored WITHOUT one (inserted via
        # CURRENT_TIMESTAMP) -- '...21' < '...21.000000' as plain text, so a row's own
        # timestamp compared "less than" a parameter representing that SAME timestamp,
        # and a lead matched itself as its own "next" (found live testing this route).
        created_col = func.strftime("%Y-%m-%d %H:%M:%S", Lead.created_at)
        anchor_created = lead.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # "next" = the next OLDER lead in the same desc-ordered list (further down the
        # table); "prev" = the next NEWER one (further up).
        next_lead = (
            query.filter(or_(
                created_col < anchor_created,
                and_(created_col == anchor_created, Lead.id < lead.id),
            ))
            .order_by(created_col.desc(), Lead.id.desc())
            .first()
        )
        prev_lead = (
            query.filter(or_(
                created_col > anchor_created,
                and_(created_col == anchor_created, Lead.id > lead.id),
            ))
            .order_by(created_col.asc(), Lead.id.asc())
            .first()
        )
        position = query.filter(or_(
            created_col > anchor_created,
            and_(created_col == anchor_created, Lead.id >= lead.id),
        )).count()
        total = query.count()

        return jsonify({
            "position": position,
            "total": total,
            "prev": {"id": prev_lead.id, "company_name": prev_lead.company_name} if prev_lead else None,
            "next": {"id": next_lead.id, "company_name": next_lead.company_name} if next_lead else None,
        })
    finally:
        db.close()


def _lead_is_suppressed(db, lead):
    """Single-lead version of list_leads()' bulk suppression check -- reuses the real
    is_suppressed() from suppression.py directly (2 queries, negligible for one lead)
    instead of duplicating its normalization logic, unlike the bulk path which needs
    the set-based approach to stay cheap across up to 500 leads at once."""
    if lead.primary_email and channel_is_suppressed(db, "EMAIL", lead.primary_email):
        return True
    phone = lead.whatsapp_number or lead.primary_phone
    if phone and channel_is_suppressed(db, "WHATSAPP", phone):
        return True
    return False


@leads_bp.route("/<lead_id>", methods=["GET"])
def get_lead(lead_id):
    """Full detail for the Lead Detail view (CRM_UI_UX_PLAN.md Phase 1) -- everything the
    system knows about one lead in a single response: score WITH breakdown (not just the
    summary line list_leads() gives), pain points with evidence, firmographics, review
    stats. The timeline (agent_events/outreach_logs/inbound_conversations, merged and
    sorted) is a separate endpoint below -- kept apart since it's a different shape and
    can grow large, no reason to force every list-context caller to pay for it."""
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        score = db.query(LeadScore).filter(LeadScore.lead_id == lead_id).first()
        insight = (
            db.query(LeadReviewInsight)
            .filter(LeadReviewInsight.lead_id == lead_id)
            .order_by(LeadReviewInsight.analyzed_at.desc())
            .first()
        )
        firmographics = db.query(LeadFirmographics).filter(LeadFirmographics.lead_id == lead_id).first()

        body = _serialize(lead, score, is_suppressed=_lead_is_suppressed(db, lead))
        if score and body["score"] is not None:
            body["score"]["scoring_breakdown"] = json.loads(score.scoring_breakdown) if score.scoring_breakdown else {}
        body["pain_points"] = (
            json.loads(insight.pain_points_extracted)
            if insight and insight.pain_points_extracted else []
        )
        body["review_insight"] = {
            "review_source": insight.review_source,
            "average_rating": insight.average_rating,
            "total_reviews_count": insight.total_reviews_count,
            "sentiment_score": insight.sentiment_score,
        } if insight else None
        body["firmographics"] = {
            "linkedin_url": firmographics.linkedin_url,
            "company_size_range": firmographics.company_size_range,
            "industry": firmographics.industry,
            "tech_stack": json.loads(firmographics.tech_stack) if firmographics.tech_stack else [],
        } if firmographics else None
        return jsonify(body)
    finally:
        db.close()


_EDITABLE_FIELDS = {
    "company_name", "website_url", "instagram_url", "facebook_url", "linkedin_url",
    "primary_email", "primary_phone",
    "whatsapp_number", "contact_person_name", "contact_person_role", "region_location",
}


@leads_bp.route("/<lead_id>", methods=["PATCH"])
def patch_lead(lead_id):
    """Manual admin override of a lead's editable contact/profile fields (CRM_UI_UX_PLAN.md
    Phase 1) -- deliberately separate from PATCH /<id>/status below, which has its own
    pipeline-transition semantics and callers."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422
    unknown = set(data.keys()) - _EDITABLE_FIELDS
    if unknown:
        return jsonify({"error": [f"unknown/non-editable field(s): {sorted(unknown)}"]}), 422

    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        for field, value in data.items():
            setattr(lead, field, value)
        db.commit()
        db.refresh(lead)
        return jsonify(_serialize(lead))
    finally:
        db.close()


@leads_bp.route("/<lead_id>/timeline", methods=["GET"])
def get_lead_timeline(lead_id):
    """Every real event this lead has ever had, merged from 3 separate tables into one
    chronological list -- agent_events (discovery/enrich/review/score/classify/escalate),
    outreach_logs (what was actually sent), inbound_conversations (what actually came
    back). Each entry is pre-shaped server-side (a `title`/`type` the frontend can map
    straight to an icon) rather than pushing that formatting logic into the UI."""
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404

        events = []
        for e in db.query(AgentEvent).filter(AgentEvent.lead_id == lead_id).all():
            events.append({
                "type": "AGENT_EVENT",
                "timestamp": str(e.created_at),
                "agent": e.agent,
                "action_type": e.action_type,
                "confidence": e.confidence,
                "risk_level": e.risk_level,
                "routed_to": e.routed_to,
                "outcome": e.outcome,
                "payload": json.loads(e.payload) if e.payload else {},
            })

        for log in db.query(OutreachLog).filter(OutreachLog.lead_id == lead_id).all():
            events.append({
                "type": "OUTREACH_SENT",
                "timestamp": str(log.sent_at),
                "channel": log.channel,
                "subject": log.message_subject,
                "body": log.message_body,
                "status": log.status,
            })

        for conv in db.query(InboundConversation).filter(InboundConversation.lead_id == lead_id).all():
            events.append({
                "type": "REPLY_RECEIVED",
                "timestamp": str(conv.created_at),
                "channel": conv.channel,
                "sender_type": conv.sender_type,
                # `message_content` is the RAW stored body -- for email that includes
                # everything the client quoted below the reply (our own original outreach,
                # signature, footer), same "wall of quoted text" the hard-classifiers strip
                # before keyword-matching. Displaying it raw made a one-line reply look like
                # the lead re-sent our whole email back (found live from a real screenshot).
                # Stripped here for DISPLAY only -- the DB row keeps the full original.
                "message": strip_quoted_reply(conv.message_content) or conv.message_content,
                "intent_detected": conv.intent_detected,
                "confidence": conv.confidence,
                "ai_suggested_response": conv.ai_suggested_response,
            })

        events.sort(key=lambda ev: ev["timestamp"])
        return jsonify(events)
    finally:
        db.close()


@leads_bp.route("", methods=["POST"])
def create_lead():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if not data.get("product_id"):
        errors.append("product_id is required")
    if not data.get("company_name"):
        errors.append("company_name is required")
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        product = db.get(Product, data["product_id"])
        if not product:
            return jsonify({"error": [f"product_id '{data['product_id']}' does not exist"]}), 422

        lead = Lead(
            product_id=data["product_id"],
            company_name=data["company_name"],
            website_url=data.get("website_url"),
            primary_email=data.get("primary_email"),
            primary_phone=data.get("primary_phone"),
            whatsapp_number=data.get("whatsapp_number"),
            contact_person_name=data.get("contact_person_name"),
            contact_person_role=data.get("contact_person_role"),
            source=data.get("source"),
            region_location=data.get("region_location"),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return jsonify(_serialize(lead)), 201
    finally:
        db.close()


@leads_bp.route("/<lead_id>/outreach", methods=["POST"])
def trigger_outreach(lead_id):
    """Manual, human-initiated outreach trigger (dashboard "Send Outreach Now" button) --
    runs the real draft->QC->send flow synchronously so the click gets a real result back
    immediately, instead of enqueueing and hoping the background worker picks it up in
    time for a live demo. This is a deliberate single-lead human action, not the
    scheduler's autonomous tick -- it is NOT gated by system_settings.autonomous_outreach_
    enabled (that switch only governs the scheduler's own automatic claiming; see
    tracker.md A.3 / services/system_settings.py).
    """
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404

        score = db.query(LeadScore).filter(LeadScore.lead_id == lead_id).first()
        if not score:
            return jsonify({"error": ["lead has not been scored yet -- nothing to act on"]}), 422

        # OUTREACHING means a send is ACTIVELY in flight right now (claim_lead_for_outreach
        # sets this immediately, before the slow LLM-draft+QC+send work even starts) --
        # forcing it back to SCORED here would let a second concurrent click bypass that
        # atomic claim's own protection and fire a real duplicate send. This isn't
        # hypothetical: the dashboard polls every 15s and a lead mid-send visibly moves
        # Kanban columns, which remounts its card with fresh (unblocked) button state --
        # so a second click during that window looks perfectly safe to a real user and
        # produced 4 duplicate real email/WhatsApp sends before this guard existed.
        if lead.status == "OUTREACHING":
            return jsonify({
                "error": ["outreach is already in progress for this lead -- wait for it to finish"]
            }), 409

        # A deliberate manual re-trigger (e.g. for a demo) should still work regardless of
        # whatever TERMINAL state a previous run left the lead in -- reset to SCORED so
        # claim_lead_for_outreach's atomic claim has something to claim.
        if lead.status != "SCORED":
            lead.status = "SCORED"
            db.commit()

        # enqueue_jobs=False -- this endpoint processes the channels itself, synchronously,
        # right below; letting claim_lead_for_outreach() also enqueue OUTREACH_EMAIL/
        # OUTREACH_WA would mean jobs.worker picks up the exact same work again and sends
        # a real duplicate whenever the worker is running (i.e. always, in normal use).
        channels = claim_lead_for_outreach(db, lead_id, enqueue_jobs=False)
        if not channels:
            return jsonify({
                "error": ["lead is not outreach-eligible (tier must be HOT/WARM and "
                          "confidence high enough, and it needs at least one contact channel)"]
            }), 422

        # Snapshot existing log ids per channel BEFORE processing -- this may not be the
        # lead's first outreach attempt (e.g. a repeated demo), so "a log exists" isn't
        # enough to tell a fresh send from a stale one; only a NEW id counts.
        existing_ids = {
            channel: {row.id for row in db.query(OutreachLog.id).filter(
                OutreachLog.lead_id == lead_id, OutreachLog.channel == channel)}
            for channel in channels
        }

        handlers = {"EMAIL": handle_outreach_email, "WHATSAPP": handle_outreach_wa}
        try:
            for channel in channels:
                handlers[channel](db, {"lead_id": lead_id})
        except Exception:
            # Safety net (2026-08-19 incident): claim_lead_for_outreach() already committed
            # OUTREACHING above, before this slow LLM-draft+QC+send work even starts. If a
            # handler blows up (LLM outage, etc.), the lead must not stay parked in
            # OUTREACHING forever -- the guard above (line ~550) would then reject every
            # future retry with 409, permanently stuck. Revert to SCORED so the next click
            # (or the scheduler's own tick) can claim it again.
            logger.exception("trigger_outreach failed for lead %s -- reverting to SCORED", lead_id)
            db.rollback()
            db.execute(text(
                "UPDATE leads SET status='SCORED', updated_at=CURRENT_TIMESTAMP "
                "WHERE id=:id AND status='OUTREACHING'"), {"id": lead_id})
            db.commit()
            return jsonify({
                "error": ["outreach send failed (provider outage or similar) -- lead was "
                          "reset to SCORED, safe to retry"]
            }), 503

        results = {}
        for channel in channels:
            log = (
                db.query(OutreachLog)
                .filter(OutreachLog.lead_id == lead_id, OutreachLog.channel == channel,
                        ~OutreachLog.id.in_(existing_ids[channel]))
                .order_by(OutreachLog.sent_at.desc())
                .first()
            )
            results[channel] = (
                {"status": log.status, "subject": log.message_subject}
                if log else {"status": "ESCALATED", "reason": "QC/validation rejected the draft -- needs a human"}
            )

        db.refresh(lead)
        return jsonify({"lead_id": lead_id, "lead_status": lead.status, "results": results})
    finally:
        db.close()


@leads_bp.route("/<lead_id>/status", methods=["PATCH"])
def patch_lead_status(lead_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("status"):
        return jsonify({"error": ["status is required"]}), 422
    if data["status"] not in VALID_STATUSES:
        return jsonify({"error": [f"status must be one of {sorted(VALID_STATUSES)}"]}), 422

    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        lead.status = data["status"]
        db.commit()
        db.refresh(lead)
        return jsonify(_serialize(lead))
    finally:
        db.close()
