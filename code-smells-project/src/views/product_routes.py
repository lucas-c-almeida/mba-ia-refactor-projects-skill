"""
Product routes — parse -> call -> render, nothing else (fixes AP-05 / AP-03: this
used to be where validation and persistence lived, directly in controllers.py).
"""
from flask import jsonify, request

from src.models.errors import ValidationError
from src.validation import parse_preco_opcional


def register(app, product_controller) -> None:
    @app.route("/produtos", methods=["GET"])
    def listar_produtos():
        produtos = product_controller.listar()
        return jsonify({"dados": produtos, "sucesso": True}), 200

    @app.route("/produtos/busca", methods=["GET"])
    def buscar_produtos():
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)

        preco_min, erro = parse_preco_opcional(request.args.get("preco_min"))
        if erro:
            raise ValidationError(erro)
        preco_max, erro = parse_preco_opcional(request.args.get("preco_max"))
        if erro:
            raise ValidationError(erro)

        resultados = product_controller.buscar_por_filtro(
            termo, categoria, preco_min, preco_max
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @app.route("/produtos/<int:produto_id>", methods=["GET"])
    def buscar_produto(produto_id):
        produto = product_controller.buscar(produto_id)
        return jsonify({"dados": produto, "sucesso": True}), 200

    @app.route("/produtos", methods=["POST"])
    def criar_produto():
        produto_id = product_controller.criar(request.get_json())
        return (
            jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}),
            201,
        )

    @app.route("/produtos/<int:produto_id>", methods=["PUT"])
    def atualizar_produto(produto_id):
        product_controller.atualizar(produto_id, request.get_json())
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @app.route("/produtos/<int:produto_id>", methods=["DELETE"])
    def deletar_produto(produto_id):
        product_controller.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
