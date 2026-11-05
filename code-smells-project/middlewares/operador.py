"""Guard for operator-only routes: a credential from configuration, compared in constant
time, closed by default. With OPERATOR_TOKEN unset or empty, the route answers 403."""
import hmac
from functools import wraps

from flask import jsonify, request

CABECALHO_OPERADOR = "X-Operator-Token"


def criar_guarda_de_operador(token_configurado):
    def exigir_operador(view):
        @wraps(view)
        def protegida(*args, **kwargs):
            informado = request.headers.get(CABECALHO_OPERADOR, "")
            autorizado = bool(token_configurado) and hmac.compare_digest(
                informado.encode("utf-8"), token_configurado.encode("utf-8"))
            if not autorizado:
                return jsonify({"erro": "Acesso negado"}), 403
            return view(*args, **kwargs)
        return protegida
    return exigir_operador
