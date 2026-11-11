from flask import Blueprint, jsonify, request

from routes import serializers, validation


def create_task_blueprint(controller):
    bp = Blueprint('tasks', __name__)

    @bp.route('/tasks', methods=['GET'])
    def get_tasks():
        rows = controller.list_tasks()
        return jsonify([serializers.task_list_item(*row) for row in rows]), 200

    @bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        task, overdue = controller.get_task(task_id)
        return jsonify(serializers.task_with_overdue(task, overdue)), 200

    @bp.route('/tasks', methods=['POST'])
    def create_task():
        fields = validation.parse_task_create(request.get_json())
        task = controller.create_task(fields)
        return jsonify(serializers.task(task)), 201

    @bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        controller.require_task(task_id)
        changes = validation.parse_task_update(request.get_json())
        task = controller.update_task(task_id, changes)
        return jsonify(serializers.task(task)), 200

    @bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        criteria = validation.parse_task_search(request.args)
        tasks = controller.search(**criteria)
        return jsonify([serializers.task(task) for task in tasks]), 200

    @bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
