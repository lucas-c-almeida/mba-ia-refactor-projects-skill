"""Boundary checks on plain values (no framework objects)."""
from models.errors import ValidationError


def exigir_objeto(dados, permitir_vazio=False):
    """The body must be a JSON object (and, unless allowed, not empty)."""
    if not isinstance(dados, dict) or (not dados and not permitir_vazio):
        raise ValidationError("Dados inválidos")
    return dados


def eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def exigir_tipo(valor, tipo_ok, campo):
    if not tipo_ok(valor):
        raise ValidationError("Tipo inválido para o campo '" + campo + "'")


def como_inteiro(valor, campo):
    """Accept an integer or a numeric string; reject everything else."""
    if isinstance(valor, bool):
        raise ValidationError("Tipo inválido para o campo '" + campo + "'")
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str):
        try:
            return int(valor.strip())
        except ValueError:
            pass
    raise ValidationError("Tipo inválido para o campo '" + campo + "'")
