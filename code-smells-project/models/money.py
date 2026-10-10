"""Exact money arithmetic: amounts are stored and computed as integer centavos.

The boundary keeps the type clients already receive: a JSON number in currency units.
"""
from decimal import ROUND_HALF_UP, Decimal

CENTAVOS_POR_UNIDADE = 100
CASAS_DECIMAIS = 2


def to_centavos(value):
    """Convert a currency amount (int, float or numeric text) to integer centavos."""
    exact = Decimal(str(value)) * CENTAVOS_POR_UNIDADE
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_centavos(centavos):
    """Convert integer centavos to the number clients receive."""
    return round(centavos / CENTAVOS_POR_UNIDADE, CASAS_DECIMAIS)
