"""Phase 15 Step 15(B) -- standalone, criteria-driven prospect discovery. Deliberately a
SEPARATE blueprint from api/leads.py: prospects never enter the leads funnel (Table 30 is
its own table, Step 15(B).1's own rule), so this stays its own read/write surface.
"""
from __future__ import annotations
import logging

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Prospect, ProspectSearch
from services.prospect_service import ProspectSearchBlocked, enrich_prospect_contact, run_prospect_search

logger = logging.getLogger(__name__)

prospects_bp = Blueprint("prospects", __name__, url_prefix="/api/v1/prospects")


def _serialize_prospect(p: Prospect) -> dict:
    return {
        "id": p.id,
        "search_id": p.search_id,
        "full_name": p.full_name,
        "headline": p.headline,
        "linkedin_url": p.linkedin_url,
        "current_company": p.current_company,
        "location_text": p.location_text,
        "email": p.email,
        "phone": p.phone,
        "source": p.source,
        "confidence": p.confidence,
        "enrichment_status": p.enrichment_status,
        "created_at": str(p.created_at),
    }


def _serialize_search(s: ProspectSearch) -> dict:
    return {
        "id": s.id,
        "criteria_text": s.criteria_text,
        "role_keywords": s.role_keywords,
        "location": s.location,
        "provider": s.provider,
        "result_count": s.result_count,
        "spend": s.spend,
        "created_at": str(s.created_at),
    }


@prospects_bp.route("/search", methods=["POST"])
def search_prospects():
    """Runs a real search immediately (no job queue -- this is an operator-initiated,
    interactive action, same posture as 'Send Outreach Now', not a background tick)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    criteria_text = (data.get("criteria_text") or "").strip()
    role_keywords = data.get("role_keywords")
    location = (data.get("location") or "").strip() or None
    extra_keywords = data.get("extra_keywords") or None

    errors = []
    if not criteria_text:
        errors.append("criteria_text is required")
    if not isinstance(role_keywords, list) or not role_keywords or not all(
        isinstance(r, str) and r.strip() for r in role_keywords
    ):
        errors.append("role_keywords must be a non-empty list of non-empty strings")
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        try:
            search = run_prospect_search(
                db, criteria_text, role_keywords, location=location, extra_keywords=extra_keywords)
        except ProspectSearchBlocked as exc:
            return jsonify({"error": str(exc)}), 402  # Payment Required -- a real budget refusal
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 503

        prospects = db.query(Prospect).filter(Prospect.search_id == search.id).all()
        return jsonify({
            "search": _serialize_search(search),
            "prospects": [_serialize_prospect(p) for p in prospects],
        })
    finally:
        db.close()


@prospects_bp.route("", methods=["GET"])
def list_prospects():
    db = SessionLocal()
    try:
        query = db.query(Prospect)
        search_id = request.args.get("search_id")
        if search_id:
            query = query.filter(Prospect.search_id == search_id)
        prospects = query.order_by(Prospect.created_at.desc(), Prospect.id.desc()).limit(500).all()
        return jsonify([_serialize_prospect(p) for p in prospects])
    finally:
        db.close()


@prospects_bp.route("/searches", methods=["GET"])
def list_searches():
    db = SessionLocal()
    try:
        searches = db.query(ProspectSearch).order_by(
            ProspectSearch.created_at.desc(), ProspectSearch.id.desc()).limit(200).all()
        return jsonify([_serialize_search(s) for s in searches])
    finally:
        db.close()


@prospects_bp.route("/<prospect_id>/enrich", methods=["POST"])
def enrich_prospect(prospect_id):
    db = SessionLocal()
    try:
        prospect = db.get(Prospect, prospect_id)
        if not prospect:
            return jsonify({"error": "prospect not found"}), 404
        enrich_prospect_contact(db, prospect)
        return jsonify(_serialize_prospect(prospect))
    finally:
        db.close()
