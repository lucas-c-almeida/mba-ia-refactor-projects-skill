"""One database connection per request, opened on first use and closed at teardown."""
from flask import g

from models.database import connect


def register(app, database_path):
    def current_connection():
        if "db" not in g:
            g.db = connect(database_path)
        return g.db

    @app.teardown_appcontext
    def close_connection(_error):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    return current_connection
