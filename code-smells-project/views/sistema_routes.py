"""Index, health and administrative routes."""
from flask import Blueprint, jsonify

from models.constants import APP_VERSION
from views import schemas


def criar_blueprint(controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
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

    @bp.get("/health")
    def health_check():
        relatorio, detalhe_erro = controller.saude()
        if relatorio is None:
            return jsonify({"status": "erro", "detalhes": detalhe_erro}), 500
        return jsonify(relatorio), 200

    # NOTE: both admin routes are unauthenticated, exactly as before. Protecting or removing them
    # changes the public contract and is listed under PROPOSED, NOT APPLIED.
    @bp.post("/admin/reset-db")
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    def executar_query():
        dados = schemas.corpo_json() or {}
        linhas, eh_select = controller.executar_query(dados.get("sql", ""))
        if eh_select:
            return jsonify({"dados": linhas, "sucesso": True}), 200
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200

    return bp
