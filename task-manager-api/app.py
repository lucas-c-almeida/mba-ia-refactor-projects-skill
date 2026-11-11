"""Composition root: the only place that wires configuration, persistence, controllers and
routes together (RP-06). Importing this module has no side effects."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db, enable_sqlite_foreign_keys
from middlewares.error_handler import register_error_handlers
from middlewares.operator_guard import OperatorGuard
from models.clock import SystemClock
from models.repositories import CategoryRepository, TaskRepository, UserRepository
from routes.category_routes import create_category_blueprint
from routes.converters import BoundedIntegerConverter
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Driver errors in logs never carry bound values (passwords, digests) (RP-08).
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'hide_parameters': True}
    app.config['SECRET_KEY'] = settings.secret_key
    app.url_map.converters['int'] = BoundedIntegerConverter

    CORS(app)
    db.init_app(app)

    clock = SystemClock()
    tasks, users, categories = TaskRepository(), UserRepository(), CategoryRepository()
    operator_guard = OperatorGuard(settings.operator_token)

    app.register_blueprint(create_system_blueprint())
    app.register_blueprint(create_task_blueprint(TaskController(tasks, users, categories, clock)))
    app.register_blueprint(create_user_blueprint(UserController(users, tasks, clock), operator_guard))
    app.register_blueprint(create_category_blueprint(CategoryController(categories, tasks)))
    app.register_blueprint(create_report_blueprint(
        ReportController(tasks, users, categories, clock), operator_guard))
    register_error_handlers(app)

    with app.app_context():
        enable_sqlite_foreign_keys(db.engine)
        db.create_all()

    return app


def main():
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    app = create_app(settings)
    app.run(debug=settings.debug, host=settings.host, port=settings.port)


if __name__ == '__main__':
    main()
