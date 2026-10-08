"""Report routes. The sales report spans every customer, so it is operator-only (closed by default)."""

from flask import Blueprint, jsonify


def create_report_blueprint(controller, operator_required):
    blueprint = Blueprint("reports", __name__)

    @blueprint.route("/relatorios/vendas", methods=["GET"])
    @operator_required
    def sales_report():
        return jsonify({"dados": controller.sales_report(), "sucesso": True}), 200

    return blueprint
