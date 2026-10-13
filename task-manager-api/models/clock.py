"""Time source for the domain (injectable in controllers)."""
from datetime import datetime, timezone


def utc_now():
    """Naive UTC timestamp: the storage and comparison format used by every column."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
