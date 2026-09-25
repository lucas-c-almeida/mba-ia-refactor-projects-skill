"""Sales report use case."""


class ReportController:
    def __init__(self, pedidos):
        self._pedidos = pedidos

    def vendas(self) -> dict:
        return self._pedidos.relatorio_vendas()
