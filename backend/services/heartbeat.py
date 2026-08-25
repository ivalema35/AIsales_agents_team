"""Process liveness heartbeats (Phase 6 Step 6.1).

Each long-running background process (`jobs.worker`, `scraper_worker.async_runner`,
`jobs.discovery_scheduler`, `jobs.inbound_poller`) calls `beat()` from inside its own loop.
A reader (Step 6.2's `/system/live`) decides who is DOWN by comparing `last_seen_at` against
a staleness window — nothing ever marks itself dead, because a process that has crashed or
been SIGKILLed cannot write its own tombstone.

Deliberately NOT a `systemctl is-active` shell-out: the API process must never need root,
and this same code has to work on the dev machine where none of these are systemd units.

`bos-api` (gunicorn) has no heartbeat on purpose — it runs 3 worker processes that would all
write the same row, and if the API is down the CRM cannot load at all, which is its own
unambiguous signal.

Two properties this module must never lose:

1. **A heartbeat failure can never take down the process it is monitoring.** Every write is
   wrapped; a DB lock or a missing table degrades to a log line, never an exception escaping
   into the caller's loop. This mirrors the "one bad tick must not kill the loop" rule already
   used in every scheduler/poller loop in this project.
2. **It must not add meaningful load.** `jobs.worker`'s loop spins back-to-back while the queue
   is busy, so an unthrottled write would mean hundreds of pointless UPDATEs a minute. The
   throttle is an in-memory timestamp check — it costs nothing and touches the DB only when a
   write is actually due.
"""
from __future__ import annotations
import json
import logging
import time

from sqlalchemy import text

# Reused from services/system_health.py (not redefined) so a real restart and the reader's
# own DOWN-threshold can never drift onto two different numbers.
from services.system_health import STALE_MULTIPLIER

logger = logging.getLogger(__name__)

# Minimum seconds between two real DB writes for the same process. A monitor that refreshes
# every few seconds cannot meaningfully use anything finer than this, and the staleness window
# that decides DOWN (Step 6.2) is far wider.
MIN_WRITE_INTERVAL_SECONDS = 15

# process_name -> monotonic timestamp of the last real write, per process. Module-level because
# each background process is its own OS process; there is nothing to share across them.
_last_write = {}


def beat(db, process_name, status="RUNNING", detail=None, force=False,
         expected_interval_seconds=None):
    """Record that `process_name` is alive right now.

    Safe to call on every loop iteration — writes are throttled to at most one per
    MIN_WRITE_INTERVAL_SECONDS unless `force=True` (used for startup and for a status change,
    both of which are worth recording immediately).

    `expected_interval_seconds`: how often this process expects to beat. Callers should pass
    their real loop interval (clamped up to MIN_WRITE_INTERVAL_SECONDS, since a faster loop
    still only writes that often). Step 6.2's reader uses it to judge staleness per process
    rather than against one global window — without it, the 300s discovery scheduler and the
    2s job worker cannot both be judged correctly by the same rule.

    Returns True if a row was actually written, False if throttled or if the write failed.
    Callers are not expected to check the return value; it exists for tests.
    """
    now = time.monotonic()
    last = _last_write.get(process_name)
    if not force and last is not None and (now - last) < MIN_WRITE_INTERVAL_SECONDS:
        return False

    # A process that loops faster than the throttle still only lands a write per throttle
    # window, so that — not its loop speed — is its real observable beat rate.
    interval = max(expected_interval_seconds or MIN_WRITE_INTERVAL_SECONDS,
                   MIN_WRITE_INTERVAL_SECONDS)

    payload = "{}"
    if detail:
        try:
            payload = json.dumps(detail)
        except (TypeError, ValueError):
            # Never let an unserialisable detail value cost us the heartbeat itself -- the
            # timestamp is the part that matters, the context is a nice-to-have.
            logger.warning("heartbeat detail for %s was not JSON-serialisable, dropping it",
                           process_name)

    try:
        # started_at is preserved across an ordinary beat, so the monitor shows real uptime
        # rather than the age of the last beat -- BUT a real restart (a genuinely new OS
        # process reusing the same process_name) must reset it, or uptime silently reports
        # the OLD process's age forever. Found live, 2026-08-25, verifying Phase 6's own DoD
        # gate: stopped+restarted a real VPS service and watched `started_at` stay stuck 5
        # days in the past. The only real signal this beat is a genuine restart (as opposed
        # to the same process's own next beat) is the SAME staleness gap the reader itself
        # uses to call a process DOWN -- reused via STALE_MULTIPLIER, not a second threshold.
        db.execute(text("""
            INSERT INTO system_heartbeats
                (process_name, status, detail, expected_interval_seconds,
                 last_seen_at, started_at)
            VALUES (:name, :status, :detail, :interval,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(process_name) DO UPDATE SET
                status       = excluded.status,
                detail       = excluded.detail,
                expected_interval_seconds = excluded.expected_interval_seconds,
                last_seen_at = CURRENT_TIMESTAMP,
                started_at   = CASE
                    WHEN (julianday(CURRENT_TIMESTAMP) - julianday(system_heartbeats.last_seen_at)) * 86400.0
                         > system_heartbeats.expected_interval_seconds * :stale_multiplier
                    THEN CURRENT_TIMESTAMP
                    ELSE system_heartbeats.started_at
                END
        """), {"name": process_name, "status": status, "detail": payload,
               "interval": interval, "stale_multiplier": STALE_MULTIPLIER})
        db.commit()
        _last_write[process_name] = now
        return True
    except Exception:  # noqa: BLE001 - a monitoring write must never break what it monitors
        logger.warning("heartbeat write failed for %s", process_name, exc_info=True)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001 - the session may already be unusable; nothing to do
            pass
        return False


def beat_standalone(process_name, status="RUNNING", detail=None, force=False,
                    expected_interval_seconds=None):
    """`beat()` for a caller that has no session to lend -- opens and closes its own.

    Used by processes whose loop does not already hold a session (`jobs.worker` closes its
    session per job; `scraper_worker.async_runner` runs an asyncio loop and must not hold a
    sync session across awaits).
    """
    # Check the throttle BEFORE opening a session -- otherwise a 2s loop would open and close
    # a DB session every pass just to discover it had nothing to write.
    now = time.monotonic()
    last = _last_write.get(process_name)
    if not force and last is not None and (now - last) < MIN_WRITE_INTERVAL_SECONDS:
        return False

    from database.db_config import SessionLocal
    db = SessionLocal()
    try:
        return beat(db, process_name, status=status, detail=detail, force=force,
                    expected_interval_seconds=expected_interval_seconds)
    finally:
        db.close()
