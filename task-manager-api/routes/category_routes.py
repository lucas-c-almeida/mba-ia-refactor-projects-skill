"""Category routes: parse → call the controller → render."""
from flask import Blueprint, jsonify

from routes import presenters
from routes.validation import json_object, pick, string, string_or_null

CREATE_CATEGORY_FIELDS = {
    'name': (string_or_null, 'Nome inválido'),
    'description': (string_or_null, 'Descrição inválida'),
    'color': (string_or_null, 'Cor inválida'),
}

UPDATE_CATEGORY_FIELDS = {
    'name': (string, 'Nome inválido'),
    'description': (string_or_null, 'Descrição inválida'),
    'color': (string_or_null, 'Cor inválida'),
}


def create_category_blueprint(controller):
    bp = Blueprint('categories', __name__)

    @bp.route('/categories', methods=['GET'])
    def list_categories():
        return jsonify([presenters.category_with_count(*row)
                        for row in controller.list_categories()]), 200

    @bp.route('/categories', methods=['POST'])
    def create_category():
        category = controller.create_category(pick(json_object(), CREATE_CATEGORY_FIELDS))
        return jsonify(category.to_dict()), 201

    @bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        category = controller.require_category(cat_id)
        fields = pick(json_object(allow_empty=True), UPDATE_CATEGORY_FIELDS)
        return jsonify(controller.update_category(category, fields).to_dict()), 200

    @bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        controller.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return bp
