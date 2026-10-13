"""Operator-only guard: a credential from configuration, compared in constant time, closed by default."""
import hmac
from functools import wraps

from flask import request

from models.errors import ForbiddenError

CABECALHO_OPERADOR = "x-operator-token"


def exigir_operador(operator_token):
    """Wrap a view so it only runs with the configured operator token.

    With no token configured the guard never opens (the route answers 403).
    """

    def decorador(view):
        @wraps(view)
        def protegida(*args, **kwargs):
            fornecido = request.headers.get(CABECALHO_OPERADOR, "")
            autorizado = bool(operator_token) and hmac.compare_digest(
                fornecido.encode("utf-8"), operator_token.encode("utf-8")
            )
            if not autorizado:
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return protegida

    return decorador
