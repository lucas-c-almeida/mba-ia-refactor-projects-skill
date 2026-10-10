"""Composition root: the only place that names concrete implementations and wires them together."""
import logging

from flask import Flask, g
from flask_cors import CORS

from config.settings import load_settings
from controllers.pedidos import PedidoController
from controllers.produtos import ProdutoController
from controllers.relatorios import RelatorioController
from controllers.saude import SaudeController
from controllers.usuarios import UsuarioController
from middlewares.error_handler import register_error_handlers
from middlewares.operator_guard import exigir_operador
from models.database import connect, init_database, transaction
from models.pedido import PedidoRepository
from models.produto import ProdutoRepository
from models.relatorio import RelatorioRepository
from models.saude import SaudeRepository
from models.usuario import UsuarioRepository
from routes import pedidos, produtos, relatorios, saude, usuarios

logger = logging.getLogger(__name__)


def _connection_per_request(app, db_path):
    """Each request gets its own connection, closed when the request ends."""

    def get_connection():
        if "db" not in g:
            g.db = connect(db_path)
        return g.db

    @app.teardown_appcontext
    def close_connection(_error):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    return get_connection


def create_app(settings=None):
    settings = settings or load_settings()
    init_database(settings.db_path)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    get_connection = _connection_per_request(app, settings.db_path)

    produto_repository = ProdutoRepository(get_connection)
    usuario_repository = UsuarioRepository(get_connection)
    pedido_repository = PedidoRepository(get_connection)

    def unidade_de_trabalho():
        return transaction(get_connection())

    produtos.register(app, ProdutoController(produto_repository))
    usuarios.register(app, UsuarioController(usuario_repository))
    pedidos.register(
        app, PedidoController(pedido_repository, produto_repository, unidade_de_trabalho))
    relatorios.register(
        app, RelatorioController(RelatorioRepository(get_connection)),
        exigir_operador(settings.operator_token))
    saude.register(app, SaudeController(SaudeRepository(get_connection), settings))
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    runtime_settings = load_settings()
    application = create_app(runtime_settings)
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://localhost:%s", runtime_settings.port)
    logger.info("=" * 50)
    application.run(
        host=runtime_settings.host, port=runtime_settings.port, debug=runtime_settings.debug)
