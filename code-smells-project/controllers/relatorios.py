"""Report use cases."""


class RelatorioController:
    def __init__(self, relatorios):
        self._relatorios = relatorios

    def vendas(self):
        return self._relatorios.vendas()
