from models import pedido as regras_pedido
from models.erros import ErroDeRegraDeNegocio


class PedidoController:
    def __init__(self, pedidos, produtos, usuarios, notificador):
        self._pedidos = pedidos
        self._produtos = produtos
        self._usuarios = usuarios
        self._notificador = notificador

    def criar(self, usuario_id: int, itens: list) -> dict:
        if not self._usuarios.existe(usuario_id):
            raise ErroDeRegraDeNegocio("Usuário " + str(usuario_id) + " não encontrado")

        produtos = self._produtos.buscar_varios(item["produto_id"] for item in itens)
        solicitado = {}
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ErroDeRegraDeNegocio("Produto " + str(item["produto_id"]) + " não encontrado")
            # Lines for the same product draw on the same stock.
            solicitado[item["produto_id"]] = solicitado.get(item["produto_id"], 0) + item["quantidade"]
            if produto["estoque"] < solicitado[item["produto_id"]]:
                raise ErroDeRegraDeNegocio("Estoque insuficiente para " + produto["nome"])

        total = regras_pedido.calcular_total(itens, produtos)
        pedido_id = self._pedidos.criar(usuario_id, total, itens, produtos)
        self._notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self) -> list:
        return self._pedidos.listar()

    def listar_do_usuario(self, usuario_id: int) -> list:
        return self._pedidos.listar(usuario_id)

    def atualizar_status(self, pedido_id: int, status: str) -> bool:
        """False when the order does not exist."""
        if not self._pedidos.atualizar_status(pedido_id, status):
            return False
        self._notificador.status_alterado(pedido_id, status)
        return True
