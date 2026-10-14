from flask import Blueprint, jsonify, request

from middlewares.operator_guard import require_operator


def build_user_blueprint(controller):
    bp = Blueprint('users', __name__)

    @bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify(controller.list_users()), 200

    @bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @bp.route('/users', methods=['POST'])
    def create_user():
        return jsonify(controller.create_user(request.get_json())), 201

    @bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json())), 200

    @bp.route('/users/<int:user_id>', methods=['DELETE'])
    @require_operator
    def delete_user(user_id):
        return jsonify(controller.delete_user(user_id)), 200

    @bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify(controller.list_user_tasks(user_id)), 200

    @bp.route('/login', methods=['POST'])
    def login():
        return jsonify(controller.login(request.get_json())), 200

    return bp
