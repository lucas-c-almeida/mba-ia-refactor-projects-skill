"""Composition root: configuration, infrastructure, controllers, routes, error boundary.

Importing this module has no side effects; `create_app()` builds the application (RP-06).
"""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db, enforce_foreign_keys
from middlewares.error_handler import register_error_handlers
from middlewares.operator_guard import OperatorGuard
from models import category, task, user  # noqa: F401 — registers the tables for create_all
from models.clock import utc_now
from routes import register_routes


def create_app(settings=None):
    settings = settings or load_settings()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if settings.secret_key:
        app.config['SECRET_KEY'] = settings.secret_key

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    controllers = {
        'tasks': TaskController(clock=utc_now),
        'users': UserController(clock=utc_now),
        'reports': ReportController(clock=utc_now),
        'categories': CategoryController(),
    }
    register_routes(app, controllers, OperatorGuard(settings.operator_token))
    register_error_handlers(app)

    with app.app_context():
        enforce_foreign_keys(db.engine)
        db.create_all()
    return app


if __name__ == '__main__':
    runtime = load_settings()
    create_app(runtime).run(debug=runtime.debug, host=runtime.host, port=runtime.port)
