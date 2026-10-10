"""Health check use case."""
import logging

from config.settings import APP_VERSION
from errors import HealthCheckError
from models.usuario import SENHA_MASCARADA

logger = logging.getLogger(__name__)


class SaudeController:
    def __init__(self, saude, settings):
        self._saude = saude
        self._settings = settings

    def verificar(self):
        try:
            contagens = self._saude.verificar()
        except Exception:
            logger.exception("health check failed")
            raise HealthCheckError("Banco de dados indisponível")
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": APP_VERSION,
            "ambiente": self._settings.environment,
            "db_path": self._settings.db_path,
            "debug": self._settings.debug,
            # The field is kept for existing readers; the value of a secret is never returned.
            "secret_key": SENHA_MASCARADA,
        }
