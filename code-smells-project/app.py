"""Composition root: loads configuration, builds the object graph, registers routes and the error boundary."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from controllers.health_controller import HealthController
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.usuario_controller import UsuarioController
from middlewares.error_handler import registrar_tratamento_de_erros
from models.database import Database
from models.pedido import PedidoRepository
from models.produto import ProdutoRepository
from models.relatorio import RelatorioRepository
from models.saude import SaudeRepository
from models.seed import semear
from models.usuario import UsuarioRepository
from routes import pedido_routes, produto_routes, relatorio_routes, system_routes, usuario_routes


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    db = Database(settings.db_path)
    db.initialize(semear)

    app.register_blueprint(produto_routes.criar_blueprint(ProdutoController(ProdutoRepository(db))))
    app.register_blueprint(usuario_routes.criar_blueprint(UsuarioController(UsuarioRepository(db))))
    app.register_blueprint(pedido_routes.criar_blueprint(PedidoController(PedidoRepository(db))))
    app.register_blueprint(
        relatorio_routes.criar_blueprint(RelatorioController(RelatorioRepository(db)), settings.operator_token)
    )
    app.register_blueprint(system_routes.criar_blueprint(HealthController(SaudeRepository(db), settings)))
    registrar_tratamento_de_erros(app)
    return app


if __name__ == "__main__":
    configuracao = load_settings()
    logging.basicConfig(level=logging.INFO)
    aplicacao = create_app(configuracao)
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", configuracao.host, configuracao.port)
    aplicacao.run(host=configuracao.host, port=configuracao.port, debug=configuracao.debug)
