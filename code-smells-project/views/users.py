"""Account routes: parse, call one controller method, render."""
from flask import jsonify, request

from views.schemas import bounded_id, parse_credentials, parse_new_user
from views.serializers import user_out


def register(app, controller):
    @app.get("/usuarios")
    def listar_usuarios():
        return jsonify({"dados": [user_out(u) for u in controller.list_all()], "sucesso": True}), 200

    @app.get("/usuarios/<int:user_id>")
    def buscar_usuario(user_id):
        return jsonify({"dados": user_out(controller.get(bounded_id(user_id))), "sucesso": True}), 200

    @app.post("/usuarios")
    def criar_usuario():
        nome, email, senha = parse_new_user(request.get_json(silent=True))
        return jsonify({"dados": {"id": controller.register(nome, email, senha)}, "sucesso": True}), 201

    @app.post("/login")
    def login():
        email, senha = parse_credentials(request.get_json(silent=True))
        user = controller.sign_in(email, senha)
        return jsonify({"dados": user, "sucesso": True, "mensagem": "Login OK"}), 200
