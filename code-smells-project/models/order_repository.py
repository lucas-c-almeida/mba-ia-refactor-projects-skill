"""Persistence for orders and their items. Every statement is parameterized."""
from models import order_status
from models.database import transaction
from models.errors import BusinessRuleError

UNKNOWN_PRODUCT_NAME = "Desconhecido"

_LIST_QUERY = """
    SELECT p.id, p.usuario_id, p.status, p.total_centavos, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario_centavos,
           pr.id AS produto_encontrado, pr.nome AS produto_nome
      FROM pedidos p
      LEFT JOIN itens_pedido i ON i.pedido_id = p.id
      LEFT JOIN produtos pr ON pr.id = i.produto_id
     {where}
     ORDER BY p.id, i.id
"""


def _group(rows):
    orders, by_id = [], {}
    for row in rows:
        order = by_id.get(row["id"])
        if order is None:
            order = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total_centavos": row["total_centavos"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            by_id[row["id"]] = order
            orders.append(order)
        if row["item_id"] is not None:
            order["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_encontrado"] is not None
                else UNKNOWN_PRODUCT_NAME,
                "quantidade": row["quantidade"],
                "preco_unitario_centavos": row["preco_unitario_centavos"],
            })
    return orders


class OrderRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def list_all(self):
        return _group(self._connection().execute(_LIST_QUERY.format(where="")))

    def list_for_user(self, user_id):
        return _group(self._connection().execute(_LIST_QUERY.format(where="WHERE p.usuario_id = ?"), (user_id,)))

    def create(self, user_id, lines, total_cents):
        """lines: [(produto_id, quantidade, preco_unitario_centavos, nome)]. All or nothing."""
        connection = self._connection()
        with transaction(connection):
            cursor = connection.execute(
                "INSERT INTO pedidos (usuario_id, status, total_centavos) VALUES (?, ?, ?)",
                (user_id, order_status.INITIAL, total_cents),
            )
            order_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario_centavos) "
                "VALUES (?, ?, ?, ?)",
                [(order_id, product_id, quantity, unit_cents) for product_id, quantity, unit_cents, _ in lines],
            )
            requested = {}
            for product_id, quantity, _, _ in lines:
                requested[product_id] = requested.get(product_id, 0) + quantity
            # The stock check and the decrement are one statement per product, sent as one
            # batch: a product whose stock no longer covers the order is not updated, the
            # count comes up short, and the whole order rolls back (no oversell).
            updated = connection.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                [(quantity, product_id, quantity) for product_id, quantity in requested.items()],
            ).rowcount
            if updated != len(requested):
                raise BusinessRuleError("Estoque insuficiente", with_success_flag=True)
        return order_id

    def update_status(self, order_id, status):
        connection = self._connection()
        with transaction(connection):
            connection.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, order_id))

    def sales_aggregates(self):
        row = self._connection().execute(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(total_centavos), 0) AS gross_cents,
                   COALESCE(SUM(status = ?), 0) AS pending,
                   COALESCE(SUM(status = ?), 0) AS approved,
                   COALESCE(SUM(status = ?), 0) AS cancelled
              FROM pedidos
            """,
            (order_status.PENDENTE, order_status.APROVADO, order_status.CANCELADO),
        ).fetchone()
        return row["total"], row["gross_cents"], row["pending"], row["approved"], row["cancelled"]
