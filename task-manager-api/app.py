"""Composition root: builds the object graph, registers routes and the error boundary."""
import datetime

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
from models.task_repository import TaskRepository
from models.user_repository import UserRepository
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key
    app.config['OPERATOR_TOKEN'] = settings.operator_token

    CORS(app)
    db.init_app(app)

    tasks = TaskRepository()
    users = UserRepository()
    categories = CategoryRepository()

    app.register_blueprint(create_task_blueprint(TaskController(tasks, users, categories)))
    app.register_blueprint(create_user_blueprint(UserController(users, tasks)))
    app.register_blueprint(create_report_blueprint(ReportController(tasks, users, categories)))
    app.register_blueprint(create_category_blueprint(CategoryController(categories, tasks)))
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
    config = load_settings()
    create_app(config).run(debug=config.debug, host=config.host, port=config.port)
