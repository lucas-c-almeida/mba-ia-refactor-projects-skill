"""The single error boundary: maps the domain taxonomy to HTTP responses.

Status codes and body shapes are the ones the API already returned:
  ValidationError      -> 400 {"erro"}
  BusinessRuleError    -> 400 {"erro", "sucesso": false}
  AuthenticationError  -> 401 {"erro", "sucesso": false}
  anything unexpected  -> 500 {"erro"} with a generic message; details go to the log only.
Framework HTTP errors (unknown route, wrong method) keep Flask's default responses.
"""
import logging

from flask import g, jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AuthenticationError, BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return jsonify({"erro": str(err)}), 400

    @app.errorhandler(BusinessRuleError)
    def handle_business_rule(err):
        return jsonify({"erro": str(err), "sucesso": False}), 400

    @app.errorhandler(AuthenticationError)
    def handle_authentication(err):
        return jsonify({"erro": str(err), "sucesso": False}), 401

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception("Unhandled error (request_id=%s)", getattr(g, "request_id", "unknown"))
        return jsonify({"erro": "Erro interno do servidor"}), 500
