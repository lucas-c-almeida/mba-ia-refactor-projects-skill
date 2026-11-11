"""The error boundary: one mapping from the domain taxonomy to responses.

Domain errors keep the status and body shape the API has always produced. Anything
unexpected is logged in full here and answered with a generic message: no exception
text, SQL fragment or stack trace reaches the client.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Erro interno do servidor"


def register(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        body = {"erro": error.message}
        if error.with_success_flag:
            body["sucesso"] = False
        return jsonify(body), error.status

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return error                       # routing errors (404/405) keep the framework answer
        logger.exception("unhandled error")
        return jsonify({"erro": INTERNAL_ERROR_MESSAGE}), 500
