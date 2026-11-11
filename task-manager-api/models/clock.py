from datetime import datetime, timezone


def utcnow():
    """Current UTC time as a naive datetime, the representation stored in the database.

    Successor of the deprecated datetime.utcnow() (RP-14): same value, same string format.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SystemClock:
    """The clock injected into controllers (RP-06); tests can pass their own."""

    def now(self):
        return utcnow()
