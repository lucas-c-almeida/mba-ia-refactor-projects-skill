"""Sales report: aggregates in the database, the discount rule in a pure function."""
from models.constants import FAIXAS_DESCONTO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def montar_relatorio(total_pedidos, faturamento, pendentes, aprovados, cancelados):
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


class RelatorioRepository:
    def __init__(self, db):
        self._db = db

    def vendas(self):
        with self._db.session() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(total) AS faturamento,
                       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
                       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
                       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
                FROM pedidos
                """,
                (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
            ).fetchone()
        faturamento = row["faturamento"] if row["faturamento"] is not None else 0
        return montar_relatorio(row["total"], faturamento, row["pendentes"], row["aprovados"], row["cancelados"])
