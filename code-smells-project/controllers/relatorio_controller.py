from models.relatorio import montar_relatorio


class RelatorioController:
    def __init__(self, relatorios):
        self._relatorios = relatorios

    def vendas(self) -> dict:
        total_pedidos, faturamento, por_status = self._relatorios.totais()
        return montar_relatorio(total_pedidos, faturamento, por_status)
