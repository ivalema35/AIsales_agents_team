from __future__ import annotations
import json
import logging
import time

from database.db_config import SessionLocal
from database.models import Job
from jobs.job_queue import claim_next, mark_done, mark_failed
from jobs.registry import HANDLERS, register_handler  # noqa: F401 - re-exported for existing imports
from services.heartbeat import beat_standalone

logger = logging.getLogger(__name__)

HEARTBEAT_NAME = "jobs.worker"


def run_once(job_type):
    """Claim and process a single due job of `job_type`, if any.
    Returns True if a job was claimed (processed or failed), False if none was due.
    """
    db = SessionLocal()
    try:
        job_id = claim_next(db, job_type)
        if not job_id:
            return False

        job = db.get(Job, job_id)
        handler = HANDLERS.get(job_type)
        if handler is None:
            mark_failed(db, job_id, f"no handler registered for job_type={job_type}")
            return True

        try:
            payload = json.loads(job.payload)
            handler(db, payload)
            mark_done(db, job_id)
        except Exception as exc:  # noqa: BLE001 - a handler's failure must never crash the worker loop
            logger.exception("job %s (%s) failed", job_id, job_type)
            mark_failed(db, job_id, str(exc))
        return True
    finally:
        db.close()


def run_forever(job_types, poll_interval=2):
    """Poll every registered job_type in a loop. Sleeps only when a full pass found no work,
    so a busy queue gets drained back-to-back instead of waiting out the interval each time."""
    # This loop runs far faster than the heartbeat throttle, so its real observable beat rate
    # is the throttle window, not poll_interval -- beat() clamps to that anyway.
    beat_standalone(HEARTBEAT_NAME, status="RUNNING",
                    detail={"job_types": sorted(job_types)}, force=True,
                    expected_interval_seconds=poll_interval)
    while True:
        did_work = False
        for job_type in job_types:
            if run_once(job_type):
                did_work = True
        # Called every pass; services/heartbeat.py throttles the actual DB write, so a busy
        # queue spinning back-to-back doesn't turn into hundreds of pointless UPDATEs.
        beat_standalone(HEARTBEAT_NAME, status="RUNNING" if did_work else "IDLE",
                        expected_interval_seconds=poll_interval)
        if not did_work:
            time.sleep(poll_interval)


if __name__ == "__main__":
    # See jobs/registry.py's module docstring for the real bug this import order fixes.
    import jobs.outreach_handler          # noqa: F401 - registers OUTREACH_EMAIL
    import jobs.outreach_wa_handler       # noqa: F401 - registers OUTREACH_WA
    import jobs.inbound_classify_handler  # noqa: F401 - registers CLASSIFY_INBOUND

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("jobs.worker started, handlers=%s", sorted(HANDLERS.keys()))
    run_forever(list(HANDLERS.keys()))
