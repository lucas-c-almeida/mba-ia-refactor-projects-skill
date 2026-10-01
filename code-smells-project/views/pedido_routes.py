from flask import Blueprint, jsonify

from models.errors import ValidationError
from views.requisicao import corpo_json, corpo_objeto


def criar_blueprint_pedidos(controller):
    bp = Blueprint("pedidos", __name__)

    @bp.post("/pedidos")
    def criar_pedido():
        dados = corpo_json()
        if not isinstance(dados, dict) or not dados:
            raise ValidationError("Dados inválidos")
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        resultado = controller.criar(usuario_id, itens)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @bp.get("/pedidos")
    def listar_todos_pedidos():
        return jsonify({"dados": controller.listar_todos(), "sucesso": True}), 200

    @bp.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        return jsonify({"dados": controller.listar_por_usuario(usuario_id), "sucesso": True}), 200

    @bp.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        novo_status = corpo_objeto().get("status", "")
        controller.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    return bp
