"""SQLite access: connection factory, explicit transactions, and the schema bootstrap.

Nothing here runs on import. The composition root opens connections and runs
bootstrap() once at startup; each request gets its own connection.
"""
import logging
import sqlite3
from contextlib import contextmanager

from models import order_status
from models.money import to_cents
from models.passwords import UNUSABLE, hash_password

logger = logging.getLogger(__name__)

# Schema for a new database. Money columns hold integer cents.
SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco_centavos INTEGER,
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
        status TEXT DEFAULT '{0}',
        total_centavos INTEGER,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """.format(order_status.INITIAL),
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario_centavos INTEGER
    )
    """,
]

# A database created before money moved to cents has a REAL column instead. The cents
# column is added and filled from it; the REAL column is left in place (dropping it is
# an operator decision, recorded in the audit report).
LEGACY_MONEY_COLUMNS = [
    ("produtos", "preco", "preco_centavos"),
    ("pedidos", "total", "total_centavos"),
    ("itens_pedido", "preco_unitario", "preco_unitario_centavos"),
]

SEED_PRODUCTS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# (name, email, which configured password, role)
SEED_USERS = [
    ("Admin", "admin@loja.com", "admin", "admin"),
    ("João Silva", "joao@email.com", "customer", "cliente"),
    ("Maria Santos", "maria@email.com", "customer", "cliente"),
]


def connect(path):
    # Autocommit mode: every write happens inside an explicit transaction() block.
    connection = sqlite3.connect(str(path), isolation_level=None)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def transaction(connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def _columns(connection, table):
    return {row["name"] for row in connection.execute("PRAGMA table_info({0})".format(table))}


def _migrate_money_columns(connection):
    for table, legacy_column, cents_column in LEGACY_MONEY_COLUMNS:
        columns = _columns(connection, table)
        if cents_column not in columns:
            connection.execute("ALTER TABLE {0} ADD COLUMN {1} INTEGER".format(table, cents_column))
        if legacy_column in columns:
            connection.execute(
                "UPDATE {0} SET {1} = CAST(ROUND({2} * 100) AS INTEGER) "
                "WHERE {1} IS NULL AND {2} IS NOT NULL".format(table, cents_column, legacy_column)
            )


def _ensure_unique_email(connection):
    duplicates = connection.execute(
        "SELECT COUNT(*) FROM (SELECT email FROM usuarios GROUP BY email HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    if duplicates:
        logger.warning("usuarios.email has %d duplicated value(s); unique index not created", duplicates)
        return
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS usuarios_email_unico ON usuarios (email)")


def _seed(connection, seed_passwords):
    if connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] != 0:
        return
    connection.executemany(
        "INSERT INTO produtos (nome, descricao, preco_centavos, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        [(nome, descricao, to_cents(preco), estoque, categoria)
         for nome, descricao, preco, estoque, categoria in SEED_PRODUCTS],
    )
    rows = []
    for nome, email, password_key, tipo in SEED_USERS:
        password = seed_passwords.get(password_key, "")
        rows.append((nome, email, hash_password(password) if password else UNUSABLE, tipo))
    connection.executemany("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", rows)


def bootstrap(connection, seed_passwords):
    """Create or migrate the schema and seed an empty store. Idempotent."""
    with transaction(connection):
        for statement in SCHEMA:
            connection.execute(statement)
        _migrate_money_columns(connection)
        _ensure_unique_email(connection)
        _seed(connection, seed_passwords)
