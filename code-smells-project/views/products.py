"""Product routes: parse, call one controller method, render."""
from flask import jsonify, request

from views.schemas import bounded_id, parse_product, parse_search
from views.serializers import product_out


def register(app, controller):
    @app.get("/produtos")
    def listar_produtos():
        return jsonify({"dados": [product_out(p) for p in controller.list_all()], "sucesso": True}), 200

    @app.get("/produtos/busca")
    def buscar_produtos():
        filters = parse_search(request.args)
        results = controller.search(filters["term"], filters["category"], filters["min_price"], filters["max_price"])
        return jsonify({"dados": [product_out(p) for p in results], "total": len(results), "sucesso": True}), 200

    @app.get("/produtos/<int:product_id>")
    def buscar_produto(product_id):
        product = controller.get(bounded_id(product_id))
        return jsonify({"dados": product_out(product), "sucesso": True}), 200

    @app.post("/produtos")
    def criar_produto():
        product_id = controller.create(parse_product(request.get_json(silent=True)))
        return jsonify({"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @app.put("/produtos/<int:product_id>")
    def atualizar_produto(product_id):
        product_id = bounded_id(product_id)
        controller.ensure_exists(product_id)          # a missing product answers 404 before body checks
        controller.update(product_id, parse_product(request.get_json(silent=True)))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @app.delete("/produtos/<int:product_id>")
    def deletar_produto(product_id):
        controller.delete(bounded_id(product_id))
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
