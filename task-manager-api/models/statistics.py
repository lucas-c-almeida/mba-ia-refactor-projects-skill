"""Shared arithmetic for the statistics endpoints."""
PERCENT = 100
PERCENT_DECIMALS = 2


def completion_rate(done, total):
    """Percentage of `total` that is `done`, rounded; 0 when there is nothing to divide."""
    return round((done / total) * PERCENT, PERCENT_DECIMALS) if total > 0 else 0
