from __future__ import annotations
import json

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import ContentAsset, Product

content_assets_bp = Blueprint("content_assets", __name__, url_prefix="/api/v1/content-assets")

VALID_ASSET_TYPES = {"DEMO_URL", "VIDEO_URL", "CASE_STUDY", "TESTIMONIAL", "TEXT_BLOCK"}


def _serialize(row):
    return {
        "id": row.id,
        "product_id": row.product_id,
        "asset_type": row.asset_type,
        "title": row.title,
        "value": row.value,
        "tags": json.loads(row.tags or "[]"),
        "is_active": bool(row.is_active),
        "created_at": str(row.created_at),
    }


def _validate(data, errors):
    asset_type = data.get("asset_type")
    if asset_type is not None and asset_type not in VALID_ASSET_TYPES:
        errors.append(f"asset_type must be one of {sorted(VALID_ASSET_TYPES)}")

    tags = None
    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors.append("tags must be a JSON array")
        else:
            tags = json.dumps(data["tags"])

    product_id = data.get("product_id") or None
    if product_id is not None:
        db = SessionLocal()
        try:
            if not db.get(Product, product_id):
                errors.append(f"product {product_id!r} not found")
        finally:
            db.close()

    return tags, product_id


@content_assets_bp.route("", methods=["GET"])
def list_assets():
    db = SessionLocal()
    try:
        query = db.query(ContentAsset)
        product_id = request.args.get("product_id")
        if product_id is not None:
            # "" means explicitly the any-product (product_id IS NULL) scope
            query = query.filter(ContentAsset.product_id == (product_id or None))
        asset_type = request.args.get("asset_type")
        if asset_type:
            query = query.filter(ContentAsset.asset_type == asset_type)
        is_active = request.args.get("is_active")
        if is_active is not None:
            query = query.filter(ContentAsset.is_active == int(is_active))
        rows = query.order_by(ContentAsset.created_at.desc()).all()
        return jsonify([_serialize(r) for r in rows])
    finally:
        db.close()


@content_assets_bp.route("/<asset_id>", methods=["GET"])
def get_asset(asset_id):
    db = SessionLocal()
    try:
        row = db.get(ContentAsset, asset_id)
        if not row:
            return jsonify({"error": "content asset not found"}), 404
        return jsonify(_serialize(row))
    finally:
        db.close()


@content_assets_bp.route("", methods=["POST"])
def create_asset():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if data.get("asset_type") not in VALID_ASSET_TYPES:
        errors.append(f"asset_type must be one of {sorted(VALID_ASSET_TYPES)}")
    if not data.get("title"):
        errors.append("title is required")
    if not data.get("value"):
        errors.append("value is required")
    tags, product_id = _validate(data, errors)
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        asset = ContentAsset(
            product_id=product_id,
            asset_type=data["asset_type"],
            title=data["title"],
            value=data["value"],
            tags=tags if tags is not None else "[]",
            is_active=1 if data.get("is_active", True) else 0,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return jsonify(_serialize(asset)), 201
    finally:
        db.close()


@content_assets_bp.route("/<asset_id>", methods=["PUT"])
def update_asset(asset_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    tags, product_id = _validate(data, errors)
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        asset = db.get(ContentAsset, asset_id)
        if not asset:
            return jsonify({"error": "content asset not found"}), 404

        if "asset_type" in data:
            asset.asset_type = data["asset_type"]
        if "title" in data:
            if not data["title"]:
                return jsonify({"error": ["title cannot be empty"]}), 422
            asset.title = data["title"]
        if "value" in data:
            if not data["value"]:
                return jsonify({"error": ["value cannot be empty"]}), 422
            asset.value = data["value"]
        if tags is not None:
            asset.tags = tags
        if "product_id" in data:
            asset.product_id = product_id
        if "is_active" in data:
            asset.is_active = 1 if data["is_active"] else 0

        db.commit()
        db.refresh(asset)
        return jsonify(_serialize(asset))
    finally:
        db.close()


@content_assets_bp.route("/<asset_id>", methods=["DELETE"])
def delete_asset(asset_id):
    db = SessionLocal()
    try:
        asset = db.get(ContentAsset, asset_id)
        if not asset:
            return jsonify({"error": "content asset not found"}), 404
        db.delete(asset)
        db.commit()
        return "", 204
    finally:
        db.close()
