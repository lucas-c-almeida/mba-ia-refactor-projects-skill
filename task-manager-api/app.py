import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  (registers the tables with the metadata)
from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from models.category_repository import CategoryRepository
from models.task_repository import TaskRepository
from models.unit_of_work import UnitOfWork
from models.user_repository import UserRepository
from routes.category_routes import build_category_blueprint
from routes.report_routes import build_report_blueprint
from routes.system_routes import build_system_blueprint
from routes.task_routes import build_task_blueprint
from routes.user_routes import build_user_blueprint


def create_app(settings=None):
    """Composition root: the only place that names concrete implementations."""
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key
    app.config['OPERATOR_TOKEN'] = settings.operator_token

    CORS(app)
    db.init_app(app)

    tasks = TaskRepository(db.session)
    users = UserRepository(db.session)
    categories = CategoryRepository(db.session)
    unit_of_work = UnitOfWork(db.session)

    app.register_blueprint(build_task_blueprint(
        TaskController(tasks, users, categories, unit_of_work)))
    app.register_blueprint(build_user_blueprint(
        UserController(users, tasks, unit_of_work)))
    app.register_blueprint(build_report_blueprint(
        ReportController(tasks, users, categories)))
    app.register_blueprint(build_category_blueprint(
        CategoryController(categories, tasks, unit_of_work)))
    app.register_blueprint(build_system_blueprint())

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    runtime = load_settings()
    create_app(runtime).run(debug=runtime.debug, host=runtime.host, port=runtime.port)
