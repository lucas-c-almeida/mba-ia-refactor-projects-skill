from flask import jsonify

from controllers.sistema_controller import VERSAO_API


def registrar_rotas_sistema(app, controller) -> None:
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": VERSAO_API,
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
        saudavel, dados = controller.saude()
        return jsonify(dados), 200 if saudavel else 500

    app.add_url_rule("/", "index", index, methods=["GET"])
    app.add_url_rule("/health", "health_check", health_check, methods=["GET"])
