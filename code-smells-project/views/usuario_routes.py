"""User and login routes."""
from flask import Blueprint, jsonify

from views import schemas, serializers


def criar_blueprint(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.get("/usuarios")
    def listar_usuarios():
        return jsonify({"dados": serializers.usuarios(controller.listar()), "sucesso": True}), 200

    @bp.get("/usuarios/<int:usuario_id>")
    def buscar_usuario(usuario_id):
        usuario = controller.obter(usuario_id)
        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": serializers.usuario(usuario), "sucesso": True}), 200

    @bp.post("/usuarios")
    def criar_usuario():
        valores = schemas.usuario(schemas.corpo_obrigatorio())
        usuario_id = controller.criar(**valores)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @bp.post("/login")
    def login():
        email, senha = schemas.credenciais(schemas.corpo_json())
        usuario = controller.autenticar(email, senha)
        return jsonify({
            "dados": serializers.usuario_autenticado(usuario),
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200

    return bp
