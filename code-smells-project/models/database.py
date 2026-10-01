"""SQLite connection factory and schema bootstrap.

No module-level connection (AP-07): the composition root decides when connections are opened,
and request-scoped connections are managed by middlewares/db_session.py.
"""

import logging
import sqlite3

from models import senhas
from models.pedido import StatusPedido
from models.seed import PRODUTOS_INICIAIS, USUARIOS_INICIAIS
from models.usuario import TIPO_PADRAO

logger = logging.getLogger(__name__)

SCHEMA = (
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
        tipo TEXT DEFAULT '""" + TIPO_PADRAO + """',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT '""" + StatusPedido.PENDENTE + """',
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


def conectar(db_path):
    conexao = sqlite3.connect(db_path)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar(db_path):
    """Create the schema, apply the idempotent migrations and seed an empty database."""
    conexao = conectar(db_path)
    try:
        with conexao:
            for ddl in SCHEMA:
                conexao.execute(ddl)
            _garantir_email_unico(conexao)
            _migrar_senhas_em_texto(conexao)
            _semear_se_vazio(conexao)
    finally:
        conexao.close()


def _garantir_email_unico(conexao):
    """AP-20: email is the sign-in identity. The index is only created when the existing data
    already satisfies it; otherwise the conflict is logged and left for the owner to resolve."""
    duplicado = conexao.execute(
        "SELECT email FROM usuarios WHERE email IS NOT NULL "
        "GROUP BY email HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()
    if duplicado is not None:
        logger.warning("usuarios.email has duplicate values; unique index not created")
        return
    conexao.execute("CREATE UNIQUE INDEX IF NOT EXISTS usuarios_email_unico ON usuarios (email)")


def _migrar_senhas_em_texto(conexao):
    """AP-08: replace any plaintext password left by an earlier version with its hash."""
    linhas = conexao.execute("SELECT id, senha FROM usuarios WHERE senha IS NOT NULL").fetchall()
    pendentes = [
        (senhas.gerar_hash(linha["senha"]), linha["id"])
        for linha in linhas
        if not senhas.eh_hash(linha["senha"])
    ]
    if pendentes:
        conexao.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", pendentes)
        logger.info("Migrated %d plaintext password(s) to hashes", len(pendentes))


def _semear_se_vazio(conexao):
    total = conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    if total != 0:
        return
    conexao.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_INICIAIS,
    )
    conexao.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, senhas.gerar_hash(senha), tipo) for nome, email, senha, tipo in USUARIOS_INICIAIS],
    )
