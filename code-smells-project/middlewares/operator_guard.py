"""Guard for operator-only operations: a credential from configuration, closed by default."""

import hmac
from functools import wraps

from flask import request

from models.constants import OPERATOR_TOKEN_HEADER
from models.errors import AccessDeniedError


def make_operator_guard(operator_token):
    """Build a decorator. With no token configured the guard always refuses (fail closed)."""

    def operator_required(view):
        @wraps(view)
        def guarded(*args, **kwargs):
            given = request.headers.get(OPERATOR_TOKEN_HEADER, "")
            allowed = bool(operator_token) and hmac.compare_digest(
                given.encode("utf-8"), operator_token.encode("utf-8")
            )
            if not allowed:
                raise AccessDeniedError("Acesso negado")
            return view(*args, **kwargs)

        return guarded

    return operator_required
