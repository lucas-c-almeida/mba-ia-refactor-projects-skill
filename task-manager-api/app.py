"""Composition root: the only place that reads configuration, wires the layers and starts."""
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
from models.clock import utcnow
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    CORS(app, allow_private_network=settings.cors_allow_private_network)
    db.init_app(app)

    clock = utcnow
    app.register_blueprint(create_task_blueprint(TaskController(clock)))
    app.register_blueprint(create_user_blueprint(UserController(), clock))
    app.register_blueprint(create_report_blueprint(ReportController(clock)))
    app.register_blueprint(create_category_blueprint(CategoryController()))
    app.register_blueprint(create_system_blueprint())
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def main():
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    create_app(settings).run(debug=settings.debug, host=settings.host, port=settings.port)


if __name__ == '__main__':
    main()
