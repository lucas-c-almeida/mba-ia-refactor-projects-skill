"""Rotas de produto: interpretar a requisição → chamar o controller → renderizar."""
from flask import jsonify, request

from models.erros import ErroValidacao
from views import serializadores


def _numero_opcional(nome):
    """Parâmetro de consulta numérico opcional; texto não numérico é erro do cliente."""
    bruto = request.args.get(nome, None)
    if not bruto:
        return bruto
    try:
        return float(bruto)
    except ValueError:
        raise ErroValidacao(f"Parâmetro {nome} deve ser numérico") from None


def registrar(app, controller):
    def listar_produtos():
        produtos = controller.listar()
        return jsonify({"dados": [serializadores.produto(p) for p in produtos], "sucesso": True}), 200

    def buscar_produtos():
        resultados = controller.pesquisar(
            request.args.get("q", ""),
            request.args.get("categoria", None),
            _numero_opcional("preco_min"),
            _numero_opcional("preco_max"),
        )
        return jsonify({
            "dados": [serializadores.produto(p) for p in resultados],
            "total": len(resultados),
            "sucesso": True,
        }), 200

    def buscar_produto(produto_id):
        produto = controller.buscar(produto_id)
        if produto is None:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": serializadores.produto(produto), "sucesso": True}), 200

    def criar_produto():
        produto_id = controller.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar_produto(produto_id):
        controller.atualizar(produto_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar_produto(produto_id):
        controller.remover(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    app.add_url_rule("/produtos", "listar_produtos", listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", atualizar_produto, methods=["PUT"])
    app.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", deletar_produto, methods=["DELETE"])
