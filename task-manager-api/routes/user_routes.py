from flask import Blueprint, jsonify, request

from routes import serializers, validation


def create_user_blueprint(controller, operator_guard):
    bp = Blueprint('users', __name__)

    @bp.route('/users', methods=['GET'])
    def get_users():
        rows = controller.list_users()
        return jsonify([serializers.user_list_item(user, count) for user, count in rows]), 200

    @bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user, tasks = controller.get_user(user_id)
        data = serializers.user(user)
        data['tasks'] = [serializers.task(task) for task in tasks]
        return jsonify(data), 200

    @bp.route('/users', methods=['POST'])
    def create_user():
        fields = validation.parse_user_create(request.get_json())
        user = controller.create_user(**fields)
        return jsonify(serializers.user(user)), 201

    @bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        controller.require_user(user_id)
        changes = validation.parse_user_update(request.get_json())
        user = controller.update_user(user_id, changes, operator_guard.is_authorized())
        return jsonify(serializers.user(user)), 200

    @bp.route('/users/<int:user_id>', methods=['DELETE'])
    @operator_guard.require
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        rows = controller.user_tasks(user_id)
        return jsonify([serializers.user_task_item(task, overdue) for task, overdue in rows]), 200

    @bp.route('/login', methods=['POST'])
    def login():
        email, password = validation.parse_login(request.get_json())
        user, token = controller.login(email, password)
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': serializers.user(user),
            'token': token,
        }), 200

    return bp
