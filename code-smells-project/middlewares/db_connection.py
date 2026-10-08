"""Request-scoped database connection: opened on first use, closed when the request ends.

An uncommitted transaction is discarded on close, so a request that fails halfway never leaves
partial writes for the next request to commit.
"""

from flask import g


def register_connection_lifecycle(app, database):
    """Return the `connection_provider` that repositories receive."""

    def connection_provider():
        if "db" not in g:
            g.db = database.connect()
        return g.db

    @app.teardown_appcontext
    def close_connection(_error):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    return connection_provider
