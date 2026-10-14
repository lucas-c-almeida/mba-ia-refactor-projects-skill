"""Index and health routes."""
from flask import Blueprint, jsonify

from models.constants import API_VERSION


def criar_blueprint(health_controller):
    bp = Blueprint("sistema", __name__)

    @bp.route("/", methods=["GET"])
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": API_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    @bp.route("/health", methods=["GET"])
    def health_check():
        return jsonify(health_controller.verificar()), 200

    return bp
