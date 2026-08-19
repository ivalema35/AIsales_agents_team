"""Analytics endpoints (CRM_UI_UX_PLAN.md Phase 3) -- read-only aggregations, computed
fresh from real data every call, nothing cached/pre-materialized."""
from __future__ import annotations
from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from datetime import datetime

from services.analytics_service import (
    get_funnel, get_channel_performance, get_trend, get_by_product, get_outreach_funnel,
)

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


@analytics_bp.route("/funnel", methods=["GET"])
def funnel():
    db = SessionLocal()
    try:
        return jsonify(get_funnel(db))
    finally:
        db.close()


@analytics_bp.route("/channel-performance", methods=["GET"])
def channel_performance():
    db = SessionLocal()
    try:
        return jsonify(get_channel_performance(db))
    finally:
        db.close()


@analytics_bp.route("/trend", methods=["GET"])
def trend():
    granularity = request.args.get("granularity", "day")
    if granularity not in ("day", "week", "month"):
        return jsonify({"error": ["granularity must be one of day, week, month"]}), 422
    try:
        periods = int(request.args.get("periods", 30))
    except ValueError:
        return jsonify({"error": ["periods must be an integer"]}), 422
    periods = max(1, min(periods, 90))

    db = SessionLocal()
    try:
        return jsonify(get_trend(db, granularity, periods))
    finally:
        db.close()


def _valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


@analytics_bp.route("/outreach-funnel", methods=["GET"])
def outreach_funnel():
    start = request.args.get("start")
    end = request.args.get("end")
    if start and not _valid_date(start):
        return jsonify({"error": ["start must be YYYY-MM-DD"]}), 422
    if end and not _valid_date(end):
        return jsonify({"error": ["end must be YYYY-MM-DD"]}), 422
    if end and not start:
        return jsonify({"error": ["end requires start"]}), 422

    db = SessionLocal()
    try:
        return jsonify(get_outreach_funnel(db, start, end))
    finally:
        db.close()


@analytics_bp.route("/by-product", methods=["GET"])
def by_product():
    db = SessionLocal()
    try:
        return jsonify(get_by_product(db))
    finally:
        db.close()
