"""Order and sales-report routes."""
from flask import Blueprint, jsonify

from views import schemas


def criar_blueprint(pedido_controller, relatorio_controller):
    bp = Blueprint("pedidos", __name__)

    @bp.post("/pedidos")
    def criar_pedido():
        usuario_id, itens = schemas.pedido(schemas.corpo_obrigatorio())
        resultado = pedido_controller.criar(usuario_id, itens)
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    @bp.get("/pedidos")
    def listar_todos_pedidos():
        return jsonify({"dados": pedido_controller.listar(), "sucesso": True}), 200

    @bp.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        return jsonify({"dados": pedido_controller.listar_do_usuario(usuario_id), "sucesso": True}), 200

    @bp.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        pedido_controller.atualizar_status(pedido_id, schemas.status(schemas.corpo_json()))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    @bp.get("/relatorios/vendas")
    def relatorio_vendas():
        return jsonify({"dados": relatorio_controller.vendas(), "sucesso": True}), 200

    return bp
