"""The system clock, in one place so rules can receive it instead of reading it (RP-06)."""
from datetime import datetime, timezone


def utc_now():
    """Current UTC time as a naive datetime.

    Successor of the deprecated ``datetime.utcnow()`` (Python 3.13 DeprecationWarning, observed
    2026-09-21), which names ``datetime.now(datetime.UTC)``. The tzinfo is dropped so stored and
    rendered values stay identical to what the application produced before (RP-14).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_now():
    """Current local time, as the health endpoint has always reported it."""
    return datetime.now()
