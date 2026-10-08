"""Operator guard for privileged operations (RP-04).

Privileged operations have no legitimate anonymous caller. The credential comes from
configuration (OPERATOR_TOKEN) and the guard fails closed: with no credential configured, every
request is refused. This is a guard on single operations, not an identity model.
"""
import hmac
from functools import wraps

from flask import current_app, jsonify, request

OPERATOR_HEADER = 'X-Operator-Token'
FORBIDDEN_MESSAGE = 'Acesso restrito a operadores'


def operator_required(view):
    @wraps(view)
    def guarded(*args, **kwargs):
        expected = current_app.config.get('OPERATOR_TOKEN') or ''
        given = request.headers.get(OPERATOR_HEADER, '')
        if not expected or not hmac.compare_digest(given.encode(), expected.encode()):
            return jsonify({'error': FORBIDDEN_MESSAGE}), 403
        return view(*args, **kwargs)

    return guarded
