"""One database connection per request, opened on first use and closed at teardown."""
from flask import g


def registrar_conexao_por_requisicao(app, database):
    def obter_conexao():
        if "conexao" not in g:
            g.conexao = database.conectar()
        return g.conexao

    @app.teardown_appcontext
    def fechar_conexao(_erro):
        conexao = g.pop("conexao", None)
        if conexao is not None:
            conexao.close()

    return obter_conexao
