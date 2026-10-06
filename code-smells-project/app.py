"""Composition root: the only place that names concrete implementations (AP-06).

    python app.py                    # development server, configured from the environment
    flask --app app run              # the factory create_app() is discovered by Flask

Configuration is read once by config/settings.py; see .env.example for every key.
"""

import logging
from types import SimpleNamespace

from flask import Flask
from flask_cors import CORS

from adapters.notificador import NotificadorConsole
from config.settings import load_settings
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.sistema_controller import SistemaController
from controllers.usuario_controller import UsuarioController
from middlewares.db_session import ConexaoPorRequisicao
from middlewares.error_handler import registrar_tratamento_de_erros
from models import database
from models.pedido import PedidoRepository
from models.produto import ProdutoRepository
from models.relatorio import RelatorioRepository
from models.sistema import SistemaRepository
from models.usuario import UsuarioRepository
from views import registrar_rotas

logger = logging.getLogger("loja")


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    database.inicializar(settings.db_path)
    conexao = ConexaoPorRequisicao(settings.db_path)
    conexao.registrar(app)

    produtos = ProdutoRepository(conexao)
    usuarios = UsuarioRepository(conexao)
    controllers = SimpleNamespace(
        produtos=ProdutoController(produtos),
        usuarios=UsuarioController(usuarios),
        pedidos=PedidoController(PedidoRepository(conexao), produtos, usuarios, NotificadorConsole()),
        relatorios=RelatorioController(RelatorioRepository(conexao)),
        sistema=SistemaController(SistemaRepository(conexao), settings),
    )

    registrar_rotas(app, controllers)
    registrar_tratamento_de_erros(app)
    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_settings()
    app = create_app(settings)

    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://localhost:%s", settings.port)
    logger.info("=" * 50)

    app.run(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
