def completion_rate(done, total):
    """Percentage of finished items, two decimals; 0 when there is nothing to count."""
    return round((done / total) * 100, 2) if total > 0 else 0
