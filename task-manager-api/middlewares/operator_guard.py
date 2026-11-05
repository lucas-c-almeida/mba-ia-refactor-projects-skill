"""Operator credential for privileged operations (RP-04).

Not an identity model: one shared credential, configured through OPERATOR_TOKEN and sent in the
X-Operator-Token header. With no credential configured (unset or empty), every privileged
operation answers 403 — closed by default.
"""
import hmac
from functools import wraps

from flask import request

from models.errors import ForbiddenError

OPERATOR_HEADER = 'X-Operator-Token'
FORBIDDEN_MESSAGE = 'Operação restrita ao operador'


class OperatorGuard:
    def __init__(self, operator_token):
        self._token = operator_token.encode() if operator_token else None

    def is_operator(self):
        """True only when a credential is configured and the request presents it."""
        if not self._token:
            return False
        presented = request.headers.get(OPERATOR_HEADER, '').encode()
        return hmac.compare_digest(presented, self._token)

    def require(self, view):
        @wraps(view)
        def guarded(*args, **kwargs):
            if not self.is_operator():
                raise ForbiddenError(FORBIDDEN_MESSAGE)
            return view(*args, **kwargs)
        return guarded
