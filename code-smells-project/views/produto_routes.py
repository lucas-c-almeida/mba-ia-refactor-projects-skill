from flask import Blueprint, jsonify, request

from views.requisicao import corpo_json, numero_opcional


def criar_blueprint_produtos(controller):
    bp = Blueprint("produtos", __name__)

    @bp.get("/produtos")
    def listar_produtos():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    @bp.get("/produtos/busca")
    def buscar_produtos():
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = numero_opcional("preco_min")
        preco_max = numero_opcional("preco_max")
        resultados = controller.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @bp.get("/produtos/<int:produto_id>")
    def obter_produto(produto_id):
        return jsonify({"dados": controller.obter(produto_id), "sucesso": True}), 200

    @bp.post("/produtos")
    def criar_produto():
        produto_id = controller.criar(corpo_json())
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @bp.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        controller.atualizar(produto_id, corpo_json())
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @bp.delete("/produtos/<int:produto_id>")
    def remover_produto(produto_id):
        controller.remover(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return bp
