"""Composition root: the only module that wires configuration, models, controllers and routes."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db, enable_sqlite_foreign_keys, upgrade_legacy_tables
from middlewares.error_handler import register_error_handlers
from models.clock import utc_now
from models.repositories import CategoryRepository, TaskRepository, UnitOfWork, UserRepository
from routes.category_routes import build_category_blueprint
from routes.report_routes import build_report_blueprint
from routes.request import JsonRequest
from routes.system_routes import build_system_blueprint
from routes.task_routes import build_task_blueprint
from routes.user_routes import build_user_blueprint


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.request_class = JsonRequest
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key
    app.config['OPERATOR_TOKEN'] = settings.operator_token

    CORS(app)
    db.init_app(app)

    tasks = TaskRepository()
    users = UserRepository()
    categories = CategoryRepository()
    uow = UnitOfWork()

    app.register_blueprint(build_task_blueprint(TaskController(tasks, users, categories, uow, utc_now)))
    app.register_blueprint(build_user_blueprint(UserController(users, tasks, uow, utc_now)))
    app.register_blueprint(build_category_blueprint(CategoryController(categories, tasks, uow)))
    app.register_blueprint(build_report_blueprint(ReportController(tasks, users, categories, utc_now)))
    app.register_blueprint(build_system_blueprint())
    register_error_handlers(app)

    with app.app_context():
        import models  # noqa: F401  (registers the tables on the metadata)
        enable_sqlite_foreign_keys(db.engine)
        db.create_all()
        upgrade_legacy_tables(db.engine)

    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = load_settings()
    create_app(config).run(debug=config.debug, host=config.host, port=config.port)
