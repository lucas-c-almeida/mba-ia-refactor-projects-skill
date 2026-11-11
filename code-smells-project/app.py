"""Composition root: load configuration, build the object graph, register routes and
the error boundary. The only module that names concrete implementations."""
import logging

from flask import Flask
from flask_cors import CORS

from adapters.notifier import ConsoleNotifier
from config.settings import load_settings
from controllers.health_controller import HealthController
from controllers.order_controller import OrderController
from controllers.product_controller import ProductController
from controllers.report_controller import ReportController
from controllers.user_controller import UserController
from middlewares import db_session, error_handler
from models.database import bootstrap, connect
from models.order_repository import OrderRepository
from models.product_repository import ProductRepository
from models.store_stats_repository import StoreStatsRepository
from models.user_repository import UserRepository
from views import orders, products, reports, system, users


def _initialize_database(settings):
    connection = connect(settings.database_path)
    try:
        bootstrap(connection, {"admin": settings.seed_admin_password,
                               "customer": settings.seed_customer_password})
    finally:
        connection.close()


def create_app(settings=None):
    settings = settings or load_settings()
    app = Flask(__name__)
    if settings.secret_key:
        app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app, origins=settings.cors_origins)

    _initialize_database(settings)
    current_connection = db_session.register(app, settings.database_path)

    product_repository = ProductRepository(current_connection)
    user_repository = UserRepository(current_connection)
    order_repository = OrderRepository(current_connection)

    products.register(app, ProductController(product_repository))
    users.register(app, UserController(user_repository))
    orders.register(app, OrderController(order_repository, product_repository, user_repository, ConsoleNotifier()))
    reports.register(app, ReportController(order_repository), settings.operator_token)
    system.register(app, HealthController(StoreStatsRepository(current_connection)), settings)
    error_handler.register(app)
    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_settings()
    app = create_app(settings)
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:{0}".format(settings.port))
    print("=" * 50)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
