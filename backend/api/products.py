from __future__ import annotations
import json

import phonenumbers
from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Product, ProductStrategy

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
        "target_regions": json.loads(product.target_regions or "[]"),
        "target_country": product.target_country,
        "created_at": str(product.created_at),
        "updated_at": str(product.updated_at),
    }


def _extract_json_fields(data, errors):
    """Validates target_keywords (array) / pain_point_mappings (object) / target_regions
    (array) if present. Returns (target_keywords_str, pain_point_mappings_str,
    target_regions_str) — None means 'not provided'. Appends to `errors` instead of
    raising, so callers always get a 422, never a 500.
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

    target_regions = None
    if "target_regions" in data:
        if not isinstance(data["target_regions"], list):
            errors.append("target_regions must be a JSON array")
        else:
            target_regions = json.dumps(data["target_regions"])

    return target_keywords, pain_point_mappings, target_regions


def _validate_target_country(data, errors):
    """ISO 3166-1 alpha-2 (e.g. "IN", "CA") -- validated against phonenumbers' own real
    region list (SUPPORTED_REGIONS) rather than just "is it 2 letters", so a typo like
    "XX" is caught here instead of silently breaking every phone normalization for this
    product's leads later (tracker.md, 2026-08-17)."""
    if "target_country" not in data:
        return None
    value = str(data["target_country"] or "").strip().upper()
    if value not in phonenumbers.SUPPORTED_REGIONS:
        errors.append(f"target_country must be a real ISO 3166-1 alpha-2 code (got {value!r})")
        return None
    return value


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
    target_keywords, pain_point_mappings, target_regions = _extract_json_fields(data, errors)
    target_country = _validate_target_country(data, errors)
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
        if target_regions is not None:
            product.target_regions = target_regions
        if target_country is not None:
            product.target_country = target_country
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
    target_keywords, pain_point_mappings, target_regions = _extract_json_fields(data, errors)
    target_country = _validate_target_country(data, errors)
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
        if target_regions is not None:
            product.target_regions = target_regions
        if target_country is not None:
            product.target_country = target_country

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


def _serialize_strategy(row):
    return {
        "id": row.id,
        "icp": json.loads(row.icp or "{}"),
        "search_queries": json.loads(row.search_queries or "[]"),
        "target_complaints": json.loads(row.target_complaints or "[]"),
        "source": row.source,
        "status": row.status,
        "created_at": str(row.created_at),
    }


@products_bp.route("/<product_id>/strategy", methods=["GET"])
def get_product_strategy(product_id):
    """Dashboard visibility (tracker.md A.2): what the ICP Strategy Agent decided to
    target for this product, plus any human-added queries alongside it. Full React view
    is Phase 4.4 -- this just guarantees the data is inspectable now."""
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            return jsonify({"error": "product not found"}), 404

        rows = (
            db.query(ProductStrategy)
            .filter(ProductStrategy.product_id == product_id, ProductStrategy.status == "ACTIVE")
            .order_by(ProductStrategy.created_at.desc())
            .all()
        )
        return jsonify({
            "product_id": product_id,
            "target_regions": json.loads(product.target_regions or "[]"),
            "active_strategies": [_serialize_strategy(r) for r in rows],
        })
    finally:
        db.close()


@products_bp.route("/<product_id>/strategy/queries", methods=["POST"])
def add_strategy_query(product_id):
    """Lets a human add extra search queries alongside the AI's own, without triggering
    (or losing) a fresh AI_GENERATED strategy. Kept as its own ACTIVE, HUMAN_ADDED row."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("search_queries"), list) \
            or not data["search_queries"]:
        return jsonify({"error": ["search_queries is required and must be a non-empty JSON array"]}), 422

    queries = [str(q).strip()[:100] for q in data["search_queries"] if str(q).strip()]
    if not queries:
        return jsonify({"error": ["search_queries contained no usable values"]}), 422

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            return jsonify({"error": "product not found"}), 404

        row = ProductStrategy(
            product_id=product_id,
            search_queries=json.dumps(queries),
            source="HUMAN_ADDED",
            status="ACTIVE",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return jsonify(_serialize_strategy(row)), 201
    finally:
        db.close()
