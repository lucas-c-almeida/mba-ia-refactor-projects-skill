"""User and login routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes.serializers import task_to_dict, user_list_item, user_task_item, user_to_dict

# Unchanged placeholder token. It is not verified anywhere: a real identity model is recorded
# under PROPOSED, NOT APPLIED (AP-04), because adding one changes the contract for every client.
PLACEHOLDER_TOKEN_PREFIX = 'fake-jwt-token-'


def create_user_blueprint(controller):
    bp = Blueprint('users', __name__)

    @bp.route('/users', methods=['GET'])
    def list_users():
        return jsonify([user_list_item(u, count) for u, count in controller.list_users()]), 200

    @bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user, tasks = controller.get_user(user_id)
        data = user_to_dict(user)
        data['tasks'] = [task_to_dict(t) for t in tasks]
        return jsonify(data), 200

    @bp.route('/users', methods=['POST'])
    def create_user():
        user = controller.create_user(request.get_json())
        return jsonify(user_to_dict(user)), 201

    @bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = controller.update_user(user_id, request.get_json())
        return jsonify(user_to_dict(user)), 200

    @bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify([user_task_item(t, overdue)
                        for t, overdue in controller.user_tasks(user_id)]), 200

    @bp.route('/login', methods=['POST'])
    def login():
        user = controller.login(request.get_json())
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user_to_dict(user),
            'token': PLACEHOLDER_TOKEN_PREFIX + str(user.id),
        }), 200

    return bp
