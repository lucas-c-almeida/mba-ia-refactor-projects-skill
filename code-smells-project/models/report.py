"""Sales report: aggregate reads and the pure computation on top of them."""

from models.constants import (
    ORDER_STATUS_APPROVED,
    ORDER_STATUS_CANCELED,
    ORDER_STATUS_PENDING,
    REVENUE_DISCOUNT_TIERS,
)


def applicable_discount(revenue):
    for threshold, rate in REVENUE_DISCOUNT_TIERS:
        if revenue > threshold:
            return revenue * rate
    return 0


def build_sales_report(total_orders, revenue, status_counts) -> dict:
    if revenue is None:
        revenue = 0
    discount = applicable_discount(revenue)
    return {
        "total_pedidos": total_orders,
        "faturamento_bruto": round(revenue, 2),
        "desconto_aplicavel": round(discount, 2),
        "faturamento_liquido": round(revenue - discount, 2),
        "pedidos_pendentes": status_counts.get(ORDER_STATUS_PENDING, 0),
        "pedidos_aprovados": status_counts.get(ORDER_STATUS_APPROVED, 0),
        "pedidos_cancelados": status_counts.get(ORDER_STATUS_CANCELED, 0),
        "ticket_medio": round(revenue / total_orders, 2) if total_orders > 0 else 0,
    }


class ReportRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def sales_report(self) -> dict:
        connection = self._connection()
        total_orders, revenue = connection.execute(
            "SELECT COUNT(*), SUM(total) FROM pedidos"
        ).fetchone()
        status_counts = {
            row[0]: row[1]
            for row in connection.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status")
        }
        return build_sales_report(total_orders, revenue, status_counts)

    def ping(self) -> None:
        self._connection().execute("SELECT 1")

    def entity_counts(self) -> dict:
        connection = self._connection()
        return {
            "produtos": connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
            "usuarios": connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
            "pedidos": connection.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
        }
