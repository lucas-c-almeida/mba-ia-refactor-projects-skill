"""User and sign-in routes: parse → call the controller → render."""
from flask import Blueprint, jsonify

from routes import presenters
from routes.validation import boolean, json_object, pick, string, string_or_null

CREATE_USER_FIELDS = {
    'name': (string_or_null, 'Nome inválido'),
    'email': (string_or_null, 'Email inválido'),
    'password': (string_or_null, 'Senha inválida'),
    'role': (string, 'Role inválido'),
}

UPDATE_USER_FIELDS = {
    'name': (string, 'Nome inválido'),
    'email': (string, 'Email inválido'),
    'password': (string, 'Senha inválida'),
    'role': (string, 'Role inválido'),
    'active': (boolean, 'Valor de active inválido'),
}


def create_user_blueprint(controller, operator_guard):
    bp = Blueprint('users', __name__)

    @bp.route('/users', methods=['GET'])
    def list_users():
        return jsonify([presenters.user_listing(*row) for row in controller.list_users()]), 200

    @bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(presenters.user_with_tasks(*controller.get_user(user_id))), 200

    @bp.route('/users', methods=['POST'])
    def create_user():
        fields = pick(json_object(), CREATE_USER_FIELDS)
        user = controller.create_user(fields.get('name'), fields.get('email'),
                                      fields.get('password'), fields.get('role'))
        return jsonify(user.to_dict()), 201

    @bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = controller.require_user(user_id)
        fields = pick(json_object(), UPDATE_USER_FIELDS)
        updated = controller.update_user(user, fields, operator_guard.is_operator())
        return jsonify(updated.to_dict()), 200

    @bp.route('/users/<int:user_id>', methods=['DELETE'])
    @operator_guard.require
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify([presenters.user_task_item(*row)
                        for row in controller.user_tasks(user_id)]), 200

    @bp.route('/login', methods=['POST'])
    def login():
        data = json_object()
        user, token = controller.login(data.get('email'), data.get('password'))
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': token,
        }), 200

    return bp
