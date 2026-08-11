import json
import uuid

from sqlalchemy import text

from database.models import Job


def enqueue(db, job_type, payload: dict, run_after=None, max_attempts=3):
    """Add a new job to the queue. `run_after` (datetime) delays when it becomes claimable;
    omit for 'as soon as possible'."""
    job = Job(
        id=str(uuid.uuid4()),
        job_type=job_type,
        payload=json.dumps(payload),
        max_attempts=max_attempts,
    )
    if run_after is not None:
        job.run_after = run_after
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def claim_next(db, job_type):
    """Atomically claim the next due PENDING job of `job_type`.
    Returns the job id, or None if nothing is due yet, or another worker won the race.
    """
    row = db.execute(text(
        "SELECT id FROM jobs WHERE status='PENDING' AND job_type=:t "
        "AND run_after <= CURRENT_TIMESTAMP ORDER BY run_after LIMIT 1"),
        {"t": job_type}).fetchone()
    if not row:
        return None
    claimed = db.execute(text(
        "UPDATE jobs SET status='CLAIMED', attempts=attempts+1, updated_at=CURRENT_TIMESTAMP "
        "WHERE id=:id AND status='PENDING'"), {"id": row.id})
    db.commit()
    return row.id if claimed.rowcount > 0 else None   # lost the race -> skip


def mark_done(db, job_id):
    db.execute(text(
        "UPDATE jobs SET status='DONE', updated_at=CURRENT_TIMESTAMP WHERE id=:id"),
        {"id": job_id})
    db.commit()


def mark_failed(db, job_id, error: str, retry_delay_seconds=60):
    """A claimed job failed. Requeue as PENDING with a backoff delay if attempts remain,
    otherwise mark DEAD permanently (max_attempts reached)."""
    row = db.execute(text(
        "SELECT attempts, max_attempts FROM jobs WHERE id=:id"), {"id": job_id}).fetchone()
    if not row:
        return
    if row.attempts >= row.max_attempts:
        db.execute(text(
            "UPDATE jobs SET status='DEAD', last_error=:err, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=:id"), {"id": job_id, "err": error})
    else:
        db.execute(text(
            "UPDATE jobs SET status='PENDING', last_error=:err, "
            "run_after=datetime(CURRENT_TIMESTAMP, :delay), updated_at=CURRENT_TIMESTAMP "
            "WHERE id=:id"), {"id": job_id, "err": error, "delay": f"+{retry_delay_seconds} seconds"})
    db.commit()
