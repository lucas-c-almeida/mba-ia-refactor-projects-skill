"""Raiz de composição: o único lugar que nomeia implementações concretas.

Carrega a configuração, cria a infraestrutura, monta repositórios e controllers, registra
rotas e a fronteira de erros. Nada tem efeito colateral na importação.
"""
import logging

from flask import Flask
from flask_cors import CORS

from config.configuracao import carregar_configuracao
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.sistema_controller import AdministracaoController, RelatorioController, SaudeController
from controllers.usuario_controller import UsuarioController
from middlewares import sessao_banco, tratamento_erros
from models import dados_iniciais
from models.administracao import AdministracaoRepositorio
from models.banco_de_dados import BancoDeDados, UnidadeDeTrabalho
from models.notificacao import NotificadorLog
from models.pedido import PedidoRepositorio
from models.produto import ProdutoRepositorio
from models.relatorio import RelatorioRepositorio
from models.saude import SaudeRepositorio
from models.usuario import UsuarioRepositorio
from views import pedidos, produtos, sistema, usuarios

logger = logging.getLogger(__name__)


def inicializar_banco(banco):
    """Cria o esquema, carrega os exemplos no primeiro boot e converte senhas legadas."""
    conexao = banco.conectar()
    try:
        banco.criar_esquema(conexao)
        provedor = lambda: conexao  # noqa: E731 — conexão única, só durante a inicialização
        repositorio_usuarios = UsuarioRepositorio(provedor)
        with UnidadeDeTrabalho(provedor)():
            dados_iniciais.carregar_se_vazio(conexao, repositorio_usuarios)
            migradas = repositorio_usuarios.migrar_senhas_em_claro()
        if migradas:
            logger.warning("%d senha(s) em claro convertida(s) para hash", migradas)
    finally:
        conexao.close()


def criar_app(configuracao=None):
    configuracao = configuracao or carregar_configuracao()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = configuracao.chave_secreta
    app.config["DEBUG"] = configuracao.debug
    # "*" preserva exatamente a política padrão anterior; outra lista restringe as origens.
    origens = "*" if configuracao.origens_cors == ("*",) else list(configuracao.origens_cors)
    CORS(app, origins=origens)

    banco = BancoDeDados(configuracao.caminho_banco)
    inicializar_banco(banco)

    conexao = sessao_banco.registrar(app, banco)
    transacao = UnidadeDeTrabalho(conexao)

    repositorio_produtos = ProdutoRepositorio(conexao)
    repositorio_pedidos = PedidoRepositorio(conexao)

    produtos.registrar(app, ProdutoController(repositorio_produtos, transacao))
    usuarios.registrar(app, UsuarioController(UsuarioRepositorio(conexao), transacao))
    pedidos.registrar(
        app,
        PedidoController(repositorio_pedidos, repositorio_produtos, NotificadorLog(), transacao),
        RelatorioController(RelatorioRepositorio(conexao)),
    )
    sistema.registrar(
        app,
        SaudeController(SaudeRepositorio(conexao)),
        AdministracaoController(AdministracaoRepositorio(conexao), transacao),
        configuracao,
    )
    tratamento_erros.registrar(app)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    configuracao = carregar_configuracao()
    aplicacao = criar_app(configuracao)
    logger.info("SERVIDOR INICIADO em http://%s:%s", configuracao.host, configuracao.porta)
    aplicacao.run(host=configuracao.host, port=configuracao.porta, debug=configuracao.debug)
