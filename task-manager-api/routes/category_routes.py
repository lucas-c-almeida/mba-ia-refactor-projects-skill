from flask import Blueprint, jsonify, request

from routes import serializers


def create_category_blueprint(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.route('/categories', methods=['GET'])
    def get_categories():
        return jsonify([serializers.category_with_count(c, n)
                        for c, n in controller.list_categories()]), 200

    @category_bp.route('/categories', methods=['POST'])
    def create_category():
        return jsonify(serializers.category(controller.create(request.get_json()))), 201

    @category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        controller.get_category(cat_id)  # 404 before the body is read, as it always was
        return jsonify(serializers.category(controller.update(cat_id, request.get_json()))), 200

    @category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        controller.delete(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return category_bp
