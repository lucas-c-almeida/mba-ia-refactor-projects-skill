"""User routes: parse, call one controller method, render."""
from flask import Blueprint, jsonify, request

from middlewares.operator_guard import operator_required


def create_user_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify(controller.list_users()), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        return jsonify(controller.create_user(request.get_json())), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json)), 200

    # Privileged: removes an account and its tasks on the caller's say-so (AP-04, RP-04).
    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    @operator_required
    def delete_user(user_id):
        return jsonify(controller.delete_user(user_id)), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify(controller.user_tasks(user_id)), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        return jsonify(controller.login(request.get_json())), 200

    return user_bp
