"""Fronteira única de erros: taxonomia do domínio → resposta HTTP, num só lugar.

Preserva os códigos de status e os formatos de corpo que o contrato já expunha; nunca
devolve mensagem interna, SQL ou stack trace — isso vai só para o log, com um id de
correlação que também segue no cabeçalho da resposta.
"""
import logging
import uuid

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.erros import ErroDependencia, ErroValidacao, NaoEncontrado, RegraNegocioViolada

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"
CABECALHO_CORRELACAO = "X-Correlation-ID"


def registrar(app):
    @app.errorhandler(ErroValidacao)
    def _validacao(erro):
        return jsonify({"erro": str(erro)}), 400

    @app.errorhandler(NaoEncontrado)
    def _nao_encontrado(erro):
        return jsonify({"erro": str(erro)}), 404

    @app.errorhandler(RegraNegocioViolada)
    def _regra_negocio(erro):
        return jsonify({"erro": str(erro), "sucesso": False}), 400

    @app.errorhandler(ErroDependencia)
    def _dependencia(erro):
        # Formato próprio do contrato de /health, a única rota que sinaliza essa falha.
        correlacao = _registrar_falha(erro)
        resposta = jsonify({"status": "erro", "detalhes": str(erro)})
        resposta.headers[CABECALHO_CORRELACAO] = correlacao
        return resposta, 500

    @app.errorhandler(HTTPException)
    def _http(erro):
        return erro          # 404 de rota, 405 de método: a resposta padrão do framework

    @app.errorhandler(Exception)
    def _inesperado(erro):
        correlacao = _registrar_falha(erro)
        resposta = jsonify({"erro": MENSAGEM_ERRO_INTERNO})
        resposta.headers[CABECALHO_CORRELACAO] = correlacao
        return resposta, 500


def _registrar_falha(erro):
    correlacao = uuid.uuid4().hex
    logger.error("falha não tratada [%s]", correlacao, exc_info=erro)
    return correlacao
