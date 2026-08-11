import json

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Product

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def _serialize(product):
    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "target_keywords": json.loads(product.target_keywords or "[]"),
        "value_proposition": product.value_proposition,
        "pain_point_mappings": json.loads(product.pain_point_mappings or "{}"),
        "priority": product.priority,
        "is_active": product.is_active,
        "created_at": str(product.created_at),
        "updated_at": str(product.updated_at),
    }


def _extract_json_fields(data, errors):
    """Validates target_keywords (array) / pain_point_mappings (object) if present.
    Returns (target_keywords_str, pain_point_mappings_str) — None means 'not provided'.
    Appends to `errors` instead of raising, so callers always get a 422, never a 500.
    """
    target_keywords = None
    if "target_keywords" in data:
        if not isinstance(data["target_keywords"], list):
            errors.append("target_keywords must be a JSON array")
        else:
            target_keywords = json.dumps(data["target_keywords"])

    pain_point_mappings = None
    if "pain_point_mappings" in data:
        if not isinstance(data["pain_point_mappings"], dict):
            errors.append("pain_point_mappings must be a JSON object")
        else:
            pain_point_mappings = json.dumps(data["pain_point_mappings"])

    return target_keywords, pain_point_mappings


@products_bp.route("", methods=["GET"])
def list_products():
    db = SessionLocal()
    try:
        query = db.query(Product)
        is_active = request.args.get("is_active")
        if is_active is not None:
            query = query.filter(Product.is_active == int(is_active))
        products = query.order_by(Product.created_at.desc()).all()
        return jsonify([_serialize(p) for p in products])
    finally:
        db.close()


@products_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            return jsonify({"error": "product not found"}), 404
        return jsonify(_serialize(product))
    finally:
        db.close()


@products_bp.route("", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if not data.get("title"):
        errors.append("title is required")
    if not data.get("description"):
        errors.append("description is required")
    target_keywords, pain_point_mappings = _extract_json_fields(data, errors)
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        product = Product(
            title=data["title"],
            description=data["description"],
            value_proposition=data.get("value_proposition"),
            priority=data.get("priority", 1),
        )
        if target_keywords is not None:
            product.target_keywords = target_keywords
        if pain_point_mappings is not None:
            product.pain_point_mappings = pain_point_mappings
        db.add(product)
        db.commit()
        db.refresh(product)
        return jsonify(_serialize(product)), 201
    finally:
        db.close()


@products_bp.route("/<product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    target_keywords, pain_point_mappings = _extract_json_fields(data, errors)
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            return jsonify({"error": "product not found"}), 404

        if "title" in data:
            if not data["title"]:
                return jsonify({"error": ["title cannot be empty"]}), 422
            product.title = data["title"]
        if "description" in data:
            if not data["description"]:
                return jsonify({"error": ["description cannot be empty"]}), 422
            product.description = data["description"]
        if "value_proposition" in data:
            product.value_proposition = data["value_proposition"]
        if "priority" in data:
            product.priority = data["priority"]
        if "is_active" in data:
            product.is_active = data["is_active"]
        if target_keywords is not None:
            product.target_keywords = target_keywords
        if pain_point_mappings is not None:
            product.pain_point_mappings = pain_point_mappings

        db.commit()
        db.refresh(product)
        return jsonify(_serialize(product))
    finally:
        db.close()


@products_bp.route("/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            return jsonify({"error": "product not found"}), 404
        db.delete(product)
        db.commit()
        return "", 204
    finally:
        db.close()
