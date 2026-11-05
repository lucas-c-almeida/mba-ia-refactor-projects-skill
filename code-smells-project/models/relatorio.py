"""Sales report: the discount rule and the aggregate query."""
from models.pedido import StatusPedido

# Revenue discount tiers, highest threshold first: (revenue above, rate).
FAIXAS_DE_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)
CASAS_DECIMAIS = 2


def calcular_desconto(faturamento: float) -> float:
    for limite, taxa in FAIXAS_DE_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def montar_relatorio(total_pedidos, faturamento, por_status) -> dict:
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
        "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
        "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
        "pedidos_pendentes": por_status.get(StatusPedido.PENDENTE, 0),
        "pedidos_aprovados": por_status.get(StatusPedido.APROVADO, 0),
        "pedidos_cancelados": por_status.get(StatusPedido.CANCELADO, 0),
        "ticket_medio": round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos > 0 else 0,
    }


class RelatorioRepository:
    def __init__(self, obter_conexao):
        self._obter_conexao = obter_conexao

    def totais(self):
        """(order count, revenue, count per status). Revenue is summed in whole cents;
        TOTAL() never overflows, and is exact while the sum stays below 2**53 cents."""
        conexao = self._obter_conexao()
        total_pedidos, centavos = conexao.execute(
            "SELECT COUNT(*), TOTAL(CAST(ROUND(total * 100) AS INTEGER)) FROM pedidos"
        ).fetchone()
        por_status = dict(conexao.execute(
            "SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
        faturamento = (centavos or 0) / 100
        return total_pedidos, faturamento, por_status
