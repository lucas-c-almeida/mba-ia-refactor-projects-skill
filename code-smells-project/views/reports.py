"""Management report route, guarded by the operator credential."""
from flask import jsonify

from middlewares.operator_guard import require_operator


def register(app, controller, operator_token):
    @app.get("/relatorios/vendas")
    @require_operator(operator_token)
    def relatorio_vendas():
        return jsonify({"dados": controller.sales(), "sucesso": True}), 200
