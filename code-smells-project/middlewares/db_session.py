"""One database connection per request, closed at teardown (AP-07, AP-13).

Repositories receive an instance of ConexaoPorRequisicao and call it to obtain the current
connection; they never know where it comes from.
"""

from flask import g

from models import database

_CHAVE = "_conexao_db"


class ConexaoPorRequisicao:
    def __init__(self, db_path):
        self._db_path = db_path

    def __call__(self):
        conexao = g.get(_CHAVE)
        if conexao is None:
            conexao = database.conectar(self._db_path)
            setattr(g, _CHAVE, conexao)
        return conexao

    def registrar(self, app):
        app.teardown_appcontext(self._fechar)

    @staticmethod
    def _fechar(_erro):
        conexao = g.pop(_CHAVE, None)
        if conexao is not None:
            conexao.close()
