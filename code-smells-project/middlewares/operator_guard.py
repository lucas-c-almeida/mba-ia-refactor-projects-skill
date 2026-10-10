"""Guard for operator-only operations: a credential from configuration, closed by default."""
import functools
import hmac

from flask import request

from errors import ForbiddenError

HEADER_OPERADOR = "X-Operator-Token"


def exigir_operador(operator_token):
    """Decorator factory. With no token configured, every call is refused (fail closed)."""
    esperado = (operator_token or "").encode("utf-8")

    def decorador(view):
        @functools.wraps(view)
        def protegida(*args, **kwargs):
            recebido = (request.headers.get(HEADER_OPERADOR) or "").encode("utf-8")
            if not esperado or not hmac.compare_digest(recebido, esperado):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return protegida

    return decorador
