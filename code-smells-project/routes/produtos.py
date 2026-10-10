"""Product routes: parse, call one controller method, render."""
from flask import jsonify, request

from routes.validators import corpo_json, parse_busca, parse_produto


def register(app, controller):
    def listar_produtos():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    def buscar_produtos():
        termo, categoria, preco_min, preco_max = parse_busca(request.args)
        resultados = controller.pesquisar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def buscar_produto(produto_id):
        return jsonify({"dados": controller.buscar(produto_id), "sucesso": True}), 200

    def criar_produto():
        produto_id = controller.criar(**parse_produto(corpo_json()))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True,
                        "mensagem": "Produto criado"}), 201

    def atualizar_produto(produto_id):
        # A missing product is answered before the body is looked at, as it always was.
        controller.exigir_existente(produto_id)
        controller.atualizar(produto_id, **parse_produto(corpo_json()))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar_produto(produto_id):
        controller.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    app.add_url_rule("/produtos", "listar_produtos", listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", buscar_produto,
                     methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", atualizar_produto,
                     methods=["PUT"])
    app.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", deletar_produto,
                     methods=["DELETE"])
