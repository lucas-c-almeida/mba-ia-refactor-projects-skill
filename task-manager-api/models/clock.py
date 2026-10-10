from datetime import datetime, timezone


def utc_now():
    """Current UTC time as a naive datetime.

    The stored values and every comparison in the application are naive UTC, so
    the timezone is dropped on purpose: this keeps the exact values the
    deprecated ``datetime.utcnow()`` produced.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
