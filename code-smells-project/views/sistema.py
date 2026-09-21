"""Rotas de índice, saúde e administração."""
from flask import jsonify, request

from config.configuracao import VERSAO_API

# O campo `secret_key` faz parte do formato atual de /health; removê-lo é mudança de
# contrato (PROPOSED, NOT APPLIED). O segredo em si nunca é devolvido.
SEGREDO_OCULTO = "********"


def registrar(app, saude, administracao, configuracao):
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
        contagens = saude.contagens()
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": contagens.produtos,
                "usuarios": contagens.usuarios,
                "pedidos": contagens.pedidos,
            },
            "versao": VERSAO_API,
            "ambiente": configuracao.ambiente,
            "db_path": configuracao.caminho_banco,
            "debug": configuracao.debug,
            "secret_key": SEGREDO_OCULTO,
        }), 200

    def reset_database():
        administracao.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query():
        resultado = administracao.executar_sql(request.get_json(silent=True))
        if resultado is None:
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
        return jsonify({"dados": resultado, "sucesso": True}), 200

    app.add_url_rule("/", "index", index, methods=["GET"])
    app.add_url_rule("/health", "health_check", health_check, methods=["GET"])
    app.add_url_rule("/admin/reset-db", "reset_database", reset_database, methods=["POST"])
    app.add_url_rule("/admin/query", "executar_query", executar_query, methods=["POST"])
