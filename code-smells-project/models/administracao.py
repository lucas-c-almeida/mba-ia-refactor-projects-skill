"""Operações administrativas expostas hoje sem autenticação.

Mantidas porque removê-las ou protegê-las muda o contrato público (a aplicação não tem
modelo de identidade). Ver "Proposed, Not Applied" em reports/audit-latest.md.
"""

TABELAS_EM_ORDEM_DE_LIMPEZA = ("itens_pedido", "pedidos", "produtos", "usuarios")


class AdministracaoRepositorio:
    def __init__(self, provedor_conexao):
        self._conexao = provedor_conexao

    def limpar_tudo(self):
        conexao = self._conexao()
        for tabela in TABELAS_EM_ORDEM_DE_LIMPEZA:   # nomes fixos, nunca vindos da entrada
            conexao.execute(f"DELETE FROM {tabela}")

    def executar_sql_livre(self, comando):
        """Executa SQL arbitrário do chamador — PROPOSED, NOT APPLIED (AP-02/AP-04)."""
        cursor = self._conexao().execute(comando)
        if comando.strip().upper().startswith("SELECT"):
            return [dict(linha) for linha in cursor.fetchall()]
        return None
