"""Health use case."""
from models.constants import API_VERSION, VALOR_MASCARADO


class HealthController:
    def __init__(self, saude, settings):
        self._saude = saude
        self._settings = settings

    def verificar(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": self._saude.contagens(),
            "versao": API_VERSION,
            "ambiente": self._settings.environment,
            "db_path": self._settings.db_path,
            "debug": self._settings.debug,
            "secret_key": VALOR_MASCARADO,
        }
