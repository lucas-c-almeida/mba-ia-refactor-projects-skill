"""Product routes: parse, call one controller method, render."""
from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    bp = Blueprint("produtos", __name__)

    @bp.route("/produtos", methods=["GET"])
    def listar_produtos():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    @bp.route("/produtos/busca", methods=["GET"])
    def buscar_produtos():
        resultados = controller.buscar_por_filtros(
            request.args.get("q", ""),
            request.args.get("categoria", None),
            request.args.get("preco_min", None),
            request.args.get("preco_max", None),
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @bp.route("/produtos/<int:produto_id>", methods=["GET"])
    def buscar_produto(produto_id):
        return jsonify({"dados": controller.buscar(produto_id), "sucesso": True}), 200

    @bp.route("/produtos", methods=["POST"])
    def criar_produto():
        produto_id = controller.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @bp.route("/produtos/<int:produto_id>", methods=["PUT"])
    def atualizar_produto(produto_id):
        controller.atualizar(produto_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
    def deletar_produto(produto_id):
        controller.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return bp
