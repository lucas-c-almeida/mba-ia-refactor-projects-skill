"""The application's notion of "now".

Timestamps are stored and compared as naive UTC values, exactly as before. The
successor named by the runtime's own deprecation warning for datetime.utcnow() is
datetime.now(timezone.utc); tzinfo is stripped so stored values, comparisons with
existing rows and their string form stay identical.
"""
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
