"""Live system state (Phase 6 Step 6.2) -- one read-only endpoint answering the question the
CRM could not answer at all before: "is the system alive, and what is it doing right now?"

Everything here is a plain SELECT. No writes, no LLM calls, no external requests: a
monitoring endpoint that can itself mutate state or fail on someone else's outage defeats
its own purpose.

One endpoint rather than four, deliberately -- the UI polls this on an interval, and four
separate calls would be four times the load for exactly the same information.

Auth: `/api/v1/system/` is not in app.py's `_PUBLIC_PREFIXES`, so the global before_request
gate already protects it. Nothing auth-related needs to live here.
"""
from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import text

from database.db_config import SessionLocal
from services.system_health import get_process_states
from services.system_settings import (
    get_bool, DISCOVERY_ENABLED, AUTONOMOUS_OUTREACH_ENABLED,
    AUTO_REPLY_ENABLED, ACKNOWLEDGMENT_REPLY_ENABLED)

system_bp = Blueprint("system", __name__, url_prefix="/api/v1/system")

ACTIVITY_LIMIT = 25


def _load_toggles(db):
    """The dashboard-editable switches that decide whether the system acts autonomously
    right now. Process liveness (get_process_states) answers "is the scheduler alive?" --
    a completely different question from "is discovery actually turned on?". A process can
    be very much alive and simply looping past a no-op every tick because a toggle is off;
    without this, that looked identical to discovery genuinely running (the exact confusion
    the operator hit -- toggled discovery off from Settings, then couldn't tell from
    anywhere in the CRM whether it had actually taken effect).
    """
    return {
        DISCOVERY_ENABLED: get_bool(db, DISCOVERY_ENABLED, default=False),
        AUTONOMOUS_OUTREACH_ENABLED: get_bool(db, AUTONOMOUS_OUTREACH_ENABLED, default=False),
        AUTO_REPLY_ENABLED: get_bool(db, AUTO_REPLY_ENABLED, default=False),
        ACKNOWLEDGMENT_REPLY_ENABLED: get_bool(db, ACKNOWLEDGMENT_REPLY_ENABLED, default=False),
    }


def _load_jobs(db):
    rows = db.execute(text("""
        SELECT job_type, status, COUNT(*) AS n
          FROM jobs
         GROUP BY job_type, status
    """)).fetchall()

    by_status, by_type = {}, {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + r.n
        by_type.setdefault(r.job_type, {})[r.status] = r.n

    return {
        "by_status": by_status,
        "by_type": by_type,
        # Pulled out because a DEAD pile-up is the one job state that always means a human
        # needs to look -- it has exhausted every retry and nothing will move it on its own.
        "dead": by_status.get("DEAD", 0),
    }


def _load_activity(db, limit=ACTIVITY_LIMIT):
    """Recent agent actions, joined to the lead's name.

    LEFT JOIN, not JOIN: agent_events.lead_id is nullable (ICP strategy runs against a product,
    not a lead) and an inner join would silently drop those rows from the feed.
    """
    rows = db.execute(text("""
        SELECT e.agent, e.action_type, e.outcome, e.routed_to, e.confidence,
               e.lead_id, l.company_name, e.created_at
          FROM agent_events e
          LEFT JOIN leads l ON l.id = e.lead_id
         ORDER BY e.created_at DESC, e.rowid DESC
         LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [{
        "agent": r.agent,
        "action_type": r.action_type,
        "outcome": r.outcome,
        "routed_to": r.routed_to,
        "confidence": r.confidence,
        "lead_id": r.lead_id,
        "company_name": r.company_name,
        "created_at": r.created_at,
    } for r in rows]


@system_bp.route("/live", methods=["GET"])
def live():
    db = SessionLocal()
    try:
        return jsonify({
            "processes": get_process_states(db),
            # Serving this response is itself proof the API is up -- there is nothing more
            # honest to report, and no heartbeat could say it better.
            "api": {"state": "UP"},
            "toggles": _load_toggles(db),
            "jobs": _load_jobs(db),
            "leads_in_flight": db.execute(text(
                "SELECT COUNT(*) FROM leads WHERE status='OUTREACHING'")).scalar() or 0,
            "activity": _load_activity(db),
        })
    finally:
        db.close()
