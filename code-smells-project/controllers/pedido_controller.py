from models.errors import ValidationError
from models.pedido import StatusPedido, calcular_total, normalizar_usuario_id, validar_itens


class PedidoController:
    def __init__(self, pedidos, produtos, usuarios, notificador):
        self._pedidos = pedidos
        self._produtos = produtos
        self._usuarios = usuarios
        self._notificador = notificador

    def criar(self, usuario_id, itens):
        usuario_id = normalizar_usuario_id(usuario_id)
        itens = validar_itens(itens)
        if not self._usuarios.existe(usuario_id):
            raise ValidationError("Usuário não encontrado")

        produtos = self._produtos.obter_varios({item.produto_id for item in itens})
        total = calcular_total(itens, produtos)
        linhas = [
            (item.produto_id, item.quantidade, produtos[item.produto_id]["preco"]) for item in itens
        ]
        pedido_id = self._pedidos.criar(usuario_id, total, linhas)

        self._notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def listar_todos(self):
        return self._pedidos.listar_todos()

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in StatusPedido.TODOS:
            raise ValidationError("Status inválido")
        self._pedidos.atualizar_status(pedido_id, novo_status)

        if novo_status == StatusPedido.APROVADO:
            self._notificador.pedido_aprovado(pedido_id)
        if novo_status == StatusPedido.CANCELADO:
            self._notificador.pedido_cancelado(pedido_id)
