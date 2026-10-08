"""The single place that reads the system clock (RP-14).

`datetime.utcnow()` is deprecated; its documented successor returns a timezone-aware value. The
stored and compared datetimes in this application are naive UTC, so the successor is converted
back to the same naive form to keep every value and comparison identical.
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
