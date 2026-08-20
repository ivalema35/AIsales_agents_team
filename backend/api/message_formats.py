from __future__ import annotations
import json

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import MessageFormat, Product
from services.message_format_service import resolve_active_format

message_formats_bp = Blueprint("message_formats", __name__, url_prefix="/api/v1/message-formats")

VALID_CHANNELS = {"EMAIL", "WHATSAPP"}


def _serialize(row):
    return {
        "id": row.id,
        "product_id": row.product_id,
        "channel": row.channel,
        "sections": json.loads(row.sections or "[]"),
        "version": row.version,
        "status": row.status,
        "created_at": str(row.created_at),
    }


@message_formats_bp.route("", methods=["GET"])
def list_formats():
    db = SessionLocal()
    try:
        query = db.query(MessageFormat)
        product_id = request.args.get("product_id")
        if product_id is not None:
            # "" means explicitly the global (product_id IS NULL) scope
            query = query.filter(MessageFormat.product_id == (product_id or None))
        channel = request.args.get("channel")
        if channel:
            query = query.filter(MessageFormat.channel == channel)
        status = request.args.get("status")
        if status:
            query = query.filter(MessageFormat.status == status)
        rows = query.order_by(MessageFormat.created_at.desc()).all()
        return jsonify([_serialize(r) for r in rows])
    finally:
        db.close()


@message_formats_bp.route("/<format_id>", methods=["GET"])
def get_format(format_id):
    db = SessionLocal()
    try:
        row = db.get(MessageFormat, format_id)
        if not row:
            return jsonify({"error": "message format not found"}), 404
        return jsonify(_serialize(row))
    finally:
        db.close()


@message_formats_bp.route("", methods=["POST"])
def create_format():
    """Creates a NEW version, never overwrites -- same versioning precedent as
    ProductStrategy. Any currently-ACTIVE format in the exact same scope
    (product_id, channel) is marked SUPERSEDED, not deleted, so Phase 9's performance
    history never loses what format a past send actually used.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 422

    errors = []
    channel = data.get("channel")
    if channel not in VALID_CHANNELS:
        errors.append(f"channel must be one of {sorted(VALID_CHANNELS)}")

    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty JSON array")
    elif not all(isinstance(s, str) and s.strip() for s in sections):
        errors.append("sections must be an array of non-empty strings")

    product_id = data.get("product_id") or None
    if product_id is not None and errors == []:
        db = SessionLocal()
        try:
            if not db.get(Product, product_id):
                errors.append(f"product {product_id!r} not found")
        finally:
            db.close()

    if errors:
        return jsonify({"error": errors}), 422

    db = SessionLocal()
    try:
        existing = (
            db.query(MessageFormat)
            .filter(MessageFormat.product_id == product_id, MessageFormat.channel == channel)
            .all()
        )
        for row in existing:
            if row.status == "ACTIVE":
                row.status = "SUPERSEDED"
        next_version = (max((r.version for r in existing), default=0)) + 1

        new_format = MessageFormat(
            product_id=product_id,
            channel=channel,
            sections=json.dumps([s.strip() for s in sections]),
            version=next_version,
            status="ACTIVE",
        )
        db.add(new_format)
        db.commit()
        db.refresh(new_format)
        return jsonify(_serialize(new_format)), 201
    finally:
        db.close()


@message_formats_bp.route("/<format_id>", methods=["DELETE"])
def deactivate_format(format_id):
    """Soft-deactivate only -- sets status=SUPERSEDED, never a hard delete. A past send
    may already reference this format's shape; the row must survive for Phase 9's
    performance history even after it stops being used for new drafts."""
    db = SessionLocal()
    try:
        row = db.get(MessageFormat, format_id)
        if not row:
            return jsonify({"error": "message format not found"}), 404
        row.status = "SUPERSEDED"
        db.commit()
        db.refresh(row)
        return jsonify(_serialize(row))
    finally:
        db.close()


@message_formats_bp.route("/resolve", methods=["GET"])
def resolve_format():
    """Step 8.1's resolution order (used by Step 8.3's drafting call): product+channel
    ACTIVE format -> global (product_id IS NULL) channel ACTIVE format -> null (no
    format at all -- today's free-form drafting, unchanged). Returns 200 with a null
    body when nothing resolves; that is a valid, expected state, not an error.
    """
    channel = request.args.get("channel")
    if channel not in VALID_CHANNELS:
        return jsonify({"error": [f"channel must be one of {sorted(VALID_CHANNELS)}"]}), 422
    product_id = request.args.get("product_id") or None

    db = SessionLocal()
    try:
        row = resolve_active_format(db, product_id, channel)
        return jsonify(_serialize(row) if row else None)
    finally:
        db.close()
