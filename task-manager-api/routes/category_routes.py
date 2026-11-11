from flask import Blueprint, jsonify, request

from routes import serializers, validation


def create_category_blueprint(controller):
    bp = Blueprint('categories', __name__)

    @bp.route('/categories', methods=['GET'])
    def get_categories():
        rows = controller.list_categories()
        return jsonify([serializers.category_list_item(cat, count) for cat, count in rows]), 200

    @bp.route('/categories', methods=['POST'])
    def create_category():
        fields = validation.parse_category_create(request.get_json())
        category = controller.create_category(**fields)
        return jsonify(serializers.category(category)), 201

    @bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        controller.require_category(cat_id)
        changes = validation.parse_category_update(request.get_json())
        category = controller.update_category(cat_id, changes)
        return jsonify(serializers.category(category)), 200

    @bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        controller.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return bp
