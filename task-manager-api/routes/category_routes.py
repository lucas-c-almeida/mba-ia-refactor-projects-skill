"""Category routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes import presenters


def create_category_blueprint(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.route('/categories', methods=['GET'])
    def get_categories():
        rows = controller.list_categories()
        return jsonify([presenters.category_list_item(category, count)
                        for category, count in rows]), 200

    @category_bp.route('/categories', methods=['POST'])
    def create_category():
        category = controller.create_category(request.get_json())
        return jsonify(presenters.category(category)), 201

    @category_bp.route('/categories/<int:category_id>', methods=['PUT'])
    def update_category(category_id):
        category = controller.update_category(category_id, request.get_json())
        return jsonify(presenters.category(category)), 200

    @category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
    def delete_category(category_id):
        controller.delete_category(category_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return category_bp
