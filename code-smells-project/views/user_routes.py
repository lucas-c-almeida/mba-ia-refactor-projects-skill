"""User routes: parse, call one controller method, render."""

from flask import Blueprint, jsonify

from views.helpers import json_body, present_user


def create_user_blueprint(controller):
    blueprint = Blueprint("users", __name__)

    @blueprint.route("/usuarios", methods=["GET"])
    def list_users():
        users = [present_user(user) for user in controller.list_users()]
        return jsonify({"dados": users, "sucesso": True}), 200

    @blueprint.route("/usuarios/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        return jsonify({"dados": present_user(controller.get_user(user_id)), "sucesso": True}), 200

    @blueprint.route("/usuarios", methods=["POST"])
    def create_user():
        user_id = controller.create_user(json_body())
        return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201

    @blueprint.route("/login", methods=["POST"])
    def login():
        user = controller.login(json_body())
        return jsonify({"dados": user, "sucesso": True, "mensagem": "Login OK"}), 200

    return blueprint
