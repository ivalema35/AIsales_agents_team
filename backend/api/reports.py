from __future__ import annotations
"""EOD report endpoints (Step 4.5). GET for dashboard/inspection visibility; POST lets a
human (or this session, for live testing) trigger generation on demand instead of only at
the scheduled 23:50 IST tick -- generate() is idempotent per report_date either way."""
import json

from flask import Blueprint, jsonify, request

from database.db_config import SessionLocal
from database.models import DailyReport
from services.reporting_service import generate

reports_bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")


def _serialize(report):
    return {
        "report_date": report.report_date,
        "metrics_summary": json.loads(report.metrics_summary or "{}"),
        "executive_summary_text": report.executive_summary_text,
        "generated_at": str(report.generated_at),
    }


@reports_bp.route("", methods=["GET"])
def list_reports():
    db = SessionLocal()
    try:
        reports = db.query(DailyReport).order_by(DailyReport.report_date.desc()).limit(30).all()
        return jsonify([_serialize(r) for r in reports])
    finally:
        db.close()


@reports_bp.route("/<report_date>", methods=["GET"])
def get_report(report_date):
    db = SessionLocal()
    try:
        report = db.query(DailyReport).filter(DailyReport.report_date == report_date).first()
        if not report:
            return jsonify({"error": "no report for that date"}), 404
        return jsonify(_serialize(report))
    finally:
        db.close()


@reports_bp.route("/generate", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}
    report_date = data.get("report_date")
    db = SessionLocal()
    try:
        report = generate(db, report_date)
        return jsonify(_serialize(report))
    finally:
        db.close()
