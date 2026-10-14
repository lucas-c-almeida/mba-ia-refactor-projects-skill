"""Product persistence."""


def _para_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoRepository:
    def __init__(self, db):
        self._db = db

    def listar(self):
        with self._db.session() as conn:
            return [_para_dict(row) for row in conn.execute("SELECT * FROM produtos").fetchall()]

    def buscar_por_id(self, produto_id):
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
            return _para_dict(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        with self._db.session() as conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
            return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        with self._db.session() as conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        with self._db.session() as conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        """Search with optional filters. Falsy filters are ignored, as before."""
        sql = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            padrao = "%" + termo + "%"
            params.extend([padrao, padrao])
        if categoria:
            sql += " AND categoria = ?"
            params.append(categoria)
        if preco_min:
            sql += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            sql += " AND preco <= ?"
            params.append(preco_max)
        with self._db.session() as conn:
            return [_para_dict(row) for row in conn.execute(sql, params).fetchall()]
