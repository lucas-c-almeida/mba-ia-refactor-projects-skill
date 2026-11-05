"""The error boundary: one mapping from the domain taxonomy to HTTP, registered once.

Routing errors (404/405) keep Flask's own answer. Anything unexpected is logged in full
and answered with a generic message: no exception text, path or trace leaves the process.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.erros import ErroDeRegraDeNegocio, ErroDeValidacao

logger = logging.getLogger(__name__)


def registrar_tratamento_de_erros(app) -> None:
    @app.errorhandler(ErroDeValidacao)
    def entrada_invalida(erro):
        return jsonify({"erro": erro.mensagem}), 400

    @app.errorhandler(ErroDeRegraDeNegocio)
    def regra_violada(erro):
        return jsonify({"erro": erro.mensagem, "sucesso": False}), 400

    @app.errorhandler(Exception)
    def inesperado(erro):
        if isinstance(erro, HTTPException):
            return erro
        logger.exception("unhandled error")
        return jsonify({"erro": "Erro interno do servidor"}), 500
