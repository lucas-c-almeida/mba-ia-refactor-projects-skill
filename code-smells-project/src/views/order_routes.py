"""Order routes — parse -> call -> render."""
from flask import jsonify, request


def register(app, order_controller) -> None:
    @app.route("/pedidos", methods=["POST"])
    def criar_pedido():
        resultado = order_controller.criar(request.get_json())
        return (
            jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}),
            201,
        )

    @app.route("/pedidos", methods=["GET"])
    def listar_todos_pedidos():
        pedidos = order_controller.listar_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @app.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
    def listar_pedidos_usuario(usuario_id):
        pedidos = order_controller.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @app.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
    def atualizar_status_pedido(pedido_id):
        order_controller.atualizar_status(pedido_id, request.get_json())
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
