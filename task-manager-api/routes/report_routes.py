"""Delivery layer for reports and categories: parse -> call the controller -> render.

(AP-05.) Categories are a distinct use case from reports, but the original placed both
in one blueprint file; the file is kept as-is (04-architecture-guidelines.md §7: do not
move code for aesthetics — no finding is resolved by relocating it), and each use case
now delegates to its own controller.
"""
from flask import Blueprint, jsonify, request

from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController

report_bp = Blueprint('reports', __name__)
_reports = ReportController()
_categories = CategoryController()


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(_reports.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    return jsonify(_reports.user_report(user_id)), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(_categories.list_all()), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    return jsonify(_categories.create(data)), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    return jsonify(_categories.update(cat_id, data)), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    return jsonify(_categories.delete(cat_id)), 200
