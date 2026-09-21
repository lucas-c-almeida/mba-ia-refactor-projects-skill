"""Report routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify

from routes.serializers import summary_report, user_report


def create_report_blueprint(controller):
    bp = Blueprint('reports', __name__)

    @bp.route('/reports/summary', methods=['GET'])
    def get_summary_report():
        return jsonify(summary_report(controller.summary())), 200

    @bp.route('/reports/user/<int:user_id>', methods=['GET'])
    def get_user_report(user_id):
        return jsonify(user_report(controller.user_report(user_id))), 200

    return bp
