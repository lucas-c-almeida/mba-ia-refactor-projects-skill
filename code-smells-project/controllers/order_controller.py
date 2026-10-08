"""Order use cases. Plain values in, plain values out; no request or response objects."""

from models.constants import ORDER_STATUSES
from models.errors import BusinessRuleError, ValidationError
from models.order import order_total
from models.validation import is_number


def _as_id(value):
    """An identifier as an int: ints, integral floats and digit strings are accepted."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


class OrderController:
    def __init__(self, orders, products, notifier):
        self._orders = orders
        self._products = products
        self._notifier = notifier

    def create_order(self, payload) -> dict:
        if not payload or not isinstance(payload, dict):
            raise ValidationError("Dados inválidos")
        raw_user_id = payload.get("usuario_id")
        raw_items = payload.get("itens", [])
        if not raw_user_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not raw_items or len(raw_items) == 0:
            raise ValidationError("Pedido deve ter pelo menos 1 item")

        user_id = _as_id(raw_user_id)
        if user_id is None:
            raise ValidationError("Usuario ID inválido")
        lines = self._read_lines(raw_items)

        products = self._products.find_many([line["produto_id"] for line in lines])
        priced_lines = []
        for line in lines:
            product = products.get(line["produto_id"])
            if product is None:
                raise BusinessRuleError(
                    "Produto " + str(line["produto_id"]) + " não encontrado", failure_flag=True
                )
            if product["estoque"] < line["quantidade"]:
                raise BusinessRuleError(
                    "Estoque insuficiente para " + product["nome"], failure_flag=True
                )
            priced_lines.append({**line, "preco_unitario": product["preco"]})

        total = order_total(priced_lines)
        order_id = self._orders.create(user_id, priced_lines, total)
        self._notifier.order_created(order_id, raw_user_id)
        return {"pedido_id": order_id, "total": total}

    @staticmethod
    def _read_lines(raw_items) -> list:
        if not isinstance(raw_items, list):
            raise ValidationError("Itens inválidos")
        lines = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise ValidationError("Itens inválidos")
            product_id = _as_id(item.get("produto_id"))
            quantity = item.get("quantidade")
            if product_id is None:
                raise ValidationError("Itens inválidos")
            if not is_number(quantity) or quantity < 0:
                raise ValidationError("Quantidade inválida")
            lines.append({"produto_id": product_id, "quantidade": quantity})
        return lines

    def list_orders(self) -> list:
        return self._orders.list_all()

    def list_orders_for_user(self, user_id) -> list:
        return self._orders.list_for_user(user_id)

    def update_status(self, order_id, payload) -> None:
        if not isinstance(payload, dict):
            raise ValidationError("Dados inválidos")
        new_status = payload.get("status", "")
        if new_status not in ORDER_STATUSES:
            raise ValidationError("Status inválido")
        self._orders.update_status(order_id, new_status)
        self._notifier.order_status_changed(order_id, new_status)
