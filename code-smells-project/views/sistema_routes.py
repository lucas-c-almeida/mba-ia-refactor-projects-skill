from flask import Blueprint, jsonify

from config.settings import APP_VERSION
from models.errors import ValidationError
from views.requisicao import corpo_objeto, texto

ENDPOINTS_PUBLICOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


def criar_blueprint_sistema(controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": APP_VERSION,
            "endpoints": ENDPOINTS_PUBLICOS,
        })

    @bp.get("/health")
    def health_check():
        return jsonify(controller.health()), 200

    @bp.post("/admin/reset-db")
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    def executar_query():
        sql = texto(corpo_objeto(), "sql")
        if not sql:
            raise ValidationError("Query não informada")
        linhas = controller.executar_query(sql)
        if linhas is not None:
            return jsonify({"dados": linhas, "sucesso": True}), 200
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200

    return bp
