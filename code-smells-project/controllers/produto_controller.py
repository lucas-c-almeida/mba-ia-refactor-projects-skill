"""Casos de uso de produto. Valores simples entram e saem; nada de HTTP aqui."""
import logging

from models.erros import NaoEncontrado
from models.produto import validar_dados_produto

logger = logging.getLogger(__name__)

MENSAGEM_NAO_ENCONTRADO = "Produto não encontrado"


class ProdutoController:
    def __init__(self, produtos, unidade_de_trabalho):
        self._produtos = produtos
        self._transacao = unidade_de_trabalho

    def listar(self):
        produtos = self._produtos.listar()
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def buscar(self, produto_id):
        return self._produtos.buscar_por_id(produto_id)

    def pesquisar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.pesquisar(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        valido = validar_dados_produto(dados)
        with self._transacao():
            produto_id = self._produtos.inserir(valido)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        with self._transacao():
            # Existência antes da validação: a ordem que o contrato já expunha.
            if self._produtos.buscar_por_id(produto_id) is None:
                raise NaoEncontrado(MENSAGEM_NAO_ENCONTRADO)
            self._produtos.atualizar(produto_id, validar_dados_produto(dados))

    def remover(self, produto_id):
        with self._transacao():
            if self._produtos.buscar_por_id(produto_id) is None:
                raise NaoEncontrado(MENSAGEM_NAO_ENCONTRADO)
            self._produtos.remover(produto_id)
        logger.info("Produto %s deletado", produto_id)
