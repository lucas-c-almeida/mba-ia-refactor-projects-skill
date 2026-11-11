"""Health check use case."""
import logging
import sqlite3

from models.errors import DatabaseUnavailableError

logger = logging.getLogger(__name__)


class HealthController:
    def __init__(self, stats):
        self._stats = stats

    def check(self):
        try:
            return self._stats.record_counts()
        except sqlite3.Error:
            logger.exception("health check: database unavailable")
            raise DatabaseUnavailableError("Banco de dados indisponível")
