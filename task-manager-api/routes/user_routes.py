from flask import Blueprint, jsonify, request

from middlewares.guards import require_operator
from routes import serializers


def create_user_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify([serializers.user_list_item(u, n) for u, n in controller.list_users()]), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user, tasks = controller.get_user(user_id)
        return jsonify(serializers.user_with_tasks(user, tasks)), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        return jsonify(serializers.user(controller.create(request.get_json()))), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        controller.get_user(user_id)  # 404 before the body is read, as it always was
        return jsonify(serializers.user(controller.update(user_id, request.get_json()))), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    @require_operator  # privileged: removes an account and its tasks by request id
    def delete_user(user_id):
        controller.delete(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify([serializers.user_task_item(t) for t in controller.user_tasks(user_id)]), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        user = controller.login(request.get_json())
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': serializers.user(user),
            'token': 'fake-jwt-token-' + str(user.id),
        }), 200

    return user_bp
