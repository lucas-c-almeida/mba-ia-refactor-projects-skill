"""Verificação de saúde do banco: traduz falha do driver para o erro de dependência do domínio."""
import sqlite3
from dataclasses import dataclass

from models.erros import ErroDependencia


@dataclass(frozen=True)
class Contagens:
    produtos: int
    usuarios: int
    pedidos: int


class SaudeRepositorio:
    def __init__(self, provedor_conexao):
        self._conexao = provedor_conexao

    def contagens(self):
        try:
            conexao = self._conexao()
            conexao.execute("SELECT 1")
            linha = conexao.execute(
                """
                SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
                       (SELECT COUNT(*) FROM usuarios) AS usuarios,
                       (SELECT COUNT(*) FROM pedidos)  AS pedidos
                """
            ).fetchone()
        except sqlite3.Error as erro:
            raise ErroDependencia("banco de dados indisponível") from erro
        return Contagens(linha["produtos"], linha["usuarios"], linha["pedidos"])
