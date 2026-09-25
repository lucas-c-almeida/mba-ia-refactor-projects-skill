"""
Composition root and entry point (fixes AP-06: this is now the one place that names
concrete implementations and assembles the object graph — configuration, the
database connection, repositories, controllers, routes and the error boundary).

Run exactly as before: `python app.py`. See README.md for configuration.
"""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import load_settings
from src.controllers.admin_controller import AdminController
from src.controllers.order_controller import OrderController
from src.controllers.product_controller import ProductController
from src.controllers.report_controller import ReportController
from src.controllers.system_controller import SystemController
from src.controllers.user_controller import UserController
from src.middlewares.errors import register_error_handlers
from src.models.db import create_connection
from src.models.order_repository import OrderRepository
from src.models.product_repository import ProductRepository
from src.models.schema import ensure_schema_and_seed
from src.models.user_repository import UserRepository
from src.views import (
    admin_routes,
    order_routes,
    product_routes,
    report_routes,
    system_routes,
    user_routes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("code-smells-project")


def create_app() -> Flask:
    settings = load_settings()
    if settings.secret_key_is_ephemeral:
        logger.warning(
            "SECRET_KEY not set in the environment; using a per-process generated "
            "key. Set SECRET_KEY explicitly outside local development."
        )

    connection = create_connection(settings.db_path)
    ensure_schema_and_seed(connection)

    produtos = ProductRepository(connection)
    usuarios = UserRepository(connection)
    pedidos = OrderRepository(connection)

    product_controller = ProductController(produtos)
    user_controller = UserController(usuarios)
    order_controller = OrderController(pedidos, usuarios)
    report_controller = ReportController(pedidos)
    admin_controller = AdminController(connection)
    system_controller = SystemController(produtos, usuarios, pedidos, settings)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    if settings.cors_allow_all:
        CORS(app)

    product_routes.register(app, product_controller)
    user_routes.register(app, user_controller)
    order_routes.register(app, order_controller)
    report_routes.register(app, report_controller)
    admin_routes.register(app, admin_controller)
    system_routes.register(app, system_controller)

    register_error_handlers(app, logger)

    return app, settings


if __name__ == "__main__":
    app, settings = create_app()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:{0}".format(settings.port))
    print("=" * 50)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
