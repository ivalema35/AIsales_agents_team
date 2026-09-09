from __future__ import annotations
import json
import os
import uuid

from flask import Blueprint, current_app, jsonify, request

from config import Config
from database.db_config import SessionLocal
from database.models import ContentAsset, Product

content_assets_bp = Blueprint("content_assets", __name__, url_prefix="/api/v1/content-assets")

# IMAGE_URL added 2026-09-09, real user ask: a WhatsApp template header image (and email
# banner images) need a real, uploaded image asset, not just a pasted demo/video link.
VALID_ASSET_TYPES = {"DEMO_URL", "VIDEO_URL", "IMAGE_URL", "CASE_STUDY", "TESTIMONIAL", "TEXT_BLOCK"}

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5MB -- generous for a template header/banner image


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


@content_assets_bp.route("/upload", methods=["POST"])
def upload_asset_file():
    """2026-09-09, real user ask: a real image file (for a WhatsApp template header or an
    email banner) needs to end up at a real, publicly-fetchable URL -- Meta and every real
    recipient's mail client must be able to load it without a login session, the same
    reason the brand logo is served from /static/brand/ (see app.py's _PUBLIC_PREFIXES).

    Saves into Flask's own default static folder (backend/static/uploads/, auto-served at
    /static/uploads/<file> -- no new route needed) under a random filename (never the
    original, to avoid path traversal / collisions) and returns the real public URL. Does
    NOT create a ContentAsset row itself -- the frontend calls the existing POST /content-
    assets with asset_type=IMAGE_URL and this URL as `value`, same as any other asset type.
    """
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": ["file is required"]}), 422

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": [f"file type must be one of {sorted(ALLOWED_IMAGE_EXTENSIONS)}"]}), 422

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_UPLOAD_SIZE_BYTES:
        return jsonify({"error": ["file must be 5MB or smaller"]}), 422

    upload_dir = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(upload_dir, filename))

    url = f"{Config.PUBLIC_BASE_URL.rstrip('/')}/static/uploads/{filename}"
    return jsonify({"url": url}), 201


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
