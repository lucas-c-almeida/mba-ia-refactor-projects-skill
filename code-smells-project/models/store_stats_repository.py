"""Store-wide record counts, used by the health check."""


class StoreStatsRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def record_counts(self):
        row = self._connection().execute(
            "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
            "(SELECT COUNT(*) FROM usuarios) AS usuarios, "
            "(SELECT COUNT(*) FROM pedidos) AS pedidos"
        ).fetchone()
        return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}
