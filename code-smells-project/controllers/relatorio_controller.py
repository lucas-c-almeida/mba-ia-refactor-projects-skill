from models.relatorio import montar_relatorio


class RelatorioController:
    def __init__(self, relatorios):
        self._relatorios = relatorios

    def vendas(self):
        return montar_relatorio(*self._relatorios.totais_vendas())
