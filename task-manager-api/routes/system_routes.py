"""Service-level routes: index and health check."""
import datetime

from flask import Blueprint

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


def create_system_blueprint():
    system_bp = Blueprint('system', __name__)

    @system_bp.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @system_bp.route('/')
    def index():
        return {'message': API_NAME, 'version': API_VERSION}

    return system_bp
