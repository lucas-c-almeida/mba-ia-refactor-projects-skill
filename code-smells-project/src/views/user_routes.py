"""User and login routes — parse -> call -> render."""
from flask import jsonify, request


def register(app, user_controller) -> None:
    @app.route("/usuarios", methods=["GET"])
    def listar_usuarios():
        usuarios = user_controller.listar()
        return jsonify({"dados": usuarios, "sucesso": True}), 200

    @app.route("/usuarios/<int:usuario_id>", methods=["GET"])
    def buscar_usuario(usuario_id):
        usuario = user_controller.buscar(usuario_id)
        return jsonify({"dados": usuario, "sucesso": True}), 200

    @app.route("/usuarios", methods=["POST"])
    def criar_usuario():
        usuario_id = user_controller.criar(request.get_json())
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @app.route("/login", methods=["POST"])
    def login():
        usuario = user_controller.login(request.get_json())
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
