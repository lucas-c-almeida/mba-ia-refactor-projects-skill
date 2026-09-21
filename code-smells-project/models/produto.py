"""Product persistence. Every statement uses bound parameters."""


class ProdutoRepository:
    def __init__(self, connection_provider):
        self._conn = connection_provider

    def listar(self):
        rows = self._conn().execute("SELECT * FROM produtos").fetchall()
        return [dict(row) for row in rows]

    def obter(self, produto_id):
        row = self._conn().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return dict(row) if row else None

    def obter_varios(self, produto_ids):
        """Return {id: record} for the given ids, in one query."""
        ids = sorted(set(produto_ids))
        if not ids:
            return {}
        placeholders = ", ".join("?" for _ in ids)
        rows = self._conn().execute(
            "SELECT * FROM produtos WHERE id IN (" + placeholders + ")", ids
        ).fetchall()
        return {row["id"]: dict(row) for row in rows}

    def criar(self, nome, descricao, preco, estoque, categoria):
        conn = self._conn()
        with conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conn = self._conn()
        with conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        conn = self._conn()
        with conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        clauses = []
        params = []
        if termo:
            clauses.append("(nome LIKE '%' || ? || '%' OR descricao LIKE '%' || ? || '%')")
            params.extend([termo, termo])
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max:
            clauses.append("preco <= ?")
            params.append(preco_max)
        # Only fixed clause fragments are joined; every value is bound.
        where = " AND ".join(["1=1"] + clauses)
        rows = self._conn().execute("SELECT * FROM produtos WHERE " + where, params).fetchall()
        return [dict(row) for row in rows]
