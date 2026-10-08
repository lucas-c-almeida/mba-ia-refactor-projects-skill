"""The one place that turns errors into responses.

Domain errors keep the status codes and the `{"erro": ...}` body the endpoints always used; an
unexpected error is logged with its traceback and answered with a generic message, never with the
exception text. The framework's own HTTP errors (404 for an unknown route, 405, ...) are left to
the framework.
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import (
    AccessDeniedError,
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
)

logger = logging.getLogger(__name__)

_STATUS_BY_ERROR = (
    (NotFoundError, 404),
    (ConflictError, 409),
    (AuthenticationError, 401),
    (AccessDeniedError, 403),
    (DomainError, 400),  # validation and business-rule errors
)


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        status = next(code for kind, code in _STATUS_BY_ERROR if isinstance(error, kind))
        body = {"erro": error.message}
        if error.failure_flag:
            body["sucesso"] = False
        return jsonify(body), status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception("unhandled error")
        return jsonify({"erro": "Erro interno do servidor"}), 500
