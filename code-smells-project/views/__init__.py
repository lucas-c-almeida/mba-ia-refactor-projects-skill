from views.pedido_routes import registrar_rotas_pedido
from views.produto_routes import registrar_rotas_produto
from views.relatorio_routes import registrar_rotas_relatorio
from views.sistema_routes import registrar_rotas_sistema
from views.usuario_routes import registrar_rotas_usuario


def registrar_rotas(app, controllers, exigir_operador) -> None:
    registrar_rotas_produto(app, controllers["produtos"])
    registrar_rotas_usuario(app, controllers["usuarios"])
    registrar_rotas_pedido(app, controllers["pedidos"])
    registrar_rotas_relatorio(app, controllers["relatorios"], exigir_operador)
    registrar_rotas_sistema(app, controllers["sistema"])
