from datetime import datetime, timezone


def utc_now():
    """Current UTC time as a naive datetime (the columns store naive UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
