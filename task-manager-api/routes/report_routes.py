from flask import Blueprint, jsonify

from middlewares.guards import require_operator
from routes import serializers


def create_report_blueprint(controller):
    report_bp = Blueprint('reports', __name__)

    @report_bp.route('/reports/summary', methods=['GET'])
    @require_operator  # privileged: management aggregate naming every user
    def summary_report():
        return jsonify(serializers.summary_report(controller.summary())), 200

    @report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
    def user_report(user_id):
        return jsonify(controller.user_report(user_id)), 200

    return report_bp
