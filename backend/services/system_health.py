"""Shared system-health queries (Phase 6 Steps 6.2 + 6.4). Single source of truth for "is a
process DOWN" so the read-only /system/live endpoint and the stuck-alert tick can never
silently drift onto two different thresholds -- a classic way this kind of check quietly
breaks: one gets tuned, the other doesn't, and nobody notices for months.
"""
from __future__ import annotations
import json

from sqlalchemy import text

# The processes that are SUPPOSED to be running. Hardcoded on purpose: a process that has
# never started has no heartbeat row at all, and "no row" is the single most important case
# to surface -- reading the table alone would silently omit exactly the process whose absence
# we most need to know about.
EXPECTED_PROCESSES = (
    "jobs.worker",
    "scraper_worker.async_runner",
    "jobs.discovery_scheduler",
    "jobs.inbound_poller",
)

# A process is DOWN once it has missed this many of its own expected beats. Not 1x: a loop
# that beats every 15s will occasionally run a few seconds late (a long job, a slow write),
# and flagging that as DOWN would make the monitor cry wolf -- a monitor people learn to
# ignore is worse than no monitor at all. Each process's own interval comes from its
# heartbeat row (services/heartbeat.py), never a global window: these loops run anywhere
# from 2s to 300s apart.
STALE_MULTIPLIER = 3

# How long a lead may reasonably sit mid-send. A real send, even in the worst case (Gemini
# exhausts retries, falls back to OpenAI, QC rejects and a redraft is attempted) finishes in
# well under 2 minutes with the Step 6.4-era 12s per-call LLM timeout. 15 minutes is a wide
# margin above that -- if a lead is still OUTREACHING at 15 minutes, the send was genuinely
# interrupted (the exact 2026-08-19 incident this phase exists to catch), not just slow.
STUCK_OUTREACH_MINUTES = 15

# Same reasoning for a job that was claimed but never finished -- a crashed worker leaves it
# CLAIMED forever with no retry, since claim_next() only ever looks at PENDING jobs.
STUCK_CLAIMED_MINUTES = 15


def get_process_states(db):
    """Liveness for every expected process. Age is computed in SQL via julianday(), NOT in
    Python -- SQLite writes CURRENT_TIMESTAMP in UTC while the calling process's local clock
    may be anything (IST here, +5:30); subtracting a Python datetime.now() from that column
    would report every process as ~5.5 hours stale. Keeping both sides of the subtraction
    inside SQLite's own clock removes the class of bug entirely.
    """
    rows = db.execute(text("""
        SELECT process_name,
               status,
               detail,
               expected_interval_seconds,
               started_at,
               last_seen_at,
               CAST((julianday('now') - julianday(last_seen_at)) * 86400.0 AS INTEGER)
                   AS age_seconds
          FROM system_heartbeats
    """)).fetchall()
    seen = {r.process_name: r for r in rows}

    processes = []
    for name in EXPECTED_PROCESSES:
        row = seen.get(name)
        if row is None:
            processes.append({
                "name": name, "state": "NEVER_SEEN", "status": None, "age_seconds": None,
                "expected_interval_seconds": None, "started_at": None, "last_seen_at": None,
                "detail": {},
            })
            continue

        interval = row.expected_interval_seconds or 60
        age = max(row.age_seconds or 0, 0)  # a clock skew must never read as negative age
        stale = age > interval * STALE_MULTIPLIER

        if stale:
            state = "DOWN"
        elif row.status == "ERROR":
            state = "ERROR"
        else:
            state = "UP"

        try:
            detail = json.loads(row.detail or "{}")
        except (TypeError, ValueError):
            detail = {}

        processes.append({
            "name": name, "state": state, "status": row.status, "age_seconds": age,
            "expected_interval_seconds": interval, "started_at": row.started_at,
            "last_seen_at": row.last_seen_at, "detail": detail,
        })

    # Any heartbeat row we didn't expect -- e.g. a process renamed without updating
    # EXPECTED_PROCESSES. Surfacing it beats letting a stale row sit invisible forever.
    for name, row in seen.items():
        if name not in EXPECTED_PROCESSES:
            processes.append({
                "name": name, "state": "UNKNOWN_PROCESS", "status": row.status,
                "age_seconds": max(row.age_seconds or 0, 0),
                "expected_interval_seconds": row.expected_interval_seconds,
                "started_at": row.started_at, "last_seen_at": row.last_seen_at, "detail": {},
            })

    return processes


def find_stuck_leads(db, minutes=STUCK_OUTREACH_MINUTES):
    """Leads parked in OUTREACHING longer than a real send could ever legitimately take --
    the 2026-08-19 incident class (a send interrupted mid-flight, status never advanced)."""
    rows = db.execute(text("""
        SELECT id, company_name,
               CAST((julianday('now') - julianday(updated_at)) * 1440.0 AS INTEGER)
                   AS minutes_stuck
          FROM leads
         WHERE status = 'OUTREACHING'
           AND julianday('now') - julianday(updated_at) > :m / 1440.0
         ORDER BY updated_at
    """), {"m": minutes}).fetchall()
    return [{"id": r.id, "company_name": r.company_name, "minutes_stuck": r.minutes_stuck}
            for r in rows]


def find_stuck_jobs(db, minutes=STUCK_CLAIMED_MINUTES):
    """Jobs claimed but never finished -- a worker that crashed mid-job leaves these behind
    with no automatic retry (claim_next() only ever looks at PENDING)."""
    rows = db.execute(text("""
        SELECT id, job_type,
               CAST((julianday('now') - julianday(updated_at)) * 1440.0 AS INTEGER)
                   AS minutes_stuck
          FROM jobs
         WHERE status = 'CLAIMED'
           AND julianday('now') - julianday(updated_at) > :m / 1440.0
         ORDER BY updated_at
    """), {"m": minutes}).fetchall()
    return [{"id": r.id, "job_type": r.job_type, "minutes_stuck": r.minutes_stuck}
            for r in rows]


def count_dead_jobs(db):
    return db.execute(text("SELECT COUNT(*) FROM jobs WHERE status='DEAD'")).scalar() or 0
