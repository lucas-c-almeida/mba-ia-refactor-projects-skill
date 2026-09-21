"""Product routes: parse -> call the controller -> render."""
from flask import Blueprint, jsonify, request

from models.constants import CATEGORIA_PADRAO
from views import schemas, serializers


def criar_blueprint(controller):
    bp = Blueprint("produtos", __name__)

    @bp.get("/produtos")
    def listar_produtos():
        return jsonify({"dados": serializers.produtos(controller.listar()), "sucesso": True}), 200

    @bp.get("/produtos/busca")
    def buscar_produtos():
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = schemas.filtro_preco("preco_min")
        preco_max = schemas.filtro_preco("preco_max")
        resultados = serializers.produtos(controller.buscar(termo, categoria, preco_min, preco_max))
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @bp.get("/produtos/<int:produto_id>")
    def buscar_produto(produto_id):
        produto = controller.obter(produto_id)
        if produto is None:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": serializers.produto(produto), "sucesso": True}), 200

    @bp.post("/produtos")
    def criar_produto():
        valores = schemas.produto(schemas.corpo_obrigatorio(), CATEGORIA_PADRAO)
        produto_id = controller.criar(**valores)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @bp.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        dados = schemas.corpo_json()
        if not controller.existe(produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        valores = schemas.produto(dados, CATEGORIA_PADRAO)
        controller.atualizar(produto_id, **valores)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @bp.delete("/produtos/<int:produto_id>")
    def deletar_produto(produto_id):
        if not controller.deletar(produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return bp
