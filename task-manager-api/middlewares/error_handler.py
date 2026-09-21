"""The single error boundary (RP-09): domain errors -> the API's existing {"error": ...} shape."""
import logging

from flask import jsonify

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
    # Anything unexpected is left to the framework's default handler, which logs the traceback
    # and returns a generic 500 page with no internals (debug is off unless APP_DEBUG opts in).
