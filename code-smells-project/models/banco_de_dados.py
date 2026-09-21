"""Infraestrutura de persistência: fábrica de conexões, esquema e unidade de trabalho.

Nada aqui roda na importação. Quem cria o `BancoDeDados` é a raiz de composição (app.py).
"""
import sqlite3
from contextlib import contextmanager

ESQUEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)


class BancoDeDados:
    """Fábrica de conexões SQLite. Uma conexão por unidade de trabalho, nunca global."""

    def __init__(self, caminho):
        self._caminho = caminho


    def conectar(self):
        # isolation_level=None: as transações são abertas explicitamente pela UnidadeDeTrabalho.
        conexao = sqlite3.connect(self._caminho, isolation_level=None)
        conexao.row_factory = sqlite3.Row
        return conexao

    def criar_esquema(self, conexao):
        for comando in ESQUEMA:
            conexao.execute(comando)


class UnidadeDeTrabalho:
    """Delimita uma transação sobre a conexão da requisição corrente.

    Confirma ao sair normalmente; desfaz tudo se qualquer exceção escapar — nenhuma
    escrita parcial sobrevive a uma falha.
    """

    def __init__(self, provedor_conexao):
        self._provedor_conexao = provedor_conexao

    @contextmanager
    def __call__(self):
        conexao = self._provedor_conexao()
        # IMMEDIATE: reserva a escrita no início, para que verificação e atualização
        # (ex.: estoque) não intercalem com outra transação.
        conexao.execute("BEGIN IMMEDIATE")
        try:
            yield conexao
        except BaseException:
            conexao.execute("ROLLBACK")
            raise
        conexao.execute("COMMIT")
