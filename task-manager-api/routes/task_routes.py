from flask import Blueprint, jsonify, request


def build_task_blueprint(controller):
    bp = Blueprint('tasks', __name__)

    @bp.route('/tasks', methods=['GET'])
    def get_tasks():
        return jsonify(controller.list_tasks()), 200

    @bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        return jsonify(controller.get_task(task_id)), 200

    @bp.route('/tasks', methods=['POST'])
    def create_task():
        return jsonify(controller.create_task(request.get_json())), 201

    @bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        return jsonify(controller.update_task(task_id, request.get_json())), 200

    @bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        return jsonify(controller.delete_task(task_id)), 200

    @bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        results = controller.search_tasks(
            request.args.get('q', ''),
            request.args.get('status', ''),
            request.args.get('priority', ''),
            request.args.get('user_id', ''),
        )
        return jsonify(results), 200

    @bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
