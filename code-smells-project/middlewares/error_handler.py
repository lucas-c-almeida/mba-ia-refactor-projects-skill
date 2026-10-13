"""The single error boundary: maps the domain error taxonomy to protocol responses."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import (
    AppError,
    ForbiddenError,
    NotFoundError,
    ServicoIndisponivelError,
    UnauthorizedError,
    ValidationError,
)

logger = logging.getLogger(__name__)

_STATUS = {
    ValidationError: 400,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
}


def registrar_tratamento_de_erros(app):
    @app.errorhandler(AppError)
    def tratar_erro_de_dominio(erro):
        corpo = {"erro": erro.mensagem}
        if erro.sucesso_false:
            corpo["sucesso"] = False
        return jsonify(corpo), _STATUS.get(type(erro), 400)

    @app.errorhandler(ServicoIndisponivelError)
    def tratar_servico_indisponivel(erro):
        # The health body has its own failure shape.
        return jsonify({"status": "erro", "detalhes": erro.mensagem}), 500

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        if isinstance(erro, HTTPException):
            # The framework's own answer (unknown route, wrong method, ...) is kept as is.
            return erro
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
