import datetime

from flask import Blueprint


def build_system_blueprint():
    system_bp = Blueprint('system', __name__)

    @system_bp.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @system_bp.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return system_bp
