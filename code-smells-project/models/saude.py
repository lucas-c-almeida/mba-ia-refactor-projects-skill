"""Health probe queries."""
import logging
import sqlite3

from models.errors import ServicoIndisponivelError

logger = logging.getLogger(__name__)


class SaudeRepository:
    def __init__(self, db):
        self._db = db

    def contagens(self):
        try:
            with self._db.session() as conn:
                conn.execute("SELECT 1")
                return {
                    "produtos": conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
                    "usuarios": conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
                    "pedidos": conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
                }
        except sqlite3.Error:
            logger.exception("Health check falhou")
            raise ServicoIndisponivelError("Banco de dados indisponível")
