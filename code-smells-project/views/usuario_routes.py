from flask import Blueprint, jsonify

from models.errors import ValidationError
from views.requisicao import corpo_json, corpo_objeto, texto


def criar_blueprint_usuarios(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.get("/usuarios")
    def listar_usuarios():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    @bp.get("/usuarios/<int:usuario_id>")
    def obter_usuario(usuario_id):
        return jsonify({"dados": controller.obter(usuario_id), "sucesso": True}), 200

    @bp.post("/usuarios")
    def criar_usuario():
        dados = corpo_json()
        if not isinstance(dados, dict) or not dados:
            raise ValidationError("Dados inválidos")
        nome, email, senha = texto(dados, "nome"), texto(dados, "email"), texto(dados, "senha")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        usuario_id = controller.criar(nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @bp.post("/login")
    def login():
        dados = corpo_objeto()
        email, senha = texto(dados, "email"), texto(dados, "senha")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        usuario = controller.autenticar(email, senha)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    return bp
