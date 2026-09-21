"""Product invariants, defined once and shared by every path that writes a product."""
from models.constants import CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from models.errors import ValidationError


def validar_preco_estoque(preco, estoque):
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")


def validar_nome(nome):
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")


def validar_categoria(categoria):
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))


def validar_para_criacao(nome, preco, estoque, categoria):
    validar_preco_estoque(preco, estoque)
    validar_nome(nome)
    validar_categoria(categoria)


def validar_para_atualizacao(preco, estoque):
    # The update path has historically enforced only the non-negativity rules. Applying the
    # creation rules here would reject requests that are accepted today, so it is proposed,
    # not applied (see reports/audit-latest.md, PROPOSED, NOT APPLIED).
    validar_preco_estoque(preco, estoque)
