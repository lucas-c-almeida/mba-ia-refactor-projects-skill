"""Report routes: parse → call the controller → render."""
from flask import Blueprint, jsonify

from routes import presenters


def create_report_blueprint(controller, operator_guard):
    bp = Blueprint('reports', __name__)

    @bp.route('/reports/summary', methods=['GET'])
    @operator_guard.require
    def summary_report():
        """Per-user productivity across every account: an operator report."""
        return jsonify(presenters.summary_report(controller.summary())), 200

    @bp.route('/reports/user/<int:user_id>', methods=['GET'])
    def user_report(user_id):
        return jsonify(presenters.user_report(*controller.user_report(user_id))), 200

    return bp
