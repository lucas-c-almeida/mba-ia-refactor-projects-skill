"""Rotas de usuário e login."""
from flask import jsonify, request

from views import serializadores


def registrar(app, controller):
    def listar_usuarios():
        usuarios = controller.listar()
        return jsonify({"dados": [serializadores.usuario(u) for u in usuarios], "sucesso": True}), 200

    def buscar_usuario(usuario_id):
        usuario = controller.buscar(usuario_id)
        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": serializadores.usuario(usuario), "sucesso": True}), 200

    def criar_usuario():
        usuario_id = controller.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login():
        usuario = controller.autenticar(request.get_json(silent=True))
        if usuario is None:
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
        return jsonify({
            "dados": serializadores.usuario_autenticado(usuario),
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200

    app.add_url_rule("/usuarios", "listar_usuarios", listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", buscar_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", login, methods=["POST"])
