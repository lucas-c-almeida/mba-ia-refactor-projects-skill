from flask import Blueprint, jsonify, request


def build_user_blueprint(controller):
    """Delivery layer for users and sign-in: parse, call one controller method, render."""
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify(controller.list_users()), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        user = controller.create_user(request.get_json())
        return jsonify(user.to_dict()), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = controller.find_user(user_id)
        user = controller.update_user(user, request.get_json())
        return jsonify(user.to_dict()), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        return jsonify(controller.delete_user(user_id)), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify(controller.get_user_tasks(user_id)), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        return jsonify(controller.login(request.get_json())), 200

    return user_bp
