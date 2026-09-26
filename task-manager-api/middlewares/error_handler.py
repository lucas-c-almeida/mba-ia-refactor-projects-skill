"""One centralized error boundary, registered once by the composition root.

Fixes AP-09: every route used to repeat its own try/except/rollback/jsonify block, and
nothing was registered for a truly unexpected exception (so Flask's own debug-mode
handler took over — see AP-18). Both are replaced by this single mapping, which
preserves the status codes and `{"error": "..."}` shape every route already used.
"""
import logging

from flask import jsonify

from database import db
from middlewares.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        if err.status >= 500:
            logger.error("unhandled application error: %s", err.message)
        else:
            logger.warning("%s: %s", err.status, err.message)
        return jsonify({"error": err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # A write that was in flight when an unexpected error happened must not be left
        # half-applied (AP-09: "no transaction boundary and no compensation").
        db.session.rollback()
        logger.exception("unexpected error")
        # Never leak internals (stack trace, driver message, file path) in the response —
        # that is also AP-18/AP-08. Log the full context internally instead.
        return jsonify({"error": "Erro interno"}), 500
