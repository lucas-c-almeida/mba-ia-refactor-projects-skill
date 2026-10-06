"""Task routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from models.errors import ValidationError
from routes import presenters

MSG_SEARCH_PARAMETER_INVALID = 'Parâmetro de busca inválido'


def _optional_int(raw):
    """Query-string integer: absent or empty means "no filter"; anything else must parse."""
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(MSG_SEARCH_PARAMETER_INVALID)


def create_task_blueprint(controller):
    bp = Blueprint('tasks', __name__)

    @bp.route('/tasks', methods=['GET'])
    def get_tasks():
        now = controller.now()
        return jsonify([presenters.task_list_item(t, now) for t in controller.list_tasks()]), 200

    @bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        task = controller.get_task(task_id)
        return jsonify(presenters.task_detail(task, controller.now())), 200

    @bp.route('/tasks', methods=['POST'])
    def create_task():
        task = controller.create(request.get_json())
        return jsonify(presenters.task_dict(task)), 201

    @bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        task = controller.update(task_id, request.get_json())
        return jsonify(presenters.task_dict(task)), 200

    @bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        tasks = controller.search(text=request.args.get('q', ''),
                                  status=request.args.get('status', ''),
                                  priority=_optional_int(request.args.get('priority', '')),
                                  user_id=_optional_int(request.args.get('user_id', '')))
        return jsonify([presenters.task_dict(t) for t in tasks]), 200

    @bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(presenters.task_stats(controller.stats())), 200

    return bp
