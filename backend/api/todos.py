"""Phase 21 -- the unified AI to-do inbox. Every real to-do the AI Sales Manager raises
(CAMPAIGN-scoped or GLOBAL/free-for-all) lands here as one addressable TodoItem row,
individually feedback-able and individually approved/dismissed. Replaces
`campaigns_bp`'s old `/suggestions` (GLOBAL) and `/approve` (whole-day bulk) routes.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import Campaign, Lead, Product, TodoItem
from services.campaign_service import (
    serialize_todo_item, revise_todo_item, approve_todo_item, dismiss_todo_item)

todos_bp = Blueprint("todos", __name__, url_prefix="/api/v1/todos")


@todos_bp.route("", methods=["GET"])
def list_todos():
    """Every PENDING to-do, both scopes, newest first -- what the Dashboard's AI Manager
    Inbox and a Campaign Detail page's (filtered) queue both read. `campaign_name`/
    `product_title`/`lead_company_name` are joined in here so the frontend never needs a
    second round-trip per item just to label its card."""
    db = SessionLocal()
    try:
        items = (
            db.query(TodoItem)
            .filter(TodoItem.status == "PENDING")
            .order_by(TodoItem.created_at.desc())
            .all()
        )
        campaign_ids = {i.campaign_id for i in items if i.campaign_id}
        product_ids = {i.product_id for i in items if i.product_id}
        lead_ids = {i.lead_id for i in items if i.lead_id}
        campaigns = {c.id: c.name for c in db.query(Campaign).filter(Campaign.id.in_(campaign_ids)).all()} \
            if campaign_ids else {}
        products = {p.id: p.title for p in db.query(Product).filter(Product.id.in_(product_ids)).all()} \
            if product_ids else {}
        leads = {l.id: l.company_name for l in db.query(Lead).filter(Lead.id.in_(lead_ids)).all()} \
            if lead_ids else {}

        result = []
        for item in items:
            data = serialize_todo_item(item)
            data["campaign_name"] = campaigns.get(item.campaign_id)
            data["product_title"] = products.get(item.product_id)
            data["lead_company_name"] = leads.get(item.lead_id)
            result.append(data)
        return jsonify(result)
    finally:
        db.close()


@todos_bp.route("/<todo_id>/feedback", methods=["POST"])
def submit_feedback(todo_id):
    data = request.get_json(silent=True) or {}
    instruction = str(data.get("instruction") or "").strip()
    if not instruction:
        return jsonify({"error": ["instruction is required"]}), 422
    db = SessionLocal()
    try:
        try:
            return jsonify(revise_todo_item(db, todo_id, instruction))
        except ValueError as exc:
            return jsonify({"error": [str(exc)]}), 404
        except RuntimeError as exc:
            return jsonify({"error": [str(exc)]}), 503
    finally:
        db.close()


@todos_bp.route("/<todo_id>/approve", methods=["POST"])
def approve(todo_id):
    db = SessionLocal()
    try:
        try:
            return jsonify(approve_todo_item(db, todo_id))
        except ValueError as exc:
            return jsonify({"error": [str(exc)]}), 404
    finally:
        db.close()


@todos_bp.route("/<todo_id>/dismiss", methods=["POST"])
def dismiss(todo_id):
    db = SessionLocal()
    try:
        try:
            return jsonify(dismiss_todo_item(db, todo_id))
        except ValueError as exc:
            return jsonify({"error": [str(exc)]}), 404
    finally:
        db.close()
