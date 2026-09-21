"""The single error boundary: domain errors -> responses, in one place."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException, InternalServerError

from models.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        if err.status >= 500:
            logger.error('%s: %s', type(err).__name__, err.message)
        else:
            logger.info('%s: %s', type(err).__name__, err.message)
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            # Framework-level responses (404 for unknown routes, 415 for a non-JSON body...)
            # keep their standard rendering.
            return err
        # Unexpected: full context goes to the log. The response keeps the framework's
        # standard 500 rendering, as before (changing it is recorded as proposed, not applied).
        logger.exception('unhandled error')
        return InternalServerError()
