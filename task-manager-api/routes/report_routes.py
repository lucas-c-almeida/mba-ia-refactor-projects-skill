"""Report routes: parse -> call one controller method -> render."""
from flask import Blueprint, jsonify

from routes import presenters


def create_report_blueprint(controller):
    bp = Blueprint('reports', __name__)

    @bp.route('/reports/summary', methods=['GET'])
    def summary_report():
        return jsonify(presenters.summary_report(controller.summary())), 200

    @bp.route('/reports/user/<int:user_id>', methods=['GET'])
    def user_report(user_id):
        return jsonify(presenters.user_report(controller.user_report(user_id))), 200

    return bp
