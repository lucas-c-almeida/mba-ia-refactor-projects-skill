"""
Schema creation and demo-data seeding.

Named for what it does (unlike the original get_db(), which was a "get" that also
created tables and inserted rows — AP-16). Called once from the composition root.

Schema changes versus the original (fixes AP-20; each verified safe to add against
the only data this project ever has at boot time — its own seed rows):
  * usuarios.email gets a UNIQUE index. It is the column login_usuario looks up by
    and expects one result; verified there are zero duplicate emails in the seed
    data before adding it.
  * pedidos.usuario_id gets a FOREIGN KEY to usuarios.id, and itens_pedido.pedido_id
    gets one to pedidos.id. Neither has an existing DELETE endpoint whose behaviour
    the constraint would change.
  * itens_pedido.produto_id is deliberately left WITHOUT a foreign key: DELETE
    /produtos/<id> exists today with no check, and adding the constraint without
    first deciding cascade-vs-restrict would silently change what that endpoint
    does. See the audit report's "Proposed, Not Applied" section.
  * money columns (preco, total, preco_unitario) are stored as INTEGER minor units
    (cents) instead of REAL, avoiding binary-floating-point drift. The JSON boundary
    still serializes a decimal number in the same units as before (see
    src/models/product_repository.py and order_repository.py).

Passwords are hashed with werkzeug's generate_password_hash (Flask's own dependency
— no new dependency added) instead of stored in plain text (fixes AP-08).
"""
import sqlite3

from werkzeug.security import generate_password_hash

from src.models.constants import STATUS_PENDENTE


def ensure_schema_and_seed(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT,
            preco_cents INTEGER,
            estoque INTEGER,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha_hash TEXT,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS usuarios_email_key ON usuarios (email)"
    )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios (id),
            status TEXT DEFAULT '{STATUS_PENDENTE}',
            total_cents INTEGER,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL REFERENCES pedidos (id),
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario_cents INTEGER
        )
        """
    )
    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos = [
            ("Notebook Gamer", "Notebook potente para jogos", 599999, 10, "informatica"),
            ("Mouse Wireless", "Mouse sem fio ergonômico", 8990, 50, "informatica"),
            ("Teclado Mecânico", "Teclado mecânico RGB", 29990, 30, "informatica"),
            ("Monitor 27''", "Monitor 27 polegadas 144hz", 189990, 15, "informatica"),
            ("Headset Gamer", "Headset com microfone", 19990, 25, "informatica"),
            ("Cadeira Gamer", "Cadeira ergonômica", 129990, 8, "moveis"),
            ("Webcam HD", "Webcam 1080p", 24990, 20, "informatica"),
            ("Hub USB", "Hub USB 3.0 7 portas", 7990, 40, "informatica"),
            ("SSD 1TB", "SSD NVMe 1TB", 44990, 35, "informatica"),
            ("Camiseta Dev", "Camiseta estampa código", 5990, 100, "vestuario"),
        ]
        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco_cents, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            produtos,
        )

        # Demo accounts for local exploration, as documented in README.md. Passwords
        # are hashed before they ever reach the database (fixes AP-08); this seed
        # data is still visible in source as sample credentials for a local demo,
        # exactly as the project's own README describes it.
        usuarios = [
            ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
            ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
            ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
        ]
        cursor.executemany(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
            usuarios,
        )
        connection.commit()
