"""SQLite access. One short-lived connection per unit of work; nothing global."""
import sqlite3
from contextlib import contextmanager

from models.constants import SQLITE_TIMEOUT_SEGUNDOS

_SCHEMA = (
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


class Database:
    def __init__(self, path):
        self._path = path

    @contextmanager
    def session(self):
        """Open a connection, commit on success, roll back on error, always close."""
        conn = sqlite3.connect(self._path, timeout=SQLITE_TIMEOUT_SEGUNDOS)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self, seed):
        """Create the schema and, on an empty catalogue, call `seed(conn)`."""
        with self.session() as conn:
            for statement in _SCHEMA:
                conn.execute(statement)
            conn.commit()
            if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                seed(conn)
