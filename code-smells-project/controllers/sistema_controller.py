"""Operational use cases: health report and administrative maintenance."""
import logging

from models.constants import APP_VERSION, VALOR_OCULTO
from models.errors import DependencyError, ValidationError

logger = logging.getLogger(__name__)


class SistemaController:
    def __init__(self, sistema, settings):
        self._sistema = sistema
        self._settings = settings

    def saude(self):
        """Return (report, None) when healthy, or (None, error detail) when the database fails.

        Catching here is the purpose of a health check: dependency failure is reported as data.
        """
        try:
            contagens = self._sistema.contagens()
        except DependencyError as err:
            logger.error("Health check failed: %s", err)
            return None, str(err)
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": APP_VERSION,
            "ambiente": self._settings.environment,
            "db_path": self._settings.database_path,
            "debug": self._settings.debug,
            # Field kept so the response shape is unchanged; the value is never disclosed.
            # Removing the field is listed under PROPOSED, NOT APPLIED.
            "secret_key": VALOR_OCULTO,
        }, None

    def resetar_banco(self):
        self._sistema.apagar_todos_os_dados()
        logger.warning("Banco de dados resetado")

    def executar_query(self, sql):
        if not sql:
            raise ValidationError("Query não informada")
        return self._sistema.executar_sql_arbitrario(sql)
