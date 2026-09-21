"""Casos de uso de pedido: fechamento transacional e mudança de status."""
from models.notificacao import Notificador
from models.pedido import fechar_pedido, validar_novo_pedido, validar_status


class PedidoController:
    def __init__(self, pedidos, produtos, notificador: Notificador, unidade_de_trabalho):
        self._pedidos = pedidos
        self._produtos = produtos
        self._notificador = notificador
        self._transacao = unidade_de_trabalho

    def criar(self, dados):
        """Devolve (pedido_id, total). Tudo ou nada: qualquer falha desfaz o pedido inteiro."""
        novo = validar_novo_pedido(dados)
        with self._transacao():
            produtos = self._produtos.buscar_por_ids(item.produto_id for item in novo.itens)
            total = fechar_pedido(novo.itens, produtos)
            pedido_id = self._pedidos.inserir(novo.usuario_id, total)
            self._pedidos.inserir_itens(pedido_id, [
                (item.produto_id, item.quantidade, produtos[item.produto_id].preco)
                for item in novo.itens
            ])
            self._produtos.baixar_estoque(
                [(item.produto_id, item.quantidade) for item in novo.itens]
            )
        self._notificador.pedido_criado(pedido_id, novo.usuario_id)
        return pedido_id, total

    def listar(self, usuario_id=None):
        return self._pedidos.listar(usuario_id)

    def atualizar_status(self, pedido_id, dados):
        novo_status = validar_status(dados)
        with self._transacao():
            self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notificador.status_alterado(pedido_id, novo_status)
