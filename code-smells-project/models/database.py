"""SQLite access: connection factory, schema and first-boot seed.

No module-level connection: each request gets its own connection through the provider
built in middlewares/conexao.py, and closes it at teardown.
"""
import logging
import sqlite3
from pathlib import Path

from models import senha

logger = logging.getLogger(__name__)

# The datastore failure the outer layers may handle, without importing the driver.
ErroDeBanco = sqlite3.Error

_ESQUEMA = (
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

_PRODUTOS_INICIAIS = (
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
)


class Database:
    def __init__(self, caminho: Path):
        self._caminho = caminho

    def conectar(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self._caminho)
        conexao.row_factory = sqlite3.Row
        return conexao

    def inicializar(self, settings) -> None:
        """Create the schema and, on an empty store, the initial catalog and accounts.

        Seeded passwords come from configuration and are stored hashed; an account whose
        password is not configured is created without a usable password.
        """
        usuarios_iniciais = (
            ("Admin", "admin@loja.com", settings.seed_admin_password, "admin"),
            ("João Silva", "joao@email.com", settings.seed_joao_password, "cliente"),
            ("Maria Santos", "maria@email.com", settings.seed_maria_password, "cliente"),
        )
        conexao = self.conectar()
        try:
            with conexao:
                for comando in _ESQUEMA:
                    conexao.execute(comando)
            if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                with conexao:
                    conexao.executemany(
                        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
                        "VALUES (?, ?, ?, ?, ?)",
                        _PRODUTOS_INICIAIS,
                    )
                    conexao.executemany(
                        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                        [
                            (nome, email,
                             senha.gerar_hash(valor) if valor else senha.SENHA_INUTILIZAVEL,
                             tipo)
                            for nome, email, valor, tipo in usuarios_iniciais
                        ],
                    )
                sem_senha = [email for _, email, valor, _ in usuarios_iniciais if not valor]
                if sem_senha:
                    logger.warning("seeded accounts without a configured password "
                                   "(sign-in disabled): %d", len(sem_senha))
        finally:
            conexao.close()
