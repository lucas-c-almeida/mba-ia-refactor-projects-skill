"""Product use cases. Plain values in, plain values out: no request or response objects."""
import logging

from errors import NotFoundError, ValidationError
from models.money import to_centavos
from models.produto import CATEGORIAS_VALIDAS, NOME_MAX_CARACTERES, NOME_MIN_CARACTERES

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produtos):
        self._produtos = produtos

    def listar(self):
        produtos = self._produtos.listar()
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado", sucesso=False)
        return produto

    def exigir_existente(self, produto_id):
        if not self._produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")

    def criar(self, nome, descricao, preco, estoque, categoria):
        if len(nome) < NOME_MIN_CARACTERES:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_MAX_CARACTERES:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
        produto_id = self._produtos.criar(nome, descricao, to_centavos(preco), estoque, categoria)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        self.exigir_existente(produto_id)
        self._produtos.atualizar(
            produto_id, nome, descricao, to_centavos(preco), estoque, categoria)

    def deletar(self, produto_id):
        self.exigir_existente(produto_id)
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)

    def pesquisar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(
            termo,
            categoria,
            to_centavos(preco_min) if preco_min else None,
            to_centavos(preco_max) if preco_max else None,
        )
