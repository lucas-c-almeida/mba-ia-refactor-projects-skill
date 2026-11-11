"""Index and health routes."""
from flask import jsonify

from models.errors import DatabaseUnavailableError
from views.serializers import MASKED_SECRET

API_VERSION = "1.0.0"


def register(app, controller, settings):
    @app.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": API_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    @app.get("/health")
    def health_check():
        try:
            counts = controller.check()
        except DatabaseUnavailableError as error:
            return jsonify({"status": "erro", "detalhes": error.message}), 500
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": API_VERSION,
            "ambiente": settings.environment,
            "db_path": settings.database_file,
            "debug": settings.debug,
            # The field has always been here; the signing key itself never leaves the process.
            "secret_key": MASKED_SECRET,
        }), 200
