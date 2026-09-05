from __future__ import annotations

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import KnowledgeBaseItem, Product

knowledge_base_bp = Blueprint("knowledge_base", __name__, url_prefix="/api/v1/knowledge-base")

# Phase 16 Step 16.1/16.2 -- this is the ONLY set of valid kinds, and this file is the
# ONLY code path in the whole project allowed to write a row into knowledge_base_items.
# No agent/cognition module imports this blueprint's write functions, and no LLM call
# anywhere constructs a KnowledgeBaseItem -- that is the zero-fabrication rule (Step 16.2)
# enforced structurally, not just documented.
VALID_KINDS = {"FACT", "OBJECTION", "PROOF", "MARKETING_ASSET"}


def _serialize(row):
    return {
        "id": row.id,
        "product_id": row.product_id,
        "kind": row.kind,
        "title": row.title,
        "body": row.body,
        "created_at": str(row.created_at),
        "updated_at": str(row.updated_at),
    }


@knowledge_base_bp.route("", methods=["GET"])
def list_items():
    db = SessionLocal()
    try:
        query = db.query(KnowledgeBaseItem)
        product_id = request.args.get("product_id")
        if product_id:
            query = query.filter(KnowledgeBaseItem.product_id == product_id)
        kind = request.args.get("kind")
        if kind:
            query = query.filter(KnowledgeBaseItem.kind == kind)
        rows = query.order_by(KnowledgeBaseItem.created_at.desc()).all()
        return jsonify([_serialize(r) for r in rows])
    finally:
        db.close()


@knowledge_base_bp.route("/<item_id>", methods=["GET"])
def get_item(item_id):
    db = SessionLocal()
    try:
        row = db.get(KnowledgeBaseItem, item_id)
        if not row:
            return jsonify({"error": "knowledge base item not found"}), 404
        return jsonify(_serialize(row))
    finally:
        db.close()


@knowledge_base_bp.route("", methods=["POST"])
def create_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if not data.get("product_id"):
        errors.append("product_id is required")
    if data.get("kind") not in VALID_KINDS:
        errors.append(f"kind must be one of {sorted(VALID_KINDS)}")
    if not data.get("title"):
        errors.append("title is required")
    if not data.get("body"):
        errors.append("body is required")

    db = SessionLocal()
    try:
        if data.get("product_id") and not db.get(Product, data["product_id"]):
            errors.append(f"product {data['product_id']!r} not found")
        if errors:
            return jsonify({"error": errors}), 422

        item = KnowledgeBaseItem(
            product_id=data["product_id"],
            kind=data["kind"],
            title=data["title"],
            body=data["body"],
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return jsonify(_serialize(item)), 201
    finally:
        db.close()


@knowledge_base_bp.route("/<item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    if "kind" in data and data["kind"] not in VALID_KINDS:
        errors.append(f"kind must be one of {sorted(VALID_KINDS)}")
    if "title" in data and not data["title"]:
        errors.append("title cannot be empty")
    if "body" in data and not data["body"]:
        errors.append("body cannot be empty")
    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        item = db.get(KnowledgeBaseItem, item_id)
        if not item:
            return jsonify({"error": "knowledge base item not found"}), 404

        if "kind" in data:
            item.kind = data["kind"]
        if "title" in data:
            item.title = data["title"]
        if "body" in data:
            item.body = data["body"]

        db.commit()
        db.refresh(item)
        return jsonify(_serialize(item))
    finally:
        db.close()


@knowledge_base_bp.route("/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    db = SessionLocal()
    try:
        item = db.get(KnowledgeBaseItem, item_id)
        if not item:
            return jsonify({"error": "knowledge base item not found"}), 404
        db.delete(item)
        db.commit()
        return "", 204
    finally:
        db.close()
