"""The single error boundary: domain errors in, protocol responses out."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # Protocol-level errors (unknown route, wrong method, unsupported media type)
        # keep the answer the framework already gives them.
        if isinstance(err, HTTPException):
            return err
        # Full context goes to the log; nothing internal goes to the caller.
        logger.exception('Unhandled error')
        return jsonify({'error': INTERNAL_ERROR_MESSAGE}), 500
