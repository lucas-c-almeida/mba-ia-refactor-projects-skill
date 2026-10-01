"""The single source of the current time (AP-14, AP-06).

Replaces the deprecated `datetime.utcnow()` with its successor named by the runtime warning,
`datetime.now(timezone.utc)`, and drops the tzinfo so stored and serialized values keep the
naive-UTC format the API has always returned.
"""
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
