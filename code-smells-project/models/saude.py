"""Datastore health: a trivial probe query and the row counts the health endpoint reports."""


class SaudeRepository:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def verificar(self):
        connection = self._get_connection()
        connection.execute("SELECT 1")
        return {
            "produtos": connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
            "usuarios": connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
            "pedidos": connection.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
        }
