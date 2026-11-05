"""The error boundary (RP-09): one mapping from the domain taxonomy to responses.

The application's own errors keep their status and body (`{"error": <message>}`). Anything
unexpected is logged with a correlation id and answered with a generic 500 body — never a stack
trace or the framework's debugger page. HTTP errors raised by the framework itself (unknown
route, malformed JSON) keep the framework's own answer.
"""
import logging
import uuid

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from models.errors import AppError

logger = logging.getLogger(__name__)

CORRELATION_HEADER = 'X-Correlation-ID'
INTERNAL_ERROR_MESSAGE = 'Erro interno'


def _error_response(message, status, correlation_id):
    response = jsonify({'error': message})
    response.status_code = status
    response.headers[CORRELATION_HEADER] = correlation_id
    return response


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        db.session.rollback()
        correlation_id = uuid.uuid4().hex
        logger.info('%s %s [%s]', type(error).__name__, error.message, correlation_id)
        return _error_response(error.message, error.status, correlation_id)

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return error
        db.session.rollback()
        correlation_id = uuid.uuid4().hex
        logger.exception('unexpected error [%s]', correlation_id)
        return _error_response(INTERNAL_ERROR_MESSAGE, 500, correlation_id)
