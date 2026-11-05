from flask import jsonify

from views.entrada import corpo_json, id_no_intervalo, ler_credenciais, ler_novo_usuario


def registrar_rotas_usuario(app, controller) -> None:
    def listar_usuarios():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    def obter_usuario(usuario_id):
        usuario = controller.obter(usuario_id) if id_no_intervalo(usuario_id) else None
        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar_usuario():
        usuario_id = controller.criar(**ler_novo_usuario(corpo_json()))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login():
        usuario = controller.autenticar(**ler_credenciais(corpo_json()))
        if usuario is None:
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    app.add_url_rule("/usuarios", "listar_usuarios", listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", obter_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", login, methods=["POST"])
