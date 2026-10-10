"""Order routes: parse, call one controller method, render."""
from flask import jsonify

from routes.validators import corpo_json, parse_pedido, parse_status


def register(app, controller):
    def criar_pedido():
        usuario_id, itens = parse_pedido(corpo_json())
        resultado = controller.criar(usuario_id, itens)
        return jsonify({"dados": resultado, "sucesso": True,
                        "mensagem": "Pedido criado com sucesso"}), 201

    def listar_pedidos_usuario(usuario_id):
        return jsonify({"dados": controller.listar_por_usuario(usuario_id), "sucesso": True}), 200

    def listar_todos_pedidos():
        return jsonify({"dados": controller.listar_todos(), "sucesso": True}), 200

    def atualizar_status_pedido(pedido_id):
        controller.atualizar_status(pedido_id, parse_status(corpo_json(nao_vazio=False)))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    app.add_url_rule("/pedidos", "criar_pedido", criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", listar_todos_pedidos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                     listar_pedidos_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                     atualizar_status_pedido, methods=["PUT"])
