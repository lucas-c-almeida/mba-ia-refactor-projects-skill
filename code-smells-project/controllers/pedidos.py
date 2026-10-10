"""Order use cases. Plain values in, plain values out."""
import logging

from models.money import from_centavos
from models.pedido import STATUS_APROVADO, STATUS_CANCELADO, verificar_linha

logger = logging.getLogger(__name__)


class PedidoController:
    def __init__(self, pedidos, produtos, unidade_de_trabalho):
        self._pedidos = pedidos
        self._produtos = produtos
        # A callable returning a context manager that commits on success and rolls back on error.
        self._unidade_de_trabalho = unidade_de_trabalho

    def criar(self, usuario_id, itens):
        with self._unidade_de_trabalho():
            produtos = self._produtos.buscar_para_pedido(item["produto_id"] for item in itens)
            linhas = []
            total_centavos = 0
            for item in itens:
                produto = produtos.get(item["produto_id"])
                verificar_linha(produto, item["produto_id"], item["quantidade"])
                total_centavos += produto["preco_centavos"] * item["quantidade"]
                linhas.append((item["produto_id"], item["quantidade"], produto["preco_centavos"]))
            pedido_id = self._pedidos.inserir(usuario_id, total_centavos, linhas)
            self._produtos.baixar_estoque(
                [(produto_id, quantidade) for produto_id, quantidade, _ in linhas])
        self._notificar_criacao(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": from_centavos(total_centavos)}

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def listar_todos(self):
        return self._pedidos.listar_todos()

    def atualizar_status(self, pedido_id, novo_status):
        self._pedidos.atualizar_status(pedido_id, novo_status)
        if novo_status == STATUS_APROVADO:
            logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        if novo_status == STATUS_CANCELADO:
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)

    @staticmethod
    def _notificar_criacao(pedido_id, usuario_id):
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
