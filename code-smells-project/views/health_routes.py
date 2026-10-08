"""Index and health routes."""

import logging

from flask import Blueprint, jsonify

from models.constants import APP_VERSION, REDACTED

logger = logging.getLogger(__name__)


def create_health_blueprint(controller, settings):
    blueprint = Blueprint("system", __name__)

    @blueprint.route("/", methods=["GET"])
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    @blueprint.route("/health", methods=["GET"])
    def health_check():
        # The health endpoint has its own error shape, so it is the one handler that shapes it.
        try:
            counts = controller.check()
        except Exception:
            logger.exception("health check failed")
            return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": APP_VERSION,
            "ambiente": settings.environment,
            "db_path": settings.db_path,
            "debug": settings.debug,
            "secret_key": REDACTED,
        }), 200

    return blueprint
