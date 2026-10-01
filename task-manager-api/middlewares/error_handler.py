"""The single error boundary (AP-09, AP-18).

Domain errors keep the status codes and the `{"error": "<message>"}` body the API has always
returned. Anything unexpected is logged with its traceback and answered with a generic body:
no stack trace, source path or driver message ever reaches the client.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import (AppError, AuthenticationError, ConflictError, ForbiddenError,
                           NotFoundError, PersistenceError, ValidationError)

logger = logging.getLogger(__name__)

STATUS_BY_ERROR = {
    ValidationError.code: 400,
    AuthenticationError.code: 401,
    ForbiddenError.code: 403,
    NotFoundError.code: 404,
    ConflictError.code: 409,
    PersistenceError.code: 500,
}
INTERNAL_ERROR_STATUS = 500
INTERNAL_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        status = STATUS_BY_ERROR.get(err.code, INTERNAL_ERROR_STATUS)
        logger.info('%s (%s): %s', err.code, status, err.message)
        return jsonify({'error': err.message}), status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            # Routing and protocol errors (404 for an unknown path, 405, 415, malformed JSON)
            # keep the framework's own answer.
            return err
        logger.exception('unhandled error')
        return jsonify({'error': INTERNAL_ERROR_MESSAGE}), INTERNAL_ERROR_STATUS
