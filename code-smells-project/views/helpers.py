"""Delivery-boundary helpers: reading the request and shaping what leaves."""

from flask import request

from models.constants import REDACTED
from models.errors import ValidationError


def json_body():
    """The JSON body, or None when it is absent or malformed (the use case answers 400)."""
    return request.get_json(silent=True)


def optional_float(name):
    """A float query parameter; an empty or absent one is None, a non-numeric one is a 400."""
    raw = request.args.get(name, None)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        raise ValidationError(name + " deve ser numérico")


def present_user(user) -> dict:
    """Allow-list presentation of a user: the password field is kept, its value never leaves."""
    return {
        "id": user["id"],
        "nome": user["nome"],
        "email": user["email"],
        "senha": REDACTED,
        "tipo": user["tipo"],
        "criado_em": user["criado_em"],
    }
