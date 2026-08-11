from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Lead, Product

leads_bp = Blueprint("leads", __name__, url_prefix="/api/v1/leads")

VALID_STATUSES = {
    "DISCOVERED", "ENRICHED", "REVIEWED", "SCORED", "OUTREACHING",
    "OUTREACHED", "ENGAGED", "HOT_LEAD", "CONVERTED", "REJECTED",
}


def _serialize(lead):
    return {
        "id": lead.id,
        "product_id": lead.product_id,
        "company_name": lead.company_name,
        "website_url": lead.website_url,
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
    }


@leads_bp.route("", methods=["GET"])
def list_leads():
    db = SessionLocal()
    try:
        query = db.query(Lead)
        product_id = request.args.get("product_id")
        if product_id:
            query = query.filter(Lead.product_id == product_id)
        status = request.args.get("status")
        if status:
            if status not in VALID_STATUSES:
                return jsonify({"error": [f"status must be one of {sorted(VALID_STATUSES)}"]}), 422
            query = query.filter(Lead.status == status)
        leads = query.order_by(Lead.created_at.desc()).all()
        return jsonify([_serialize(lead) for lead in leads])
    finally:
        db.close()


@leads_bp.route("/<lead_id>", methods=["GET"])
def get_lead(lead_id):
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        return jsonify(_serialize(lead))
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
