"""Order persistence and pricing. Reads are set-based; writes happen in one transaction."""

from models.constants import ORDER_STATUS_PENDING

_ITEMS_SELECT = """
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           CASE WHEN p.id IS NULL THEN 'Desconhecido' ELSE p.nome END AS produto_nome
      FROM itens_pedido i
      {join}
      LEFT JOIN produtos p ON p.id = i.produto_id
      {where}
     ORDER BY i.id
"""


def order_total(priced_lines) -> float:
    """Sum of unit price times quantity, accumulated in line order."""
    total = 0
    for line in priced_lines:
        total = total + (line["preco_unitario"] * line["quantidade"])
    return total


def _assemble(order_rows, item_rows) -> list:
    orders = []
    by_id = {}
    for row in order_rows:
        order = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }
        orders.append(order)
        by_id[row["id"]] = order
    for item in item_rows:
        order = by_id.get(item["pedido_id"])
        if order is None:
            continue
        order["itens"].append(
            {
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            }
        )
    return orders


class OrderRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def create(self, usuario_id, priced_lines, total) -> int:
        """Insert the order, its items and the stock decrement atomically."""
        connection = self._connection()
        try:
            cursor = connection.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, ORDER_STATUS_PENDING, total),
            )
            pedido_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [
                    (pedido_id, line["produto_id"], line["quantidade"], line["preco_unitario"])
                    for line in priced_lines
                ],
            )
            connection.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(line["quantidade"], line["produto_id"]) for line in priced_lines],
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        return pedido_id

    def list_all(self) -> list:
        connection = self._connection()
        order_rows = connection.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
        item_rows = connection.execute(_ITEMS_SELECT.format(join="", where="")).fetchall()
        return _assemble(order_rows, item_rows)

    def list_for_user(self, usuario_id) -> list:
        connection = self._connection()
        order_rows = connection.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id", (usuario_id,)
        ).fetchall()
        item_rows = connection.execute(
            _ITEMS_SELECT.format(
                join="JOIN pedidos o ON o.id = i.pedido_id", where="WHERE o.usuario_id = ?"
            ),
            (usuario_id,),
        ).fetchall()
        return _assemble(order_rows, item_rows)

    def update_status(self, order_id, new_status) -> None:
        connection = self._connection()
        connection.execute("UPDATE pedidos SET status = ? WHERE id = ?", (new_status, order_id))
        connection.commit()
