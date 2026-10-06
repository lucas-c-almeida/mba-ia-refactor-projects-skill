"""Category routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes import presenters


def create_category_blueprint(controller):
    bp = Blueprint('categories', __name__)

    @bp.route('/categories', methods=['GET'])
    def get_categories():
        result = []
        for category, task_count in controller.list_categories():
            data = presenters.category_dict(category)
            data['task_count'] = task_count
            result.append(data)
        return jsonify(result), 200

    @bp.route('/categories', methods=['POST'])
    def create_category():
        category = controller.create(request.get_json())
        return jsonify(presenters.category_dict(category)), 201

    @bp.route('/categories/<int:category_id>', methods=['PUT'])
    def update_category(category_id):
        category = controller.update(category_id, request.get_json())
        return jsonify(presenters.category_dict(category)), 200

    @bp.route('/categories/<int:category_id>', methods=['DELETE'])
    def delete_category(category_id):
        controller.delete(category_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return bp
