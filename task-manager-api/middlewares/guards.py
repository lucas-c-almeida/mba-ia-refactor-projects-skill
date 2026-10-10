"""Guard for privileged operations: an operator credential supplied by configuration.

This is not an identity model: it invents no users, roles or policy. With no credential
configured the guarded operations answer 403 (closed by default).
"""
import hmac
from functools import wraps

from flask import current_app, request

from models.errors import ForbiddenError

OPERATOR_HEADER = 'X-Operator-Token'


def require_operator(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = (current_app.config.get('OPERATOR_TOKEN') or '').encode()
        given = (request.headers.get(OPERATOR_HEADER) or '').encode()
        if not expected or not hmac.compare_digest(given, expected):
            raise ForbiddenError('Acesso restrito ao operador')
        return view(*args, **kwargs)
    return wrapper
