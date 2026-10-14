"""Product use cases."""
import logging

from controllers.validation import eh_numero, exigir_objeto, exigir_tipo
from models.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)
from models.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _eh_texto(valor):
    return isinstance(valor, str)


def _extrair_campos(dados):
    """Required keys (in the original order of checks) and value types."""
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)
    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    exigir_tipo(nome, _eh_texto, "nome")
    exigir_tipo(descricao, _eh_texto, "descricao")
    exigir_tipo(preco, eh_numero, "preco")
    exigir_tipo(estoque, eh_numero, "estoque")
    exigir_tipo(categoria, _eh_texto, "categoria")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    return nome, descricao, preco, estoque, categoria


def _converter_preco(valor, campo):
    if not valor:
        return valor
    try:
        return float(valor)
    except ValueError:
        raise ValidationError("Valor inválido para '" + campo + "'")


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
            raise NotFoundError("Produto não encontrado", sucesso_false=True)
        return produto

    def criar(self, dados):
        exigir_objeto(dados)
        nome, descricao, preco, estoque, categoria = _extrair_campos(dados)
        if len(nome) < NOME_PRODUTO_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_PRODUTO_MAX:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
        produto_id = self._produtos.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        if not self._produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        exigir_objeto(dados)
        nome, descricao, preco, estoque, categoria = _extrair_campos(dados)
        self._produtos.atualizar(produto_id, nome, descricao, preco, estoque, categoria)

    def deletar(self, produto_id):
        if not self._produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)

    def buscar_por_filtros(self, termo, categoria, preco_min, preco_max):
        preco_min = _converter_preco(preco_min, "preco_min")
        preco_max = _converter_preco(preco_max, "preco_max")
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)
