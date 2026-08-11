import json
import logging
import time

from database.db_config import SessionLocal
from database.models import Job
from jobs.job_queue import claim_next, mark_done, mark_failed

logger = logging.getLogger(__name__)

# Populated by later phases via register_handler(job_type) — e.g. agents/scoring_agent.py
# registers "SCORE". Keeping the registry here (not hardcoded job types) means worker.py
# never needs to change as Phase 2-5 add new job types.
HANDLERS = {}


def register_handler(job_type):
    def decorator(fn):
        HANDLERS[job_type] = fn
        return fn
    return decorator


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
    while True:
        did_work = False
        for job_type in job_types:
            if run_once(job_type):
                did_work = True
        if not did_work:
            time.sleep(poll_interval)


if __name__ == "__main__":
    run_forever(list(HANDLERS.keys()))
