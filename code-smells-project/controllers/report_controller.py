"""Management report use case (operator-only; the guard is applied at the route)."""
from models.sales_report import build_report


class ReportController:
    def __init__(self, orders):
        self._orders = orders

    def sales(self):
        return build_report(*self._orders.sales_aggregates())
