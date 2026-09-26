"""Delivery layer for tasks: parse -> call the controller -> render.

No persistence call and no business rule lives here any more (AP-05); the routes,
status codes and body shapes are unchanged (04-architecture-guidelines.md §6).
"""
from flask import Blueprint, jsonify, request

from controllers.task_controller import TaskController

task_bp = Blueprint('tasks', __name__)
_controller = TaskController()


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(_controller.list_all()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(_controller.get(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    # get_json() without silent=True: a syntactically malformed body is rejected by
    # Flask's own parser before reaching the controller, exactly as the original did.
    data = request.get_json()
    return jsonify(_controller.create(data)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    return jsonify(_controller.update(task_id, data)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify(_controller.delete(task_id)), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    result = _controller.search(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(_controller.stats()), 200
