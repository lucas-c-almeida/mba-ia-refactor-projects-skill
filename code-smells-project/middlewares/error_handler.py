"""The single error boundary (AP-09, AP-18).

Domain errors keep the status codes and the {"erro": ...} body the API always produced.
Unexpected errors are logged in full and answered with a generic message: no exception text,
SQL or stack trace ever reaches a client. HTTP errors raised by the framework itself (unknown
route, method not allowed) keep the framework's own response.
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


def registrar_tratamento_de_erros(app):
    @app.errorhandler(AppError)
    def tratar_erro_da_aplicacao(erro):
        return jsonify(erro.body()), erro.status

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        if isinstance(erro, HTTPException):
            return erro
        logger.exception("Erro inesperado")
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
