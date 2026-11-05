from flask import jsonify

from views.entrada import corpo_json, id_no_intervalo, ler_pedido, ler_status


def registrar_rotas_pedido(app, controller) -> None:
    def criar_pedido():
        resultado = controller.criar(**ler_pedido(corpo_json()))
        return jsonify({"dados": resultado, "sucesso": True,
                        "mensagem": "Pedido criado com sucesso"}), 201

    def listar_todos_pedidos():
        return jsonify({"dados": controller.listar_todos(), "sucesso": True}), 200

    def listar_pedidos_usuario(usuario_id):
        pedidos = controller.listar_do_usuario(usuario_id) if id_no_intervalo(usuario_id) else []
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def atualizar_status_pedido(pedido_id):
        status = ler_status(corpo_json())
        if not id_no_intervalo(pedido_id) or not controller.atualizar_status(pedido_id, status):
            return jsonify({"erro": "Pedido não encontrado"}), 404
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    app.add_url_rule("/pedidos", "criar_pedido", criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", listar_todos_pedidos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                     listar_pedidos_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                     atualizar_status_pedido, methods=["PUT"])
