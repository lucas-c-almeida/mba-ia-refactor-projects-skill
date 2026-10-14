import hmac
from functools import wraps

from flask import current_app, request

from models.errors import ForbiddenError

OPERATOR_HEADER = 'X-Operator-Token'


def require_operator(view):
    """Guard for operator-only operations. Closed by default: with no OPERATOR_TOKEN
    configured every call is answered with 403."""

    @wraps(view)
    def guarded(*args, **kwargs):
        expected = current_app.config.get('OPERATOR_TOKEN')
        given = request.headers.get(OPERATOR_HEADER, '')
        allowed = bool(expected) and hmac.compare_digest(given.encode(), expected.encode())
        if not allowed:
            raise ForbiddenError('Acesso restrito')
        return view(*args, **kwargs)

    return guarded
