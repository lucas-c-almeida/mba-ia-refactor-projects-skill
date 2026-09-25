"""
Administrative operations — behaviourally UNCHANGED from the original on purpose.

Both `/admin/reset-db` and `/admin/query` are reachable with no authentication at
all, and the audit report (AP-04, AP-02) files that as CRITICAL. Fixing it requires
introducing an identity model the application does not have today — that is a
product decision, not a refactoring, and the report's contract gate holds it back
as `PROPOSED, NOT APPLIED` rather than guessing one. See reports/audit-latest.md.

`executar_query` in particular has no safe transformation available: its entire
purpose is running attacker-or-operator-supplied SQL text, so there is nothing to
parameterize. It is moved here unchanged, still a live CRITICAL finding after this
refactor by design — the re-audit is expected to find it again.
"""
from src.models.errors import ValidationError


class AdminController:
    def __init__(self, connection):
        self._connection = connection

    def reset_db(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        self._connection.commit()

    def executar_query(self, dados: dict) -> dict:
        query = (dados or {}).get("sql", "")
        if not query:
            raise ValidationError("Query não informada")

        cursor = self._connection.cursor()
        cursor.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            return {"dados": [dict(row) for row in rows], "sucesso": True}
        self._connection.commit()
        return {"mensagem": "Query executada", "sucesso": True}
