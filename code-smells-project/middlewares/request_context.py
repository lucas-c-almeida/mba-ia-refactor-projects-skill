"""Per-request context: a correlation id and a request-scoped database connection."""
import uuid

from flask import g, request

from models import database

REQUEST_ID_HEADER = "X-Request-ID"


def register_request_context(app, database_path):
    """Install the hooks and return the connection provider the repositories depend on."""

    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex

    @app.after_request
    def expose_request_id(response):
        response.headers[REQUEST_ID_HEADER] = getattr(g, "request_id", "")
        return response

    @app.teardown_appcontext
    def close_connection(_exc):
        connection = g.pop("db_connection", None)
        if connection is not None:
            connection.close()

    def connection_provider():
        if "db_connection" not in g:
            g.db_connection = database.connect(database_path)
        return g.db_connection

    return connection_provider
