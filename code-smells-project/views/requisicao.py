"""Request parsing helpers shared by the views."""

from flask import request

from models.errors import ValidationError


def corpo_json():
    """The JSON body, or None when it is absent or not valid JSON."""
    return request.get_json(silent=True)


def corpo_objeto():
    """The JSON body when it is an object, otherwise an empty dict."""
    dados = corpo_json()
    return dados if isinstance(dados, dict) else {}


def texto(dados, campo):
    """A string field, or "" when absent or not a string."""
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


def numero_opcional(nome):
    """A query-string number, None when absent or empty; a malformed value is a client error."""
    bruto = request.args.get(nome, None)
    if not bruto:
        return bruto
    try:
        return float(bruto)
    except ValueError as exc:
        raise ValidationError("Parâmetro " + nome + " inválido") from exc
