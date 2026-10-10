"""Connections, schema bootstrap and the one-off migrations of the SQLite datastore.

Nothing here runs at import time: the composition root calls ``init_database`` once at start-up
and opens one connection per request through ``connect``.
"""
import logging
import sqlite3
from contextlib import contextmanager

from models import seed
from models.money import to_centavos
from models.passwords import hash_password

logger = logging.getLogger(__name__)

# How long a writer waits for another connection's lock before failing.
BUSY_TIMEOUT_MS = 5000

_COLUMNS_PRODUTOS = """(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    preco_centavos INTEGER,
    estoque INTEGER,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)"""

_COLUMNS_PEDIDOS = """(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    status TEXT DEFAULT 'pendente',
    total_centavos INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)"""

_COLUMNS_ITENS_PEDIDO = """(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    preco_unitario_centavos INTEGER
)"""

_CREATE_USUARIOS = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

_CREATE_EMAIL_UNIQUE_INDEX = "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_email ON usuarios (email)"
_COUNT_DUPLICATE_EMAILS = (
    "SELECT COUNT(*) FROM (SELECT email FROM usuarios GROUP BY email HAVING COUNT(*) > 1)"
)

# Databases created before amounts were kept as integer centavos hold them in REAL columns. SQLite
# cannot change a column type in place, so each such table is rebuilt by copy inside one
# transaction; no row is dropped.
_LEGACY_MONEY_MIGRATIONS = (
    (
        "PRAGMA table_info(produtos)", "preco",
        (
            "CREATE TABLE produtos_novo " + _COLUMNS_PRODUTOS,
            "INSERT INTO produtos_novo (id, nome, descricao, preco_centavos, estoque, categoria, ativo,"
            " criado_em) SELECT id, nome, descricao, CAST(ROUND(preco * 100) AS INTEGER), estoque,"
            " categoria, ativo, criado_em FROM produtos",
            "DROP TABLE produtos",
            "ALTER TABLE produtos_novo RENAME TO produtos",
        ),
    ),
    (
        "PRAGMA table_info(pedidos)", "total",
        (
            "CREATE TABLE pedidos_novo " + _COLUMNS_PEDIDOS,
            "INSERT INTO pedidos_novo (id, usuario_id, status, total_centavos, criado_em) SELECT id,"
            " usuario_id, status, CAST(ROUND(total * 100) AS INTEGER), criado_em FROM pedidos",
            "DROP TABLE pedidos",
            "ALTER TABLE pedidos_novo RENAME TO pedidos",
        ),
    ),
    (
        "PRAGMA table_info(itens_pedido)", "preco_unitario",
        (
            "CREATE TABLE itens_pedido_novo " + _COLUMNS_ITENS_PEDIDO,
            "INSERT INTO itens_pedido_novo (id, pedido_id, produto_id, quantidade,"
            " preco_unitario_centavos) SELECT id, pedido_id, produto_id, quantidade,"
            " CAST(ROUND(preco_unitario * 100) AS INTEGER) FROM itens_pedido",
            "DROP TABLE itens_pedido",
            "ALTER TABLE itens_pedido_novo RENAME TO itens_pedido",
        ),
    ),
)


def connect(db_path):
    """Open a connection in autocommit mode; transactions are explicit (see ``transaction``)."""
    connection = sqlite3.connect(db_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = " + str(BUSY_TIMEOUT_MS))
    return connection


@contextmanager
def transaction(connection):
    """One atomic unit of work: commit on success, roll back on any error."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def _migrate_legacy_money(connection):
    for describe_sql, legacy_column, statements in _LEGACY_MONEY_MIGRATIONS:
        columns = {row["name"] for row in connection.execute(describe_sql)}
        if legacy_column not in columns:
            continue
        logger.info("migrating a legacy table to integer centavos (%s)", describe_sql)
        with transaction(connection):
            for statement in statements:
                connection.execute(statement)


def _ensure_unique_email(connection):
    duplicates = connection.execute(_COUNT_DUPLICATE_EMAILS).fetchone()[0]
    if duplicates:
        logger.warning(
            "usuarios has %d e-mail(s) used by more than one account: the unique index was not "
            "created; resolve the duplicates and restart", duplicates)
        return
    connection.execute(_CREATE_EMAIL_UNIQUE_INDEX)


def _seed_initial_data(connection):
    if connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] != 0:
        return
    with transaction(connection):
        for nome, descricao, preco, estoque, categoria in seed.PRODUTOS:
            connection.execute(
                "INSERT INTO produtos (nome, descricao, preco_centavos, estoque, categoria)"
                " VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, to_centavos(preco), estoque, categoria))
        for nome, email, senha, tipo in seed.USUARIOS:
            connection.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, hash_password(senha), tipo))


def init_database(db_path):
    """Create or upgrade the schema and seed first-run data. Idempotent."""
    connection = connect(db_path)
    try:
        _migrate_legacy_money(connection)
        connection.execute("CREATE TABLE IF NOT EXISTS produtos " + _COLUMNS_PRODUTOS)
        connection.execute(_CREATE_USUARIOS)
        connection.execute("CREATE TABLE IF NOT EXISTS pedidos " + _COLUMNS_PEDIDOS)
        connection.execute("CREATE TABLE IF NOT EXISTS itens_pedido " + _COLUMNS_ITENS_PEDIDO)
        _ensure_unique_email(connection)
        _seed_initial_data(connection)
    finally:
        connection.close()
