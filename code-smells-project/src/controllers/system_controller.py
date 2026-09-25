"""
Home and health-check use cases. `health` no longer opens a cursor and issues raw
queries itself (fixed AP-03's third mixed responsibility) — it asks each repository
for its own count. The secret key is masked, not removed, and `debug` now reflects
the real (safe-by-default) configuration value; both keep their field and type, so
this is a value-only change (see AP-18 in the audit report).
"""

SECRET_KEY_REDACTED = "[REDACTED]"


class SystemController:
    def __init__(self, produtos, usuarios, pedidos, settings):
        self._produtos = produtos
        self._usuarios = usuarios
        self._pedidos = pedidos
        self._settings = settings

    def home(self) -> dict:
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }

    def health(self) -> dict:
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": "1.0.0",
            "ambiente": "producao",
            "db_path": self._settings.db_path,
            "debug": self._settings.debug,
            "secret_key": SECRET_KEY_REDACTED,
        }
