"""Sales report route."""
from flask import jsonify


def register(app, report_controller) -> None:
    @app.route("/relatorios/vendas", methods=["GET"])
    def relatorio_vendas():
        relatorio = report_controller.vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
