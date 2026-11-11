"""Guard for operator-only operations: a credential from configuration, compared in
constant time, closed when none is configured. Not an identity model: it invents no
users or roles; it only keeps anonymous callers out of a management operation."""
import hmac
from functools import wraps

from flask import request

from models.errors import ForbiddenError

OPERATOR_HEADER = "X-Operator-Token"


def require_operator(operator_token):
    def decorator(view):
        @wraps(view)
        def guarded(*args, **kwargs):
            given = request.headers.get(OPERATOR_HEADER, "")
            if not operator_token or not hmac.compare_digest(given.encode("utf-8"), operator_token.encode("utf-8")):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)
        return guarded
    return decorator
