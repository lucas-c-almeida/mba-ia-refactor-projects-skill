"""The application's clock (RP-14, RP-06).

`datetime.utcnow()` is deprecated (DeprecationWarning observed on Python 3.13, which names
`datetime.now(datetime.UTC)` as the successor). The database stores naive UTC datetimes and the
API serializes them with `str()`, so the successor's aware value is converted back to naive UTC
here: stored values, comparisons and the serialized format stay exactly as before.
"""
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
