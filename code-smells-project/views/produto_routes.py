from flask import jsonify

from views.entrada import corpo_json, id_no_intervalo, ler_filtros_de_busca, ler_produto


def registrar_rotas_produto(app, controller) -> None:
    def listar_produtos():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    def pesquisar_produtos():
        resultados = controller.pesquisar(**ler_filtros_de_busca())
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def obter_produto(produto_id):
        produto = controller.obter(produto_id) if id_no_intervalo(produto_id) else None
        if produto is None:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": produto, "sucesso": True}), 200

    def criar_produto():
        produto_id = controller.criar(**ler_produto(corpo_json()))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True,
                        "mensagem": "Produto criado"}), 201

    def atualizar_produto(produto_id):
        dados = corpo_json()
        if not id_no_intervalo(produto_id) or not controller.existe(produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        controller.atualizar(produto_id, **ler_produto(dados))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def remover_produto(produto_id):
        if not id_no_intervalo(produto_id) or not controller.remover(produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    # Endpoint names are kept from the original registration; paths and methods are the
    # public contract and are unchanged.
    app.add_url_rule("/produtos", "listar_produtos", listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", pesquisar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", obter_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", atualizar_produto, methods=["PUT"])
    app.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", remover_produto, methods=["DELETE"])
