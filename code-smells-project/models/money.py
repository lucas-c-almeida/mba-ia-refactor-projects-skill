"""Money is stored and computed as integer cents; it crosses the boundary as a decimal
number of reais, as it always has."""
from decimal import ROUND_HALF_UP, Decimal

CENTS_PER_UNIT = 100
INT64_MAX = 2 ** 63 - 1


def to_cents(amount):
    """A finite non-negative int/float amount -> integer cents (half-up)."""
    return int((Decimal(str(amount)) * CENTS_PER_UNIT).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def from_cents(cents):
    """Integer cents -> the float the API has always returned."""
    if cents is None:
        return None
    return cents / CENTS_PER_UNIT


def quantize_to_cents(value):
    """A Decimal amount in reais -> float rounded to the cent, half-up."""
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
