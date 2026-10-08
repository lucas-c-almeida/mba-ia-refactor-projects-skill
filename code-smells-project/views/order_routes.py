"""Order routes: parse, call one controller method, render."""

from flask import Blueprint, jsonify

from views.helpers import json_body


def create_order_blueprint(controller):
    blueprint = Blueprint("orders", __name__)

    @blueprint.route("/pedidos", methods=["POST"])
    def create_order():
        result = controller.create_order(json_body())
        return jsonify({"dados": result, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @blueprint.route("/pedidos", methods=["GET"])
    def list_orders():
        return jsonify({"dados": controller.list_orders(), "sucesso": True}), 200

    @blueprint.route("/pedidos/usuario/<int:user_id>", methods=["GET"])
    def list_user_orders(user_id):
        return jsonify({"dados": controller.list_orders_for_user(user_id), "sucesso": True}), 200

    @blueprint.route("/pedidos/<int:order_id>/status", methods=["PUT"])
    def update_order_status(order_id):
        controller.update_status(order_id, json_body())
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    return blueprint
