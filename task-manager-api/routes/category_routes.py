"""Category routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes.serializers import category_list_item, category_to_dict


def create_category_blueprint(controller):
    bp = Blueprint('categories', __name__)

    @bp.route('/categories', methods=['GET'])
    def list_categories():
        return jsonify([category_list_item(c, count)
                        for c, count in controller.list_categories()]), 200

    @bp.route('/categories', methods=['POST'])
    def create_category():
        category = controller.create_category(request.get_json())
        return jsonify(category_to_dict(category)), 201

    @bp.route('/categories/<int:category_id>', methods=['PUT'])
    def update_category(category_id):
        category = controller.update_category(category_id, request.get_json())
        return jsonify(category_to_dict(category)), 200

    @bp.route('/categories/<int:category_id>', methods=['DELETE'])
    def delete_category(category_id):
        controller.delete_category(category_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return bp
