from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """The current UTC time, naive (no tzinfo) — the shape every column and comparison
    in this codebase already expects. `datetime.utcnow()` is deprecated (AP-14: observed
    via a DeprecationWarning raised from seed.py under Python 3.13, forced on with
    `PYTHONWARNINGS=always::DeprecationWarning python -X dev`); `datetime.now(timezone.utc)`
    is its documented successor but returns an AWARE datetime, which is not a drop-in
    replacement here — comparing an aware value against the naive ones already stored
    would raise TypeError. Stripping tzinfo keeps the exact value the old call produced.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
