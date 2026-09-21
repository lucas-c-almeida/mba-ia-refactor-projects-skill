"""Product use cases. Plain values in, plain values out; no HTTP."""
import logging

from models import regras_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produtos):
        self._produtos = produtos

    def listar(self):
        produtos = self._produtos.listar()
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        return self._produtos.obter(produto_id)

    def existe(self, produto_id):
        return self._produtos.obter(produto_id) is not None

    def criar(self, nome, descricao, preco, estoque, categoria):
        regras_produto.validar_para_criacao(nome, preco, estoque, categoria)
        produto_id = self._produtos.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        regras_produto.validar_para_atualizacao(preco, estoque)
        self._produtos.atualizar(produto_id, nome, descricao, preco, estoque, categoria)

    def deletar(self, produto_id):
        """Return False when the product does not exist."""
        if not self.existe(produto_id):
            return False
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
        return True

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)
