"""Product rules: one definition used by every operation that writes a product."""
from models.errors import ValidationError

VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
DEFAULT_CATEGORY = "geral"
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 200


def check_product_invariants(nome, preco, estoque, categoria):
    """The domain checks, in the order the API has always reported them."""
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < MIN_NAME_LENGTH:
        raise ValidationError("Nome muito curto")
    if len(nome) > MAX_NAME_LENGTH:
        raise ValidationError("Nome muito longo")
    if categoria not in VALID_CATEGORIES:
        raise ValidationError("Categoria inválida. Válidas: " + str(VALID_CATEGORIES))
