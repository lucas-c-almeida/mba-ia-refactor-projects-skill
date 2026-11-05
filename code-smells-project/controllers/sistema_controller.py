import logging

from models.database import ErroDeBanco

logger = logging.getLogger(__name__)

VERSAO_API = "1.0.0"

# The health response keeps its secret_key field (clients read it); its value is never
# the configured key.
SEGREDO_MASCARADO = "********"


class SistemaController:
    def __init__(self, produtos, usuarios, pedidos, settings):
        self._produtos = produtos
        self._usuarios = usuarios
        self._pedidos = pedidos
        self._settings = settings

    def saude(self):
        """(healthy, payload). Reports the configuration actually in effect."""
        try:
            contagens = {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            }
        except ErroDeBanco:
            logger.exception("health check: database unavailable")
            return False, {"status": "erro", "detalhes": "banco de dados indisponível"}
        return True, {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": VERSAO_API,
            "ambiente": self._settings.environment,
            "db_path": self._settings.database_file,
            "debug": self._settings.debug,
            "secret_key": SEGREDO_MASCARADO,
        }
