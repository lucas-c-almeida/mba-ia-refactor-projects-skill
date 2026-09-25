"""
Order persistence — parameterized queries (fixes AP-02); order listing collapsed
from a query-inside-a-loop-inside-a-loop into two batched queries (fixes AP-10,
RP-10); money stored as integer cents internally, same decimal shape at the boundary
(fixes part of AP-20).
"""
from src.models.errors import ConflictError, NotFoundError


def _cents_to_amount(cents: int) -> float:
    return round(cents / 100, 2)


def _amount_to_cents(amount) -> int:
    return round(float(amount) * 100)


class OrderRepository:
    def __init__(self, connection):
        self._connection = connection

    def criar(self, usuario_id: int, itens: list) -> dict:
        cursor = self._connection.cursor()
        total_cents = 0
        produtos_por_id = {}

        for item in itens:
            produto_id = item["produto_id"]
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
            produto = cursor.fetchone()
            if produto is None:
                # Both this and the stock check below map to 400 in the original
                # (both flow through the same "erro" in resultado branch), so both
                # raise ConflictError, not NotFoundError (which would be a 404 and
                # change the status code observed today).
                raise ConflictError(
                    "Produto {0} não encontrado".format(produto_id), sucesso=False
                )
            if produto["estoque"] < item["quantidade"]:
                raise ConflictError(
                    "Estoque insuficiente para {0}".format(produto["nome"]), sucesso=False
                )
            produtos_por_id[produto_id] = produto
            total_cents += produto["preco_cents"] * item["quantidade"]

        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total_cents) VALUES (?, 'pendente', ?)",
            (usuario_id, total_cents),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            produto = produtos_por_id[item["produto_id"]]
            cursor.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, "
                "preco_unitario_cents) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco_cents"]),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        self._connection.commit()
        return {"pedido_id": pedido_id, "total": _cents_to_amount(total_cents)}

    def _montar_pedidos(self, pedido_rows) -> list:
        """One query for every item of every order, one for every product name —
        instead of two additional round trips per order (the original's N+1)."""
        pedido_ids = [row["id"] for row in pedido_rows]
        if not pedido_ids:
            return []

        cursor = self._connection.cursor()
        placeholders = ",".join("?" for _ in pedido_ids)
        cursor.execute(
            "SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario_cents, "
            "p.nome AS produto_nome "
            "FROM itens_pedido ip LEFT JOIN produtos p ON p.id = ip.produto_id "
            "WHERE ip.pedido_id IN ({0})".format(placeholders),
            pedido_ids,
        )
        itens_por_pedido = {pid: [] for pid in pedido_ids}
        for row in cursor.fetchall():
            itens_por_pedido[row["pedido_id"]].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": _cents_to_amount(row["preco_unitario_cents"]),
                }
            )

        return [
            {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": _cents_to_amount(row["total_cents"]),
                "criado_em": row["criado_em"],
                "itens": itens_por_pedido[row["id"]],
            }
            for row in pedido_rows
        ]

    def get_por_usuario(self, usuario_id: int) -> list:
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id", (usuario_id,)
        )
        return self._montar_pedidos(cursor.fetchall())

    def get_todos(self) -> list:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM pedidos ORDER BY id")
        return self._montar_pedidos(cursor.fetchall())

    def contar(self) -> int:
        cursor = self._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        return cursor.fetchone()[0]

    def existe(self, pedido_id: int) -> bool:
        cursor = self._connection.cursor()
        cursor.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,))
        return cursor.fetchone() is not None

    def atualizar_status(self, pedido_id: int, novo_status: str) -> None:
        if not self.existe(pedido_id):
            raise NotFoundError("Pedido {0} não encontrado".format(pedido_id))
        cursor = self._connection.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        self._connection.commit()

    def relatorio_vendas(self) -> dict:
        from src.models.constants import (
            DISCOUNT_TIER_HIGH_RATE,
            DISCOUNT_TIER_HIGH_THRESHOLD,
            DISCOUNT_TIER_LOW_RATE,
            DISCOUNT_TIER_LOW_THRESHOLD,
            DISCOUNT_TIER_MID_RATE,
            DISCOUNT_TIER_MID_THRESHOLD,
        )

        cursor = self._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total_cents) FROM pedidos")
        faturamento_cents = cursor.fetchone()[0] or 0
        faturamento = _cents_to_amount(faturamento_cents)

        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
        pendentes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
        aprovados = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
        cancelados = cursor.fetchone()[0]

        if faturamento > DISCOUNT_TIER_HIGH_THRESHOLD:
            desconto = faturamento * DISCOUNT_TIER_HIGH_RATE
        elif faturamento > DISCOUNT_TIER_MID_THRESHOLD:
            desconto = faturamento * DISCOUNT_TIER_MID_RATE
        elif faturamento > DISCOUNT_TIER_LOW_THRESHOLD:
            desconto = faturamento * DISCOUNT_TIER_LOW_RATE
        else:
            desconto = 0

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
