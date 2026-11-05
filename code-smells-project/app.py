"""Composition root: loads configuration, builds the object graph, registers the routes
and the error boundary. The only module that names concrete implementations."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings, load_settings
from controllers.notificador import NotificadorLog
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.sistema_controller import SistemaController
from controllers.usuario_controller import UsuarioController
from middlewares.conexao import registrar_conexao_por_requisicao
from middlewares.operador import criar_guarda_de_operador
from middlewares.tratamento_de_erros import registrar_tratamento_de_erros
from models.database import Database
from models.pedido import PedidoRepository
from models.produto import ProdutoRepository
from models.relatorio import RelatorioRepository
from models.usuario import UsuarioRepository
from views import registrar_rotas

logger = logging.getLogger("loja")


def create_app(settings: Settings = None) -> Flask:
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    database = Database(settings.database_path)
    database.inicializar(settings)
    obter_conexao = registrar_conexao_por_requisicao(app, database)

    produtos = ProdutoRepository(obter_conexao)
    usuarios = UsuarioRepository(obter_conexao)
    pedidos = PedidoRepository(obter_conexao)
    relatorios = RelatorioRepository(obter_conexao)

    controllers = {
        "produtos": ProdutoController(produtos),
        "usuarios": UsuarioController(usuarios),
        "pedidos": PedidoController(pedidos, produtos, usuarios, NotificadorLog()),
        "relatorios": RelatorioController(relatorios),
        "sistema": SistemaController(produtos, usuarios, pedidos, settings),
    }
    registrar_rotas(app, controllers, criar_guarda_de_operador(settings.operator_token))
    registrar_tratamento_de_erros(app)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    configuracao = load_settings()
    aplicacao = create_app(configuracao)
    logger.info("SERVIDOR INICIADO em http://%s:%s", configuracao.host, configuracao.port)
    aplicacao.run(host=configuracao.host, port=configuracao.port, debug=configuracao.debug)
