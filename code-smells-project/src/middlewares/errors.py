"""
One centralized error boundary (fixes AP-09). Every route used to repeat
`try/except Exception as e: return jsonify({"erro": str(e)}), 500`, catching
everything the same way and leaking raw exception text. Handlers now let domain
errors propagate; this is the only place that maps them to a response, and the
only place that decides what an *unexpected* exception looks like to a caller.

Status codes, and the presence or absence of the `sucesso` key, match what each
situation already returned before this refactor (see src/models/errors.py).
"""
from flask import jsonify

from src.models.errors import (
    ConflictError,
    NotAuthenticatedError,
    NotFoundError,
    ValidationError,
)


def _body(err) -> dict:
    body = {"erro": err.message}
    if err.sucesso is not None:
        body["sucesso"] = err.sucesso
    return body


def register_error_handlers(app, logger) -> None:
    @app.errorhandler(ValidationError)
    def _handle_validation(err):
        return jsonify(_body(err)), 400

    @app.errorhandler(NotFoundError)
    def _handle_not_found(err):
        return jsonify(_body(err)), 404

    @app.errorhandler(NotAuthenticatedError)
    def _handle_not_authenticated(err):
        return jsonify(_body(err)), 401

    @app.errorhandler(ConflictError)
    def _handle_conflict(err):
        return jsonify(_body(err)), 400

    @app.errorhandler(Exception)
    def _handle_unexpected(err):
        # Full context internally; a safe, fixed message externally. The original
        # returned str(e) here, which could include driver text, SQL fragments or
        # file paths (AP-09, compounding with AP-18). This one situation had no
        # "sucesso" key anywhere in the original either.
        logger.exception("unhandled error")
        return jsonify({"erro": "Erro interno"}), 500
