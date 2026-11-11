"""Sales report rules: pure computation over aggregates, no I/O."""
from decimal import Decimal

from models.money import CENTS_PER_UNIT, quantize_to_cents

# Discount tiers on gross revenue, highest first: (threshold in cents, rate).
# A commercial rule: owned by the business, not by the code.
DISCOUNT_TIERS = [
    (1_000_000, Decimal("0.10")),   # above R$ 10.000,00
    (500_000, Decimal("0.05")),     # above R$ 5.000,00
    (100_000, Decimal("0.02")),     # above R$ 1.000,00
]


def discount_rate(gross_cents):
    for threshold_cents, rate in DISCOUNT_TIERS:
        if gross_cents > threshold_cents:
            return rate
    return Decimal(0)


def build_report(total_orders, gross_cents, pending, approved, cancelled):
    gross = Decimal(gross_cents) / CENTS_PER_UNIT
    discount = gross * discount_rate(gross_cents)
    return {
        "total_pedidos": total_orders,
        "faturamento_bruto": quantize_to_cents(gross),
        "desconto_aplicavel": quantize_to_cents(discount),
        "faturamento_liquido": quantize_to_cents(gross - discount),
        "pedidos_pendentes": pending,
        "pedidos_aprovados": approved,
        "pedidos_cancelados": cancelled,
        "ticket_medio": quantize_to_cents(gross / total_orders) if total_orders > 0 else 0,
    }
