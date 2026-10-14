import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """The single place where errors become responses."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err  # routing and parsing errors keep the framework's own response
        logger.exception('Unhandled error')  # full context stays in the log
        return jsonify({'error': 'Erro interno'}), 500
