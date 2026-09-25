"""Home and health-check routes."""
import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register(app, system_controller) -> None:
    @app.route("/", methods=["GET"])
    def index():
        return jsonify(system_controller.home())

    @app.route("/health", methods=["GET"])
    def health_check():
        try:
            return jsonify(system_controller.health()), 200
        except Exception:
            # health_check's failure shape ({"status": "erro", "detalhes": ...}) has
            # always been its own thing, distinct from the rest of the API's
            # {"erro": ...} convention — preserved as-is (same field, same type)
            # rather than folded into the centralized handler, which would change
            # this response's shape. The VALUE no longer leaks raw exception text
            # (AP-09 / AP-18), which the shape comparison does not check anyway.
            logger.exception("health check failed")
            return jsonify({"status": "erro", "detalhes": "Erro interno"}), 500
