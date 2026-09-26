"""Delivery layer for users and login: parse -> call the controller -> render (AP-05)."""
from flask import Blueprint, jsonify, request

from controllers.user_controller import UserController
from middlewares.errors import BadRequestError

user_bp = Blueprint('users', __name__)
_controller = UserController()


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(_controller.list_all()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(_controller.get(user_id)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return jsonify(_controller.create(data)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    return jsonify(_controller.update(user_id, data)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    return jsonify(_controller.delete(user_id)), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(_controller.get_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        raise BadRequestError('Dados inválidos')
    result = _controller.authenticate(data.get('email'), data.get('password'))
    return jsonify(result), 200
