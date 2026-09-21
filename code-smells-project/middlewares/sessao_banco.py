"""Conexão de banco com escopo de requisição: criada sob demanda, fechada no teardown."""
from flask import g


def registrar(app, banco):
    """Registra o fechamento e devolve o provedor de conexão usado pelos repositórios."""

    def conexao_da_requisicao():
        if "conexao" not in g:
            g.conexao = banco.conectar()
        return g.conexao

    @app.teardown_appcontext
    def _fechar(_erro):
        conexao = g.pop("conexao", None)
        if conexao is not None:
            conexao.close()

    return conexao_da_requisicao
