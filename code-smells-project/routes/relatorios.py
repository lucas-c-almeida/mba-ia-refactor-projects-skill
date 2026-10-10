"""Report routes. The sales report is an operator-only aggregate over every customer."""
from flask import jsonify


def register(app, controller, exigir_operador):
    @exigir_operador
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_vendas, methods=["GET"])
