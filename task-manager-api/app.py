"""Composition root: the only place that names concrete implementations and wires them.

Run:
    flask --app app run                # Flask discovers create_app()
    python app.py                      # uses HOST / PORT / FLASK_DEBUG from the environment
"""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from models.category import CategoryRepository
from models.task import TaskRepository
from models.user import UserRepository
from routes import register_routes


def create_app(settings=None):
    if settings is None:
        settings = load_settings()

    logging.basicConfig(level=settings.log_level,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    CORS(app)
    db.init_app(app)

    session = db.session
    task_repository = TaskRepository(session)
    user_repository = UserRepository(session)
    category_repository = CategoryRepository(session)

    register_routes(
        app,
        tasks=TaskController(session, task_repository, user_repository, category_repository),
        users=UserController(session, user_repository, task_repository),
        categories=CategoryController(session, category_repository, task_repository),
        reports=ReportController(task_repository, user_repository, category_repository),
    )
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    runtime_settings = load_settings()
    create_app(runtime_settings).run(debug=runtime_settings.debug,
                                     host=runtime_settings.host,
                                     port=runtime_settings.port)
