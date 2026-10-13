import datetime

from flask import Blueprint


def build_system_blueprint():
    bp = Blueprint('system', __name__)

    @bp.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @bp.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return bp
