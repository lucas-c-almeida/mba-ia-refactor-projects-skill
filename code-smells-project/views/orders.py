"""Order routes: parse, call one controller method, render."""
from flask import jsonify, request

from models.money import from_cents
from views.schemas import bounded_id, parse_order, parse_status
from views.serializers import order_out


def register(app, controller):
    @app.post("/pedidos")
    def criar_pedido():
        user_id, items = parse_order(request.get_json(silent=True))
        order_id, total_cents = controller.place(user_id, items)
        return jsonify({
            "dados": {"pedido_id": order_id, "total": from_cents(total_cents)},
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    @app.get("/pedidos")
    def listar_todos_pedidos():
        return jsonify({"dados": [order_out(o) for o in controller.list_all()], "sucesso": True}), 200

    @app.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        orders = controller.list_for_user(bounded_id(usuario_id))
        return jsonify({"dados": [order_out(o) for o in orders], "sucesso": True}), 200

    @app.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        status = parse_status(request.get_json(silent=True))
        controller.change_status(bounded_id(pedido_id), status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
