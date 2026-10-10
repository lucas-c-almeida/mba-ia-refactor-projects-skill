from flask import Blueprint, jsonify, request

from routes import serializers


def create_task_blueprint(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        return jsonify([serializers.task_list_item(t) for t in controller.list_tasks()]), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        return jsonify(serializers.task_detail(controller.get_task(task_id))), 200

    @task_bp.route('/tasks', methods=['POST'])
    def create_task():
        task = controller.create(request.get_json())
        return jsonify(serializers.task(task)), 201

    @task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        # The task is resolved before the body is read, as it always was (404 wins over 400).
        controller.get_task(task_id)
        task = controller.update(task_id, request.get_json())
        return jsonify(serializers.task(task)), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @task_bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        tasks = controller.search(request.args.get('q', ''),
                                  request.args.get('status', ''),
                                  request.args.get('priority', ''),
                                  request.args.get('user_id', ''))
        return jsonify([serializers.task(t) for t in tasks]), 200

    @task_bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return task_bp
