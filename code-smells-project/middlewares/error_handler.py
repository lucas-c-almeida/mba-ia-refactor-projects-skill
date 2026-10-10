"""The error boundary: one mapping from the error taxonomy to responses.

Errors the application raises on purpose keep the status and body shape their handlers always
used. Anything unexpected is logged in full by the framework and answered with a generic message:
the exception text never reaches the client. The framework's own answers (unknown route, wrong
method) are left to its default pages.
"""
from flask import jsonify

from errors import AppError

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def tratar_erro_da_aplicacao(erro):
        return jsonify(erro.body()), erro.status

    @app.errorhandler(500)
    def tratar_erro_inesperado(_erro):
        # Flask has already logged the traceback of the original exception at this point.
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
