"""Product routes: parse, call one controller method, render."""

from flask import Blueprint, jsonify, request

from views.helpers import json_body, optional_float


def create_product_blueprint(controller):
    blueprint = Blueprint("products", __name__)

    @blueprint.route("/produtos", methods=["GET"])
    def list_products():
        return jsonify({"dados": controller.list_products(), "sucesso": True}), 200

    @blueprint.route("/produtos/busca", methods=["GET"])
    def search_products():
        term = request.args.get("q", "")
        category = request.args.get("categoria", None)
        min_price = optional_float("preco_min")
        max_price = optional_float("preco_max")
        results = controller.search_products(term, category, min_price, max_price)
        return jsonify({"dados": results, "total": len(results), "sucesso": True}), 200

    @blueprint.route("/produtos/<int:product_id>", methods=["GET"])
    def get_product(product_id):
        return jsonify({"dados": controller.get_product(product_id), "sucesso": True}), 200

    @blueprint.route("/produtos", methods=["POST"])
    def create_product():
        product_id = controller.create_product(json_body())
        return jsonify({"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @blueprint.route("/produtos/<int:product_id>", methods=["PUT"])
    def update_product(product_id):
        controller.update_product(product_id, json_body())
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @blueprint.route("/produtos/<int:product_id>", methods=["DELETE"])
    def delete_product(product_id):
        controller.delete_product(product_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return blueprint
