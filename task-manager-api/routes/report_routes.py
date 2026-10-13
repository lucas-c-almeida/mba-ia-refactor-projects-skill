from flask import Blueprint, jsonify

from middlewares.operator_guard import require_operator


def build_report_blueprint(controller):
    bp = Blueprint('reports', __name__)

    @bp.route('/reports/summary', methods=['GET'])
    @require_operator
    def summary_report():
        return jsonify(controller.summary()), 200

    @bp.route('/reports/user/<int:user_id>', methods=['GET'])
    @require_operator
    def user_report(user_id):
        return jsonify(controller.user_report(user_id)), 200

    return bp
