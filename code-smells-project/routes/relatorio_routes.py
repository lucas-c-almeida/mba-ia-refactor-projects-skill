"""Report routes. The sales report carries financial figures, so it is operator-only."""
from flask import Blueprint, jsonify

from middlewares.operator_guard import exigir_operador


def criar_blueprint(controller, operator_token):
    bp = Blueprint("relatorios", __name__)

    @bp.route("/relatorios/vendas", methods=["GET"])
    @exigir_operador(operator_token)
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    return bp
