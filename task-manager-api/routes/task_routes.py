"""Task routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from models.errors import ValidationError
from routes.serializers import task_detail, task_list_item, task_to_dict


def _optional_int(raw, message):
    """Query-string integer; empty means "not given". Garbage is a client error, not a crash."""
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(message)


def create_task_blueprint(controller):
    bp = Blueprint('tasks', __name__)

    @bp.route('/tasks', methods=['GET'])
    def list_tasks():
        return jsonify([task_list_item(t, overdue) for t, overdue in controller.list_tasks()]), 200

    @bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        task, overdue = controller.get_task(task_id)
        return jsonify(task_detail(task, overdue)), 200

    @bp.route('/tasks', methods=['POST'])
    def create_task():
        task = controller.create_task(request.get_json())
        return jsonify(task_to_dict(task)), 201

    @bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        task = controller.update_task(task_id, request.get_json())
        return jsonify(task_to_dict(task)), 200

    @bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        tasks = controller.search(
            text=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=_optional_int(request.args.get('priority', ''), 'Prioridade inválida'),
            user_id=_optional_int(request.args.get('user_id', ''), 'user_id inválido'),
        )
        return jsonify([task_to_dict(t) for t in tasks]), 200

    @bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
