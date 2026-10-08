"""SQLite connection factory and schema bootstrap.

No module-level connection: a connection is created per unit of work by `connect()`, and the
schema is created explicitly by `initialize()`, called once by the composition root.
"""

import logging
import sqlite3

from models.credentials import hash_password
from models.seed import SEED_PRODUCTS, SEED_USERS

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

# Additive and idempotent: existing rows are kept. A sign-in name must identify one account.
UNIQUE_EMAIL_INDEX = "CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (email)"


class Database:
    def __init__(self, path: str):
        self._path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        connection = self.connect()
        try:
            for statement in SCHEMA:
                connection.execute(statement)
            connection.commit()
            self._ensure_unique_email(connection)
            self._seed_if_empty(connection)
        finally:
            connection.close()

    def _ensure_unique_email(self, connection: sqlite3.Connection) -> None:
        try:
            connection.execute(UNIQUE_EMAIL_INDEX)
            connection.commit()
        except sqlite3.IntegrityError:
            # The existing data already holds duplicate sign-in names; deciding which row wins is
            # a product decision, so the index is skipped and the operator is told.
            logger.warning("usuarios.email holds duplicates: unique index not created")

    def _seed_if_empty(self, connection: sqlite3.Connection) -> None:
        count = connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        if count != 0:
            return
        connection.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            SEED_PRODUCTS,
        )
        connection.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(name, email, hash_password(password), kind) for name, email, password, kind in SEED_USERS],
        )
        connection.commit()
