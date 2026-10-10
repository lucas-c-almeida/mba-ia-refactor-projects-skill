"""Sales report: the discount rule (pure) and the aggregate query."""
from decimal import ROUND_HALF_UP, Decimal

from models.money import CASAS_DECIMAIS, CENTAVOS_POR_UNIDADE, from_centavos
from models.pedido import STATUS_APROVADO, STATUS_CANCELADO, STATUS_INICIAL

# (revenue above, discount rate): the first tier that applies wins.
FAIXAS_DE_DESCONTO = (
    (Decimal("10000"), Decimal("0.10")),
    (Decimal("5000"), Decimal("0.05")),
    (Decimal("1000"), Decimal("0.02")),
)


def calcular_desconto_centavos(faturamento_centavos):
    faturamento = Decimal(faturamento_centavos) / CENTAVOS_POR_UNIDADE
    for limite, taxa in FAIXAS_DE_DESCONTO:
        if faturamento > limite:
            desconto = Decimal(faturamento_centavos) * taxa
            return int(desconto.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return 0


def montar_relatorio(total_pedidos, faturamento_centavos, pedidos_por_status):
    desconto_centavos = calcular_desconto_centavos(faturamento_centavos)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": from_centavos(faturamento_centavos),
        "desconto_aplicavel": from_centavos(desconto_centavos),
        "faturamento_liquido": from_centavos(faturamento_centavos - desconto_centavos),
        "pedidos_pendentes": pedidos_por_status.get(STATUS_INICIAL, 0),
        "pedidos_aprovados": pedidos_por_status.get(STATUS_APROVADO, 0),
        "pedidos_cancelados": pedidos_por_status.get(STATUS_CANCELADO, 0),
        "ticket_medio": (
            round(faturamento_centavos / CENTAVOS_POR_UNIDADE / total_pedidos, CASAS_DECIMAIS)
            if total_pedidos > 0 else 0),
    }


class RelatorioRepository:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def vendas(self):
        rows = self._get_connection().execute(
            "SELECT status, COUNT(*) AS pedidos, COALESCE(SUM(total_centavos), 0) AS centavos"
            " FROM pedidos GROUP BY status").fetchall()
        por_status = {row["status"]: row["pedidos"] for row in rows}
        return montar_relatorio(
            sum(row["pedidos"] for row in rows),
            sum(row["centavos"] for row in rows),
            por_status)
