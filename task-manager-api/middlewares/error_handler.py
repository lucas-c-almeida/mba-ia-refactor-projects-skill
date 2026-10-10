"""The single error boundary: domain errors keep the status and body they always had; anything
unexpected is logged in full and answered with a generic message."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': str(err)}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err  # routing/parsing errors keep their framework response and status
        logger.exception('unhandled error')
        return jsonify({'error': 'Erro interno'}), 500
