"""Handler registry, split out of jobs/worker.py (2026-08-14, real bug fix).

Real bug found live: `python -m jobs.worker` loads that file as `__main__`, a SEPARATE
module identity from `jobs.worker` (the package-qualified name). Every handler module's
`from jobs.worker import register_handler` therefore imported a SECOND, freshly-created
copy of worker.py -- with its own separate, empty HANDLERS dict -- so every registration
landed in a dict the __main__ instance never looked at. `HANDLERS` stayed silently empty
forever, no matter how many handler modules were imported. This is why the standalone
`jobs.worker` background process has never actually processed anything since Step 2.1 --
every real send this whole project made only happened because a one-off script called
`worker.run_once()` directly after importing the handler itself in the SAME process.

Splitting the registry into its own module (never run as __main__ itself) means there is
only ever one instance of it, imported the same way from every direction.
"""
from __future__ import annotations
HANDLERS = {}


def register_handler(job_type):
    def decorator(fn):
        HANDLERS[job_type] = fn
        return fn
    return decorator
