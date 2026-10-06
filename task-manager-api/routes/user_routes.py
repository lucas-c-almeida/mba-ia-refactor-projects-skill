"""User and login routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes import presenters


def create_user_blueprint(controller, clock):
    bp = Blueprint('users', __name__)

    @bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify([presenters.user_list_item(user, count)
                        for user, count in controller.list_users()]), 200

    @bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user, tasks = controller.get_user(user_id)
        data = presenters.user_dict(user)
        data['tasks'] = [presenters.task_dict(t) for t in tasks]
        return jsonify(data), 200

    @bp.route('/users', methods=['POST'])
    def create_user():
        user = controller.create(request.get_json())
        return jsonify(presenters.user_dict(user)), 201

    @bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = controller.update(user_id, request.get_json())
        return jsonify(presenters.user_dict(user)), 200

    @bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        controller.delete(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        now = clock()
        return jsonify([presenters.user_task_item(t, now)
                        for t in controller.user_tasks(user_id)]), 200

    @bp.route('/login', methods=['POST'])
    def login():
        user, token = controller.login(request.get_json())
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': presenters.user_dict(user),
            'token': token,
        }), 200

    return bp
