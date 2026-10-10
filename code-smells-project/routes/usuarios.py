"""User routes: parse, call one controller method, render."""
from flask import jsonify

from routes.validators import corpo_json, parse_login, parse_usuario


def register(app, controller):
    def listar_usuarios():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    def buscar_usuario(usuario_id):
        return jsonify({"dados": controller.buscar(usuario_id), "sucesso": True}), 200

    def criar_usuario():
        usuario_id = controller.criar(*parse_usuario(corpo_json()))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login():
        usuario = controller.login(*parse_login(corpo_json(nao_vazio=False)))
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    app.add_url_rule("/usuarios", "listar_usuarios", listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", buscar_usuario,
                     methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", login, methods=["POST"])
