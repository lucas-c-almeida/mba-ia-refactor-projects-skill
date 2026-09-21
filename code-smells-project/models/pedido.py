"""Pedido: status, validação de entrada, regra de fechamento e persistência."""
from dataclasses import dataclass, field

from models.erros import ErroValidacao, RegraNegocioViolada

NOME_PRODUTO_DESCONHECIDO = "Desconhecido"


class StatusPedido:
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

    TODOS = (PENDENTE, APROVADO, ENVIADO, ENTREGUE, CANCELADO)


@dataclass(frozen=True)
class ItemSolicitado:
    produto_id: int
    quantidade: int


@dataclass(frozen=True)
class NovoPedido:
    usuario_id: int
    itens: tuple


@dataclass(frozen=True)
class ItemPedido:
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float


@dataclass
class Pedido:
    id: int
    usuario_id: int
    status: str
    total: float
    criado_em: str
    itens: list = field(default_factory=list)


def _inteiro(valor):
    """Aceita inteiro ou texto só com dígitos (o que o contrato já aceitava); senão None."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor)
    return None


def validar_novo_pedido(dados):
    if not isinstance(dados, dict) or not dados:
        raise ErroValidacao("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ErroValidacao("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ErroValidacao("Pedido deve ter pelo menos 1 item")

    usuario_id_valido = _inteiro(usuario_id)
    if usuario_id_valido is None:
        raise ErroValidacao("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ErroValidacao("Itens do pedido inválidos")

    solicitados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ErroValidacao("Item do pedido inválido")
        produto_id = _inteiro(item.get("produto_id"))
        if produto_id is None:
            raise ErroValidacao("Item do pedido inválido: produto_id deve ser inteiro")
        quantidade = item.get("quantidade")
        if isinstance(quantidade, bool) or not isinstance(quantidade, int) or quantidade <= 0:
            raise ErroValidacao("Item do pedido inválido: quantidade deve ser inteiro maior que zero")
        solicitados.append(ItemSolicitado(produto_id, quantidade))
    return NovoPedido(usuario_id_valido, tuple(solicitados))


def validar_status(dados):
    dados = dados if isinstance(dados, dict) else {}
    novo_status = dados.get("status", "")
    if novo_status not in StatusPedido.TODOS:
        raise ErroValidacao("Status inválido")
    return novo_status


def fechar_pedido(itens, produtos_por_id):
    """Confere existência e estoque de cada item, na ordem recebida, e calcula o total.

    Cada item é conferido contra o estoque lido antes do pedido (comportamento original,
    preservado).
    """
    total = 0
    for item in itens:
        produto = produtos_por_id.get(item.produto_id)
        if produto is None:
            raise RegraNegocioViolada("Produto " + str(item.produto_id) + " não encontrado")
        if produto.estoque < item.quantidade:
            raise RegraNegocioViolada("Estoque insuficiente para " + produto.nome)
        total = total + (produto.preco * item.quantidade)
    return total


class PedidoRepositorio:
    def __init__(self, provedor_conexao):
        self._conexao = provedor_conexao

    def inserir(self, usuario_id, total):
        cursor = self._conexao().execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, StatusPedido.PENDENTE, total),
        )
        return cursor.lastrowid

    def inserir_itens(self, pedido_id, itens_com_preco):
        """`itens_com_preco`: sequência de (produto_id, quantidade, preco_unitario)."""
        self._conexao().executemany(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            [(pedido_id, produto_id, quantidade, preco) for produto_id, quantidade, preco in itens_com_preco],
        )

    def listar(self, usuario_id=None):
        """Pedidos com seus itens numa única consulta (antes: 1 + N + N·M consultas)."""
        filtro, parametros = "", ()
        if usuario_id is not None:
            filtro, parametros = "WHERE p.usuario_id = ?", (usuario_id,)
        cursor = self._conexao().execute(
            f"""
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
                   pr.id AS produto_encontrado, pr.nome AS produto_nome
              FROM pedidos p
              LEFT JOIN itens_pedido i ON i.pedido_id = p.id
              LEFT JOIN produtos pr ON pr.id = i.produto_id
              {filtro}
             ORDER BY p.id, i.id
            """,
            parametros,
        )
        pedidos = {}
        for linha in cursor.fetchall():
            pedido = pedidos.get(linha["id"])
            if pedido is None:
                pedido = Pedido(linha["id"], linha["usuario_id"], linha["status"],
                                linha["total"], linha["criado_em"])
                pedidos[linha["id"]] = pedido
            if linha["item_id"] is not None:
                encontrado = linha["produto_encontrado"] is not None
                pedido.itens.append(ItemPedido(
                    linha["produto_id"],
                    linha["produto_nome"] if encontrado else NOME_PRODUTO_DESCONHECIDO,
                    linha["quantidade"],
                    linha["preco_unitario"],
                ))
        return list(pedidos.values())

    def atualizar_status(self, pedido_id, novo_status):
        self._conexao().execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
