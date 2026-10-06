"""Sales report: the discount rule and the aggregate query (AP-10, AP-15)."""

from models.pedido import StatusPedido

# Discount tiers on gross revenue: (revenue strictly above, rate). Checked from the highest down.
FAIXAS_DESCONTO = (
    (10000, 0.1),
    (5000, 0.05),
    (1000, 0.02),
)
CASAS_DECIMAIS = 2


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def montar_relatorio(total_pedidos, faturamento, pendentes, aprovados, cancelados):
    if faturamento is None:
        faturamento = 0
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
        "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
        "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos > 0 else 0,
    }


class RelatorioRepository:
    def __init__(self, conexao):
        self._conexao = conexao

    def totais_vendas(self):
        """One aggregate query instead of five."""
        linha = self._conexao().execute(
            "SELECT COUNT(*) AS total_pedidos, "
            "       SUM(total) AS faturamento, "
            "       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes, "
            "       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados, "
            "       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados "
            "  FROM pedidos",
            (StatusPedido.PENDENTE, StatusPedido.APROVADO, StatusPedido.CANCELADO),
        ).fetchone()
        return (
            linha["total_pedidos"],
            linha["faturamento"],
            linha["pendentes"],
            linha["aprovados"],
            linha["cancelados"],
        )
