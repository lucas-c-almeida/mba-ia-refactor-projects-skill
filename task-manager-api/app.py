"""Composition root (AP-06). The only place that assembles the object graph: load
configuration, wire the database, register routes and the error boundary. Nothing else
in the codebase has a side effect at import time — `import app` no longer connects to,
or creates, anything. Call `create_app()` to get a ready application (seed.py does the
same, rather than importing a module-level instance)."""
import datetime

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    # AP-18: cors_origins defaults to "*", the ORIGINAL, unchanged behaviour. Narrowing
    # the default is proposed, not applied — see reports/audit-latest.md.
    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    settings = load_settings()
    create_app(settings).run(debug=settings.debug, host=settings.host, port=settings.port)
