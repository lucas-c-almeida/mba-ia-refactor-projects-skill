"""Task routes: parse → call the controller → render."""
from flask import Blueprint, jsonify, request

from routes import presenters
from routes.validation import (id_or_null, integer, json_object, pick, query_integer, string,
                               string_or_null, tags)
from models.errors import ValidationError

TASK_FIELDS = {
    'title': (string, 'Título inválido'),
    'description': (string_or_null, 'Descrição inválida'),
    'status': (string, 'Status inválido'),
    'priority': (integer, 'Prioridade inválida'),
    'user_id': (id_or_null, 'Usuário inválido'),
    'category_id': (id_or_null, 'Categoria inválida'),
    'due_date': (string_or_null, 'Formato de data inválido'),
    'tags': (tags, 'Tags inválidas'),
}


def create_task_blueprint(controller):
    bp = Blueprint('tasks', __name__)

    @bp.route('/tasks', methods=['GET'])
    def list_tasks():
        return jsonify([presenters.task_listing(*row) for row in controller.list_tasks()]), 200

    @bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        task, overdue = controller.get_task(task_id)
        return jsonify(presenters.task(task, overdue)), 200

    @bp.route('/tasks', methods=['POST'])
    def create_task():
        data = json_object()
        if not data.get('title'):
            raise ValidationError('Título é obrigatório')
        task = controller.create_task(pick(data, TASK_FIELDS))
        return jsonify(presenters.task(task)), 201

    @bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        task = controller.require_task(task_id)
        fields = pick(json_object(), TASK_FIELDS)
        return jsonify(presenters.task(controller.update_task(task, fields))), 200

    @bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        results = controller.search(
            text=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=query_integer('priority', 'Prioridade inválida'),
            user_id=query_integer('user_id', 'Usuário inválido'),
        )
        return jsonify([presenters.task(task) for task in results]), 200

    @bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
