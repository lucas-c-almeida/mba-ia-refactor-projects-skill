"""User and authentication routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes import presenters


def create_user_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        rows = controller.list_users()
        return jsonify([presenters.user_list_item(user, count) for user, count in rows]), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user, tasks = controller.get_user(user_id)
        data = presenters.user(user)
        data['tasks'] = [presenters.task(task) for task in tasks]
        return jsonify(data), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        user = controller.create_user(request.get_json())
        return jsonify(presenters.user(user)), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = controller.update_user(user_id, request.get_json())
        return jsonify(presenters.user(user)), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        rows = controller.list_user_tasks(user_id)
        return jsonify([presenters.user_task_item(task, overdue) for task, overdue in rows]), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        user, token = controller.login(request.get_json())
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': presenters.user(user),
            'token': token,
        }), 200

    return user_bp
