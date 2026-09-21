"""Composition root: load configuration, build the object graph, register routes and boundaries.

Nothing here runs at import time. `flask --app app.py run` discovers create_app(); running
`python app.py` starts the development server with host/port/debug taken from the environment.
"""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.sistema_controller import SistemaController
from controllers.usuario_controller import UsuarioController
from middlewares.error_handler import register_error_handlers
from middlewares.request_context import register_request_context
from models import database
from models.notificacoes import NotificadorLog
from models.pedido import PedidoRepository
from models.produto import ProdutoRepository
from models.sistema import SistemaRepository
from models.usuario import UsuarioRepository
from views import pedido_routes, produto_routes, sistema_routes, usuario_routes


def create_app(settings=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    database.initialize(settings.database_path)
    connection = register_request_context(app, settings.database_path)
    register_error_handlers(app)

    produtos = ProdutoRepository(connection)
    usuarios = UsuarioRepository(connection)
    pedidos = PedidoRepository(connection)
    sistema = SistemaRepository(connection)

    app.register_blueprint(produto_routes.criar_blueprint(ProdutoController(produtos)))
    app.register_blueprint(usuario_routes.criar_blueprint(UsuarioController(usuarios)))
    app.register_blueprint(pedido_routes.criar_blueprint(
        PedidoController(pedidos, produtos, NotificadorLog()),
        RelatorioController(pedidos),
    ))
    app.register_blueprint(sistema_routes.criar_blueprint(SistemaController(sistema, settings)))
    return app


if __name__ == "__main__":
    configuracao = load_settings()
    aplicacao = create_app(configuracao)
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", configuracao.host, configuracao.port)
    aplicacao.run(host=configuracao.host, port=configuracao.port, debug=configuracao.debug)
