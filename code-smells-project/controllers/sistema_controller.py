"""Relatórios, saúde e administração."""
import logging

from models.erros import ErroValidacao
from models.relatorio import montar_resumo

logger = logging.getLogger(__name__)


class RelatorioController:
    def __init__(self, relatorios):
        self._relatorios = relatorios

    def vendas(self):
        return montar_resumo(*self._relatorios.totais_de_vendas())


class SaudeController:
    def __init__(self, saude):
        self._saude = saude

    def contagens(self):
        return self._saude.contagens()


class AdministracaoController:
    """Rotas administrativas sem autenticação — PROPOSED, NOT APPLIED (AP-04, AP-02)."""

    def __init__(self, administracao, unidade_de_trabalho):
        self._administracao = administracao
        self._transacao = unidade_de_trabalho

    def resetar_banco(self):
        with self._transacao():
            self._administracao.limpar_tudo()
        logger.warning("!!! BANCO DE DADOS RESETADO !!!")

    def executar_sql(self, dados):
        dados = dados if isinstance(dados, dict) else {}
        comando = dados.get("sql", "")
        if not comando or not isinstance(comando, str):
            raise ErroValidacao("Query não informada")
        with self._transacao():
            return self._administracao.executar_sql_livre(comando)
