"""Orders: status set, total computation and persistence."""
from decimal import Decimal


class StatusPedido:
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"
    TODOS = (PENDENTE, APROVADO, ENVIADO, ENTREGUE, CANCELADO)


PRODUTO_DESCONHECIDO = "Desconhecido"


def calcular_total(itens, produtos) -> float:
    """Exact decimal sum of price x quantity; converted to a JSON number once, at the end."""
    total = sum(
        (Decimal(str(produtos[item["produto_id"]]["preco"])) * item["quantidade"] for item in itens),
        Decimal(0),
    )
    return float(total)


class PedidoRepository:
    def __init__(self, obter_conexao):
        self._obter_conexao = obter_conexao

    def criar(self, usuario_id, total, itens, produtos) -> int:
        """Order, lines and stock decrement in one transaction: all of it or none of it."""
        conexao = self._obter_conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, StatusPedido.PENDENTE, total),
            )
            pedido_id = cursor.lastrowid
            conexao.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                [(pedido_id, item["produto_id"], item["quantidade"],
                  produtos[item["produto_id"]]["preco"]) for item in itens],
            )
            conexao.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(item["quantidade"], item["produto_id"]) for item in itens],
            )
        return pedido_id

    def listar(self, usuario_id=None) -> list:
        """Orders with their lines, in two queries whatever the number of orders."""
        conexao = self._obter_conexao()
        if usuario_id is None:
            pedidos = conexao.execute(
                "SELECT * FROM pedidos ORDER BY id").fetchall()
            itens = conexao.execute(
                "SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, "
                "pr.nome AS produto_nome "
                "FROM itens_pedido i JOIN pedidos p ON p.id = i.pedido_id "
                "LEFT JOIN produtos pr ON pr.id = i.produto_id "
                "ORDER BY i.pedido_id, i.id").fetchall()
        else:
            pedidos = conexao.execute(
                "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id", (usuario_id,)).fetchall()
            itens = conexao.execute(
                "SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, "
                "pr.nome AS produto_nome "
                "FROM itens_pedido i JOIN pedidos p ON p.id = i.pedido_id "
                "LEFT JOIN produtos pr ON pr.id = i.produto_id "
                "WHERE p.usuario_id = ? ORDER BY i.pedido_id, i.id", (usuario_id,)).fetchall()

        itens_por_pedido = {}
        for item in itens:
            itens_por_pedido.setdefault(item["pedido_id"], []).append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] is not None
                else PRODUTO_DESCONHECIDO,
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return [
            {
                "id": pedido["id"],
                "usuario_id": pedido["usuario_id"],
                "status": pedido["status"],
                "total": pedido["total"],
                "criado_em": pedido["criado_em"],
                "itens": itens_por_pedido.get(pedido["id"], []),
            }
            for pedido in pedidos
        ]

    def atualizar_status(self, pedido_id: int, status: str) -> bool:
        """True when an order with this id existed and was updated."""
        conexao = self._obter_conexao()
        with conexao:
            cursor = conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
        return cursor.rowcount > 0

    def contar(self) -> int:
        return self._obter_conexao().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
