import logging

from models import produto as regras_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produtos):
        self._produtos = produtos

    def listar(self) -> list:
        produtos = self._produtos.listar()
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id: int):
        return self._produtos.buscar_por_id(produto_id)

    def pesquisar(self, termo, categoria, preco_min, preco_max) -> list:
        return self._produtos.pesquisar(termo, categoria, preco_min, preco_max)

    def criar(self, nome, descricao, preco, estoque, categoria) -> int:
        regras_produto.validar_invariantes(nome, preco, estoque, categoria)
        produto_id = self._produtos.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def existe(self, produto_id: int) -> bool:
        return self._produtos.buscar_por_id(produto_id) is not None

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria) -> None:
        regras_produto.validar_invariantes(nome, preco, estoque, categoria)
        self._produtos.atualizar(produto_id, nome, descricao, preco, estoque, categoria)

    def remover(self, produto_id: int) -> bool:
        if self._produtos.buscar_por_id(produto_id) is None:
            return False
        self._produtos.remover(produto_id)
        logger.info("Produto %s deletado", produto_id)
        return True
