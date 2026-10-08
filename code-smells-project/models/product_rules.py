"""Product input rules. Pure: no I/O, no framework.

The create and the update policies share the type and sign checks. They differ on purpose, as they
did before the refactoring: only create checks the name length and the category list. Making
update as strict as create is recorded as PROPOSED, NOT APPLIED (it would reject updates that are
accepted today).
"""

from models.constants import (
    DEFAULT_CATEGORY,
    PRODUCT_CATEGORIES,
    PRODUCT_NAME_MAX_LENGTH,
    PRODUCT_NAME_MIN_LENGTH,
)
from models.errors import ValidationError
from models.validation import is_number

_REQUIRED_FIELDS = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def _read_common_fields(payload):
    if not payload or not isinstance(payload, dict):
        raise ValidationError("Dados inválidos")
    for field, message in _REQUIRED_FIELDS:
        if field not in payload:
            raise ValidationError(message)

    nome = payload["nome"]
    descricao = payload.get("descricao", "")
    preco = payload["preco"]
    estoque = payload["estoque"]
    categoria = payload.get("categoria", DEFAULT_CATEGORY)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not is_number(estoque):
        raise ValidationError("Estoque deve ser numérico")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria deve ser texto")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    return nome, descricao, preco, estoque, categoria


def validate_new_product(payload):
    """Return (nome, descricao, preco, estoque, categoria) or raise ValidationError."""
    nome, descricao, preco, estoque, categoria = _read_common_fields(payload)
    if len(nome) < PRODUCT_NAME_MIN_LENGTH:
        raise ValidationError("Nome muito curto")
    if len(nome) > PRODUCT_NAME_MAX_LENGTH:
        raise ValidationError("Nome muito longo")
    if categoria not in PRODUCT_CATEGORIES:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(PRODUCT_CATEGORIES)))
    return nome, descricao, preco, estoque, categoria


def validate_product_update(payload):
    """Return (nome, descricao, preco, estoque, categoria) or raise ValidationError."""
    return _read_common_fields(payload)
