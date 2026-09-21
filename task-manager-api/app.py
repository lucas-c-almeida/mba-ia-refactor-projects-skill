"""Composition root: the only place that assembles the application (RP-06).

Nothing here runs at import time. `flask --app app run` finds `create_app` by convention;
`python app.py` builds the app and starts the development server with the configured settings.
"""
from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from models.category_repository import CategoryRepository
from models.clock import local_now, utc_now
from models.task_repository import TaskRepository
from models.unit_of_work import UnitOfWork
from models.user_repository import UserRepository
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    tasks = TaskRepository(db)
    users = UserRepository(db)
    categories = CategoryRepository(db)
    unit_of_work = UnitOfWork(db)

    app.register_blueprint(create_task_blueprint(
        TaskController(tasks, users, categories, unit_of_work, clock=utc_now)))
    app.register_blueprint(create_user_blueprint(
        UserController(users, tasks, unit_of_work, clock=utc_now)))
    app.register_blueprint(create_category_blueprint(
        CategoryController(categories, tasks, unit_of_work)))
    app.register_blueprint(create_report_blueprint(
        ReportController(tasks, users, categories, clock=utc_now)))
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(local_now())}

    @app.route('/')
    def index():
        return {'message': API_NAME, 'version': API_VERSION}

    with app.app_context():
        db.create_all()   # every mapped table is registered by the repository imports above

    return app


if __name__ == '__main__':
    settings = load_settings()
    create_app(settings).run(debug=settings.debug, host=settings.host, port=settings.port)
