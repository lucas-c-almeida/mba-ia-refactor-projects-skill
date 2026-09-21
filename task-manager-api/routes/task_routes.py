"""Task routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify, request

from routes import presenters


def create_task_blueprint(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        rows = controller.list_tasks()
        return jsonify([presenters.task_list_item(task, overdue) for task, overdue in rows]), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        task, overdue = controller.get_task(task_id)
        return jsonify(presenters.task_with_overdue(task, overdue)), 200

    @task_bp.route('/tasks', methods=['POST'])
    def create_task():
        task = controller.create_task(request.get_json())
        return jsonify(presenters.task(task)), 201

    @task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        task = controller.update_task(task_id, request.get_json())
        return jsonify(presenters.task(task)), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @task_bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        tasks = controller.search(text=request.args.get('q', ''),
                                  status=request.args.get('status', ''),
                                  priority=request.args.get('priority', ''),
                                  user_id=request.args.get('user_id', ''))
        return jsonify([presenters.task(task) for task in tasks]), 200

    @task_bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return task_bp
