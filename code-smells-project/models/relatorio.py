"""Relatório de vendas: política de desconto (regra de negócio) e agregação no banco."""
from dataclasses import dataclass

from models.pedido import StatusPedido

# Política comercial: (faturamento acima de, taxa de desconto), da faixa mais alta para a
# mais baixa. Definida pelo negócio — muda sem motivo técnico.
FAIXAS_DE_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)
CASAS_DECIMAIS_MONETARIAS = 2


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DE_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


@dataclass(frozen=True)
class ResumoVendas:
    total_pedidos: int
    faturamento_bruto: float
    desconto_aplicavel: float
    faturamento_liquido: float
    pedidos_pendentes: int
    pedidos_aprovados: int
    pedidos_cancelados: int
    ticket_medio: float


def montar_resumo(total_pedidos, faturamento, pendentes, aprovados, cancelados):
    if faturamento is None:
        faturamento = 0
    desconto = calcular_desconto(faturamento)
    casas = CASAS_DECIMAIS_MONETARIAS
    return ResumoVendas(
        total_pedidos=total_pedidos,
        faturamento_bruto=round(faturamento, casas),
        desconto_aplicavel=round(desconto, casas),
        faturamento_liquido=round(faturamento - desconto, casas),
        pedidos_pendentes=pendentes,
        pedidos_aprovados=aprovados,
        pedidos_cancelados=cancelados,
        ticket_medio=round(faturamento / total_pedidos, casas) if total_pedidos > 0 else 0,
    )


class RelatorioRepositorio:
    def __init__(self, provedor_conexao):
        self._conexao = provedor_conexao

    def totais_de_vendas(self):
        """Uma consulta agregada (antes: cinco)."""
        linha = self._conexao().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   SUM(total) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
              FROM pedidos
            """,
            (StatusPedido.PENDENTE, StatusPedido.APROVADO, StatusPedido.CANCELADO),
        ).fetchone()
        return (linha["total_pedidos"], linha["faturamento"], linha["pendentes"],
                linha["aprovados"], linha["cancelados"])
