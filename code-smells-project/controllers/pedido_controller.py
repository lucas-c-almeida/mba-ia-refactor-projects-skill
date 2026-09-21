"""Order use cases: creation (stock rules, total), listing, status transitions."""
from models.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PEDIDO_VALIDOS
from models.errors import BusinessRuleError, ValidationError


class PedidoController:
    def __init__(self, pedidos, produtos, notificador):
        self._pedidos = pedidos
        self._produtos = produtos
        self._notificador = notificador

    def criar(self, usuario_id, itens):
        """`itens` is a list of (produto_id, quantidade). Returns {"pedido_id", "total"}."""
        produtos = self._produtos.obter_varios(produto_id for produto_id, _ in itens)

        total = 0
        for produto_id, quantidade in itens:
            produto = produtos.get(produto_id)
            if produto is None:
                raise BusinessRuleError("Produto " + str(produto_id) + " não encontrado")
            if produto["estoque"] < quantidade:
                raise BusinessRuleError("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * quantidade)

        pedido_id = self._pedidos.criar(
            usuario_id,
            total,
            [(produto_id, quantidade, produtos[produto_id]["preco"]) for produto_id, quantidade in itens],
        )
        self._notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar(self):
        return self._pedidos.listar()

    def listar_do_usuario(self, usuario_id):
        return self._pedidos.listar(usuario_id=usuario_id)

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise ValidationError("Status inválido")
        self._pedidos.atualizar_status(pedido_id, novo_status)
        if novo_status == STATUS_APROVADO:
            self._notificador.pedido_aprovado(pedido_id)
        if novo_status == STATUS_CANCELADO:
            self._notificador.pedido_cancelado(pedido_id)
