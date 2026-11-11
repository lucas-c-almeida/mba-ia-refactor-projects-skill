"""Order use cases: placing an order, listing, and changing its status."""
from models.errors import BusinessRuleError


class OrderController:
    def __init__(self, orders, products, users, notifier):
        self._orders = orders
        self._products = products
        self._users = users
        self._notifier = notifier

    def place(self, user_id, items):
        """items: [(produto_id, quantidade)], already well-formed. Returns (order_id, total_cents)."""
        products = self._products.find_by_ids([product_id for product_id, _ in items])
        requested, lines, total_cents = {}, [], 0
        for product_id, quantity in items:
            product = products.get(product_id)
            if product is None:
                raise BusinessRuleError("Produto " + str(product_id) + " não encontrado", with_success_flag=True)
            requested[product_id] = requested.get(product_id, 0) + quantity
            if product["estoque"] < requested[product_id]:
                raise BusinessRuleError("Estoque insuficiente para " + str(product["nome"]), with_success_flag=True)
            lines.append((product_id, quantity, product["preco_centavos"], product["nome"]))
            total_cents += product["preco_centavos"] * quantity
        if not self._users.exists(user_id):
            raise BusinessRuleError("Usuário não encontrado", with_success_flag=True)
        order_id = self._orders.create(user_id, lines, total_cents)
        self._notifier.order_created(order_id, user_id)
        return order_id, total_cents

    def list_all(self):
        return self._orders.list_all()

    def list_for_user(self, user_id):
        return self._orders.list_for_user(user_id) if user_id is not None else []

    def change_status(self, order_id, status):
        # An identifier outside the column's range matches no order: nothing to update,
        # and the answer stays the success it has always been.
        if order_id is not None:
            self._orders.update_status(order_id, status)
            self._notifier.order_status_changed(order_id, status)
