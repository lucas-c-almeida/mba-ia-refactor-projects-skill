"""Order persistence and the order-placement rules."""
import json

from models.constants import STATUS_PENDENTE
from models.errors import ValidationError

_SELECT_PEDIDOS = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           pr.id AS produto_existente, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _montar_pedidos(rows):
    """Group the joined rows back into orders with their items (one query, no N+1)."""
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["pedido_id"])
        if pedido is None:
            pedido = {
                "id": row["pedido_id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["pedido_id"]] = pedido
        if row["produto_id"] is not None or row["quantidade"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_existente"] is not None else "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


class PedidoRepository:
    def __init__(self, db):
        self._db = db

    def criar(self, usuario_id, itens):
        """Place an order atomically: validate stock, insert, decrement. Rolls back on any failure."""
        with self._db.session() as conn:
            # One set-based read for every product of the order (ids bound as a single JSON array).
            ids = json.dumps(sorted({item["produto_id"] for item in itens}))
            produtos = {
                row["id"]: row
                for row in conn.execute(
                    "SELECT * FROM produtos WHERE id IN (SELECT value FROM json_each(?))", (ids,)
                ).fetchall()
            }

            total = 0
            linhas = []
            demanda = {}
            for item in itens:
                produto = produtos.get(item["produto_id"])
                if produto is None:
                    raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado", sucesso_false=True)
                if produto["estoque"] < item["quantidade"]:
                    raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso_false=True)
                total = total + (produto["preco"] * item["quantidade"])
                linhas.append((item["produto_id"], item["quantidade"], produto["preco"]))
                demanda[item["produto_id"]] = demanda.get(item["produto_id"], 0) + item["quantidade"]

            for produto_id, quantidade in demanda.items():
                if produtos[produto_id]["estoque"] < quantidade:
                    raise ValidationError("Estoque insuficiente para " + produtos[produto_id]["nome"], sucesso_false=True)

            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid

            conn.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, produto_id, quantidade, preco) for produto_id, quantidade, preco in linhas],
            )
            # The stock guard is in the statement itself, so two concurrent orders cannot oversell.
            baixa = conn.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                [(quantidade, produto_id, quantidade) for produto_id, quantidade in demanda.items()],
            )
            if baixa.rowcount != len(demanda):
                raise ValidationError("Estoque insuficiente", sucesso_false=True)
            return {"pedido_id": pedido_id, "total": total}

    def listar_por_usuario(self, usuario_id):
        with self._db.session() as conn:
            rows = conn.execute(
                _SELECT_PEDIDOS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
            ).fetchall()
            return _montar_pedidos(rows)

    def listar_todos(self):
        with self._db.session() as conn:
            rows = conn.execute(_SELECT_PEDIDOS + " ORDER BY p.id, i.id").fetchall()
            return _montar_pedidos(rows)

    def atualizar_status(self, pedido_id, novo_status):
        with self._db.session() as conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
