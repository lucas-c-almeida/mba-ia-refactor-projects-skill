from flask import Blueprint, jsonify

from routes import serializers


def create_report_blueprint(controller, operator_guard):
    bp = Blueprint('reports', __name__)

    @bp.route('/reports/summary', methods=['GET'])
    @operator_guard.require
    def summary_report():
        # A per-user productivity rollup: operator-only (RP-04).
        return jsonify(serializers.summary_report(controller.summary())), 200

    @bp.route('/reports/user/<int:user_id>', methods=['GET'])
    def user_report(user_id):
        # Left open: classified business at the gate (D1); access control is proposed.
        return jsonify(serializers.user_report(controller.user_report(user_id))), 200

    return bp
