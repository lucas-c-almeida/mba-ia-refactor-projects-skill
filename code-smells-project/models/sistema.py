"""Operational persistence: health counts and the administrative operations.

The administrative operations are kept with their current behaviour; removing or protecting
them is recorded as PROPOSED, NOT APPLIED in the audit report (AP-02, AP-04).
"""

TABELAS_EM_ORDEM_DE_LIMPEZA = ("itens_pedido", "pedidos", "produtos", "usuarios")


class SistemaRepository:
    def __init__(self, conexao):
        self._conexao = conexao

    def contagens(self):
        linha = self._conexao().execute(
            "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
            "       (SELECT COUNT(*) FROM usuarios) AS usuarios, "
            "       (SELECT COUNT(*) FROM pedidos) AS pedidos"
        ).fetchone()
        return {"produtos": linha["produtos"], "usuarios": linha["usuarios"], "pedidos": linha["pedidos"]}

    def limpar_tudo(self):
        conexao = self._conexao()
        with conexao:
            for tabela in TABELAS_EM_ORDEM_DE_LIMPEZA:
                # Table names come from the constant above, never from input.
                conexao.execute("DELETE FROM " + tabela)

    def executar_sql(self, sql):
        """Runs the statement as given. Returns the rows for a SELECT, None otherwise."""
        conexao = self._conexao()
        cursor = conexao.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(linha) for linha in cursor.fetchall()]
        conexao.commit()
        return None
