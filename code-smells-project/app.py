"""Composition root: the only place that names concrete implementations and wires them."""

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.health_controller import HealthController
from controllers.notifier import LogNotifier
from controllers.order_controller import OrderController
from controllers.product_controller import ProductController
from controllers.report_controller import ReportController
from controllers.user_controller import UserController
from middlewares.db_connection import register_connection_lifecycle
from middlewares.error_handler import register_error_handlers
from middlewares.operator_guard import make_operator_guard
from models.database import Database
from models.order import OrderRepository
from models.product import ProductRepository
from models.report import ReportRepository
from models.user import UserRepository
from views.health_routes import create_health_blueprint
from views.order_routes import create_order_blueprint
from views.product_routes import create_product_blueprint
from views.report_routes import create_report_blueprint
from views.user_routes import create_user_blueprint


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    database = Database(settings.db_path)
    database.initialize()
    connection_provider = register_connection_lifecycle(app, database)

    products = ProductRepository(connection_provider)
    users = UserRepository(connection_provider)
    orders = OrderRepository(connection_provider)
    reports = ReportRepository(connection_provider)

    operator_required = make_operator_guard(settings.operator_token)

    app.register_blueprint(create_product_blueprint(ProductController(products)))
    app.register_blueprint(create_user_blueprint(UserController(users)))
    app.register_blueprint(
        create_order_blueprint(OrderController(orders, products, LogNotifier()))
    )
    app.register_blueprint(
        create_report_blueprint(ReportController(reports), operator_required)
    )
    app.register_blueprint(create_health_blueprint(HealthController(reports), settings))

    register_error_handlers(app)
    return app


if __name__ == "__main__":
    app_settings = load_settings()
    create_app(app_settings).run(
        host=app_settings.host, port=app_settings.port, debug=app_settings.debug
    )
