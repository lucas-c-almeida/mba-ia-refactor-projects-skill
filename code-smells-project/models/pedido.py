"""Orders: domain rules and persistence."""
from errors import ValidationError
from models.money import from_centavos

STATUS_INICIAL = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_INICIAL, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]
PRODUTO_DESCONHECIDO = "Desconhecido"

_LISTAGEM = (
    "SELECT p.id AS id, p.usuario_id AS usuario_id, p.status AS status,"
    " p.total_centavos AS total_centavos, p.criado_em AS criado_em,"
    " i.produto_id AS produto_id, i.quantidade AS quantidade,"
    " i.preco_unitario_centavos AS preco_unitario_centavos,"
    " pr.id AS produto_existente, pr.nome AS produto_nome"
    " FROM pedidos p"
    " LEFT JOIN itens_pedido i ON i.pedido_id = p.id"
    " LEFT JOIN produtos pr ON pr.id = i.produto_id"
)
_ORDEM = " ORDER BY p.id, i.id"


def verificar_linha(produto, produto_id, quantidade):
    """Rules for one order line: the product exists and its stock covers the quantity."""
    if produto is None:
        raise ValidationError("Produto " + str(produto_id) + " não encontrado", sucesso=False)
    if produto["estoque"] < quantidade:
        raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)


def _agrupar(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["id"])
        if pedido is None:
            pedido = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": from_centavos(row["total_centavos"]),
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["id"]] = pedido
        if row["produto_id"] is not None:
            existe = row["produto_existente"] is not None
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if existe else PRODUTO_DESCONHECIDO,
                "quantidade": row["quantidade"],
                "preco_unitario": from_centavos(row["preco_unitario_centavos"]),
            })
    return list(pedidos.values())


class PedidoRepository:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def inserir(self, usuario_id, total_centavos, linhas):
        """Insert an order and its lines; ``linhas`` are (produto_id, quantidade, centavos)."""
        connection = self._get_connection()
        cursor = connection.execute(
            "INSERT INTO pedidos (usuario_id, status, total_centavos) VALUES (?, ?, ?)",
            (usuario_id, STATUS_INICIAL, total_centavos))
        pedido_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade,"
            " preco_unitario_centavos) VALUES (?, ?, ?, ?)",
            [(pedido_id, produto_id, quantidade, preco_unitario_centavos)
             for produto_id, quantidade, preco_unitario_centavos in linhas])
        return pedido_id

    def listar_todos(self):
        rows = self._get_connection().execute(_LISTAGEM + _ORDEM).fetchall()
        return _agrupar(rows)

    def listar_por_usuario(self, usuario_id):
        rows = self._get_connection().execute(
            _LISTAGEM + " WHERE p.usuario_id = ?" + _ORDEM, (usuario_id,)).fetchall()
        return _agrupar(rows)

    def atualizar_status(self, pedido_id, novo_status):
        self._get_connection().execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        return True
