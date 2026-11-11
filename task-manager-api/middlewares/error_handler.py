"""The single error boundary (RP-09): domain errors and framework errors become JSON here."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)

INTERNAL_ERROR = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        if error.status >= 500:
            logger.error('%s: %s', type(error).__name__, error.message)
        return jsonify({'error': error.message}), error.status

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        # Replaces the framework's default HTML page; the status code is kept.
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        # Full detail goes to the log only; the client gets a generic body.
        logger.exception('unhandled error')
        return jsonify({'error': INTERNAL_ERROR}), 500
