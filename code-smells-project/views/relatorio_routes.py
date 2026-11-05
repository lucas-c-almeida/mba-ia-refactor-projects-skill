from flask import jsonify


def registrar_rotas_relatorio(app, controller, exigir_operador) -> None:
    @exigir_operador
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_vendas, methods=["GET"])
