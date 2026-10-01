import logging

from config.settings import APP_VERSION
from models.errors import HealthCheckError

logger = logging.getLogger(__name__)

# The health response keeps its "secret_key" field, but never the value (AP-18, AP-08).
SEGREDO_MASCARADO = "********"


class SistemaController:
    def __init__(self, sistema, settings):
        self._sistema = sistema
        self._settings = settings

    def health(self):
        try:
            contagens = self._sistema.contagens()
        except Exception as exc:  # any datastore failure is reported as an unhealthy check
            logger.exception("Health check failed")
            raise HealthCheckError("Banco de dados indisponível") from exc
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": APP_VERSION,
            "ambiente": self._settings.environment,
            "db_path": self._settings.db_path,
            "debug": self._settings.debug,
            "secret_key": SEGREDO_MASCARADO,
        }

    def resetar_banco(self):
        self._sistema.limpar_tudo()
        logger.warning("!!! BANCO DE DADOS RESETADO !!!")

    def executar_query(self, sql):
        return self._sistema.executar_sql(sql)
