"""The single error boundary (RP-09): one mapping from the error taxonomy to HTTP.

Errors the application raises on purpose keep the `{'error': <message>}` body and the status
they always had. Anything unexpected is logged with its traceback and answered with a generic
500 body; the framework's own HTTP errors (404, 405, 415, ...) are left to the framework.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        if error.status >= 500:
            logger.error('%s', error.message, exc_info=error.__cause__)
        return jsonify({'error': error.message}), error.status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception('unhandled error')
        return jsonify({'error': INTERNAL_ERROR_MESSAGE}), 500
