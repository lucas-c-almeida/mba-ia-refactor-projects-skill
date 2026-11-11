"""Operator credential for privileged operations (RP-04). Not an identity model: it invents no
users or roles. Closed by default: with OPERATOR_TOKEN unset or empty, nobody passes."""
import hmac
from functools import wraps

from flask import request

from models.errors import ForbiddenError

OPERATOR_HEADER = 'X-Operator-Token'
FORBIDDEN = 'Acesso negado'


class OperatorGuard:
    def __init__(self, token):
        self._token = token

    def is_authorized(self):
        if not self._token:
            return False
        given = request.headers.get(OPERATOR_HEADER, '')
        return hmac.compare_digest(given.encode(), self._token.encode())

    def require(self, view):
        @wraps(view)
        def guarded(*args, **kwargs):
            if not self.is_authorized():
                raise ForbiddenError(FORBIDDEN)
            return view(*args, **kwargs)
        return guarded
