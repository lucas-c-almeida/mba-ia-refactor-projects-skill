"""Operator-only guard for privileged operations.

It is a guard on individual operations, not an identity model: it invents no users
and no roles. The credential comes from configuration (OPERATOR_TOKEN); when none is
configured the guarded operation is closed (403).
"""
import hmac
from functools import wraps

from flask import current_app, jsonify, request

OPERATOR_HEADER = 'X-Operator-Token'


def _is_operator():
    expected = current_app.config.get('OPERATOR_TOKEN')
    if not expected:
        return False
    given = request.headers.get(OPERATOR_HEADER, '')
    return hmac.compare_digest(given.encode(), expected.encode())


def require_operator(view):
    @wraps(view)
    def guarded(*args, **kwargs):
        if not _is_operator():
            return jsonify({'error': 'forbidden'}), 403
        return view(*args, **kwargs)

    return guarded
