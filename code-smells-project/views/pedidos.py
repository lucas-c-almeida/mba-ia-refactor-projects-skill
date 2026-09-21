"""Rotas de pedido e de relatório de vendas."""
from flask import jsonify, request

from views import serializadores


def registrar(app, pedidos, relatorios):
    def criar_pedido():
        pedido_id, total = pedidos.criar(request.get_json(silent=True))
        return jsonify({
            "dados": {"pedido_id": pedido_id, "total": total},
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_todos_pedidos():
        return jsonify({"dados": [serializadores.pedido(p) for p in pedidos.listar()], "sucesso": True}), 200

    def listar_pedidos_usuario(usuario_id):
        encontrados = pedidos.listar(usuario_id)
        return jsonify({"dados": [serializadores.pedido(p) for p in encontrados], "sucesso": True}), 200

    def atualizar_status_pedido(pedido_id):
        pedidos.atualizar_status(pedido_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    def relatorio_vendas():
        return jsonify({"dados": serializadores.resumo_vendas(relatorios.vendas()), "sucesso": True}), 200

    app.add_url_rule("/pedidos", "criar_pedido", criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", listar_todos_pedidos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                     listar_pedidos_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                     atualizar_status_pedido, methods=["PUT"])
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_vendas, methods=["GET"])
