from flask import Blueprint, jsonify, request


def build_task_blueprint(controller):
    """Delivery layer for tasks: parse, call one controller method, render."""
    task_bp = Blueprint('tasks', __name__)

    @task_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        return jsonify(controller.list_tasks()), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        return jsonify(controller.get_task(task_id)), 200

    @task_bp.route('/tasks', methods=['POST'])
    def create_task():
        task = controller.create_task(request.get_json())
        return jsonify(task.to_dict()), 201

    @task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        task = controller.find_task(task_id)
        task = controller.update_task(task, request.get_json())
        return jsonify(task.to_dict()), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        return jsonify(controller.delete_task(task_id)), 200

    @task_bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        results = controller.search(
            request.args.get('q', ''),
            request.args.get('status', ''),
            request.args.get('priority', ''),
            request.args.get('user_id', ''),
        )
        return jsonify(results), 200

    @task_bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return task_bp
