"""Index and health routes."""
from flask import jsonify

from config.settings import APP_VERSION


def register(app, controller):
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

    def health_check():
        return jsonify(controller.verificar()), 200

    app.add_url_rule("/", "index", index, methods=["GET"])
    app.add_url_rule("/health", "health_check", health_check, methods=["GET"])
