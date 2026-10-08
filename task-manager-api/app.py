"""Composition root: the only place that assembles the application (RP-06).

Importing this module has no side effects. `create_app()` loads the configuration, builds the
repositories and controllers, registers routes and the error boundary, and creates the schema.
"""
import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  (registers every model with the mapper before the schema is created)
from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from models.category_repository import CategoryRepository
from models.task_repository import TaskRepository
from models.user_repository import UserRepository
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint


def create_app(settings=None):
    settings = settings or load_settings()
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key
    app.config['OPERATOR_TOKEN'] = settings.operator_token
    app.config['DEBUG_MODE'] = settings.debug
    app.config['BIND_HOST'] = settings.host
    app.config['BIND_PORT'] = settings.port

    CORS(
        app,
        origins=settings.cors_origins,
        allow_private_network=settings.cors_allow_private_network,
    )
    db.init_app(app)

    tasks = TaskRepository(db.session)
    users = UserRepository(db.session)
    categories = CategoryRepository(db.session)

    app.register_blueprint(create_task_blueprint(TaskController(tasks, users, categories)))
    app.register_blueprint(create_user_blueprint(UserController(users, tasks)))
    app.register_blueprint(create_category_blueprint(CategoryController(categories, tasks)))
    app.register_blueprint(create_report_blueprint(ReportController(tasks, users, categories)))
    app.register_blueprint(create_system_blueprint())
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(
        debug=application.config['DEBUG_MODE'],
        host=application.config['BIND_HOST'],
        port=application.config['BIND_PORT'],
    )
