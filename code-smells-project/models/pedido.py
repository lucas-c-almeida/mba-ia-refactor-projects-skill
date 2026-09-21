"""Order persistence: atomic order creation, set-based listing, sales aggregates."""
from models.constants import (
    PRODUTO_DESCONHECIDO,
    STATUS_APROVADO,
    STATUS_CANCELADO,
    STATUS_PENDENTE,
)


class PedidoRepository:
    def __init__(self, connection_provider):
        self._conn = connection_provider

    def criar(self, usuario_id, total, itens):
        """Insert the order, its items and the stock decrements in one transaction.

        `itens` is a sequence of (produto_id, quantidade, preco_unitario).
        """
        conn = self._conn()
        with conn:  # commits on success, rolls back on any exception
            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, produto_id, quantidade, preco) for produto_id, quantidade, preco in itens],
            )
            conn.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(quantidade, produto_id) for produto_id, quantidade, _ in itens],
            )
        return pedido_id

    def listar(self, usuario_id=None):
        """Orders with their items and product names, in a single joined query."""
        sql = (
            "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em, "
            "       i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario, "
            "       pr.nome AS produto_nome "
            "FROM pedidos p "
            "LEFT JOIN itens_pedido i ON i.pedido_id = p.id "
            "LEFT JOIN produtos pr ON pr.id = i.produto_id "
        )
        params = ()
        if usuario_id is not None:
            sql += "WHERE p.usuario_id = ? "
            params = (usuario_id,)
        sql += "ORDER BY p.id, i.id"

        pedidos = {}
        for row in self._conn().execute(sql, params).fetchall():
            pedido = pedidos.get(row["id"])
            if pedido is None:
                pedido = {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
                pedidos[row["id"]] = pedido
            if row["item_id"] is not None:
                pedido["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] if row["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())

    def atualizar_status(self, pedido_id, status):
        conn = self._conn()
        with conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def resumo_vendas(self):
        row = self._conn().execute(
            "SELECT COUNT(*) AS total_pedidos, SUM(total) AS faturamento, "
            "       SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes, "
            "       SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados, "
            "       SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados "
            "FROM pedidos",
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return {
            "total_pedidos": row["total_pedidos"],
            "faturamento": row["faturamento"],
            "pendentes": row["pendentes"] or 0,
            "aprovados": row["aprovados"] or 0,
            "cancelados": row["cancelados"] or 0,
        }
