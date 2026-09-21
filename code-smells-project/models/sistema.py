"""Operational persistence: health counters and administrative maintenance statements."""
import sqlite3

from models.errors import DependencyError


class SistemaRepository:
    def __init__(self, connection_provider):
        self._conn = connection_provider

    def contagens(self):
        try:
            row = self._conn().execute(
                "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
                "       (SELECT COUNT(*) FROM usuarios) AS usuarios, "
                "       (SELECT COUNT(*) FROM pedidos) AS pedidos"
            ).fetchone()
        except sqlite3.Error as err:
            raise DependencyError(str(err)) from err
        return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}

    def apagar_todos_os_dados(self):
        conn = self._conn()
        with conn:
            for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):  # fixed allow-list
                conn.execute("DELETE FROM " + tabela)

    def executar_sql_arbitrario(self, sql):
        """Run a caller-supplied statement.

        Preserved verbatim from the original behaviour of POST /admin/query. It is inherently an
        injection surface and is listed under PROPOSED, NOT APPLIED for removal / protection.
        Returns (rows or None, is_select).
        """
        conn = self._conn()
        cursor = conn.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()], True
        conn.commit()
        return None, False
