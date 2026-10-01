"""Order: status enumeration, item validation, total computation and persistence
(AP-02, AP-10, AP-11, AP-12, AP-15)."""

from collections import namedtuple

from models.errors import FALHA, BusinessRuleError, ValidationError


class StatusPedido:
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

    TODOS = (PENDENTE, APROVADO, ENVIADO, ENTREGUE, CANCELADO)


PRODUTO_DESCONHECIDO = "Desconhecido"

ItemPedido = namedtuple("ItemPedido", "produto_id quantidade")


def _inteiro(valor):
    """An integer identifier, as a client sends it (number or digit string); None otherwise."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor)
    return None


def normalizar_usuario_id(valor):
    usuario_id = _inteiro(valor)
    if usuario_id is None:
        raise ValidationError("Usuario ID inválido")
    return usuario_id


def validar_itens(itens):
    """Boundary invariants of an order line (AP-11): known product id, positive integer quantity."""
    if not isinstance(itens, list):
        raise ValidationError("Itens do pedido inválidos")
    validos = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item de pedido inválido")
        produto_id = _inteiro(item.get("produto_id"))
        if produto_id is None:
            raise ValidationError("Produto inválido no pedido")
        quantidade = item.get("quantidade")
        if isinstance(quantidade, bool) or not isinstance(quantidade, int) or quantidade <= 0:
            raise ValidationError("Quantidade deve ser um inteiro positivo")
        validos.append(ItemPedido(produto_id, quantidade))
    return validos


def calcular_total(itens, produtos):
    """Check every line against its product, in order, and sum price x quantity.

    Stock is checked against the quantity requested so far for that product across the whole
    order, so repeating a product in several lines cannot take its stock below zero.
    """
    total = 0
    solicitado = {}
    for item in itens:
        produto = produtos.get(item.produto_id)
        if produto is None:
            raise BusinessRuleError(
                "Produto " + str(item.produto_id) + " não encontrado", extra=FALHA
            )
        solicitado[item.produto_id] = solicitado.get(item.produto_id, 0) + item.quantidade
        if produto["estoque"] < solicitado[item.produto_id]:
            raise BusinessRuleError("Estoque insuficiente para " + produto["nome"], extra=FALHA)
        total = total + (produto["preco"] * item.quantidade)
    return total


_SELECT_PEDIDOS_COM_ITENS = (
    "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em, "
    "       i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario, "
    "       pr.nome AS produto_nome "
    "  FROM pedidos p "
    "  LEFT JOIN itens_pedido i ON i.pedido_id = p.id "
    "  LEFT JOIN produtos pr ON pr.id = i.produto_id "
)


def _agrupar_pedidos(linhas):
    pedidos = []
    por_id = {}
    for linha in linhas:
        pedido = por_id.get(linha["id"])
        if pedido is None:
            pedido = {
                "id": linha["id"],
                "usuario_id": linha["usuario_id"],
                "status": linha["status"],
                "total": linha["total"],
                "criado_em": linha["criado_em"],
                "itens": [],
            }
            por_id[linha["id"]] = pedido
            pedidos.append(pedido)
        if linha["item_id"] is None:
            continue
        nome = linha["produto_nome"]
        pedido["itens"].append({
            "produto_id": linha["produto_id"],
            "produto_nome": nome if nome is not None else PRODUTO_DESCONHECIDO,
            "quantidade": linha["quantidade"],
            "preco_unitario": linha["preco_unitario"],
        })
    return pedidos


class PedidoRepository:
    def __init__(self, conexao):
        self._conexao = conexao

    def criar(self, usuario_id, total, linhas):
        """Insert the order, its lines and the stock decrements in one transaction (AP-09, AP-10).

        `linhas` is a list of (produto_id, quantidade, preco_unitario).
        """
        conexao = self._conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, StatusPedido.PENDENTE, total),
            )
            pedido_id = cursor.lastrowid
            conexao.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                [(pedido_id, produto_id, quantidade, preco) for produto_id, quantidade, preco in linhas],
            )
            conexao.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(quantidade, produto_id) for produto_id, quantidade, _ in linhas],
            )
        return pedido_id

    def listar_todos(self):
        linhas = self._conexao().execute(
            _SELECT_PEDIDOS_COM_ITENS + "ORDER BY p.id, i.id"
        ).fetchall()
        return _agrupar_pedidos(linhas)

    def listar_por_usuario(self, usuario_id):
        linhas = self._conexao().execute(
            _SELECT_PEDIDOS_COM_ITENS + "WHERE p.usuario_id = ? ORDER BY p.id, i.id",
            (usuario_id,),
        ).fetchall()
        return _agrupar_pedidos(linhas)

    def atualizar_status(self, pedido_id, status):
        conexao = self._conexao()
        with conexao:
            conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
