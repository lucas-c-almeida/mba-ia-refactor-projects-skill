from flask import Blueprint, jsonify, request


def build_category_blueprint(controller):
    """Delivery layer for categories: parse, call one controller method, render."""
    category_bp = Blueprint('categories', __name__)

    @category_bp.route('/categories', methods=['GET'])
    def get_categories():
        return jsonify(controller.list_categories()), 200

    @category_bp.route('/categories', methods=['POST'])
    def create_category():
        category = controller.create_category(request.get_json())
        return jsonify(category.to_dict()), 201

    @category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        category = controller.find_category(cat_id)
        category = controller.update_category(category, request.get_json())
        return jsonify(category.to_dict()), 200

    @category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        return jsonify(controller.delete_category(cat_id)), 200

    return category_bp
