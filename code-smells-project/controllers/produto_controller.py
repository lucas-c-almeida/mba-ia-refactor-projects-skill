import logging

from models.errors import FALHA, NotFoundError
from models.produto import validar_dados_produto

logger = logging.getLogger(__name__)

PRODUTO_NAO_ENCONTRADO = "Produto não encontrado"


class ProdutoController:
    def __init__(self, produtos):
        self._produtos = produtos

    def listar(self):
        produtos = self._produtos.listar_todos()
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self._produtos.obter_por_id(produto_id)
        if produto is None:
            raise NotFoundError(PRODUTO_NAO_ENCONTRADO, extra=FALHA)
        return produto

    def criar(self, dados):
        valores = validar_dados_produto(dados)
        produto_id = self._produtos.criar(*valores)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        if self._produtos.obter_por_id(produto_id) is None:
            raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
        valores = validar_dados_produto(dados)
        self._produtos.atualizar(produto_id, *valores)

    def remover(self, produto_id):
        if self._produtos.obter_por_id(produto_id) is None:
            raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
        self._produtos.remover(produto_id)
        logger.info("Produto %s deletado", produto_id)

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)
