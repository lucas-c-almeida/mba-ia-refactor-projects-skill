"""Views: route declarations. Each handler parses the request, calls one controller method and
renders the response; routes, methods, status codes and body shapes are the public contract."""

from views.pedido_routes import criar_blueprint_pedidos
from views.produto_routes import criar_blueprint_produtos
from views.relatorio_routes import criar_blueprint_relatorios
from views.sistema_routes import criar_blueprint_sistema
from views.usuario_routes import criar_blueprint_usuarios


def registrar_rotas(app, controllers):
    app.register_blueprint(criar_blueprint_produtos(controllers.produtos))
    app.register_blueprint(criar_blueprint_usuarios(controllers.usuarios))
    app.register_blueprint(criar_blueprint_pedidos(controllers.pedidos))
    app.register_blueprint(criar_blueprint_relatorios(controllers.relatorios))
    app.register_blueprint(criar_blueprint_sistema(controllers.sistema))
