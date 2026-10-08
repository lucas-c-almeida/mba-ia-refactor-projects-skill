"""Product persistence. Every statement binds its values; none is built from request text."""

from models.constants import LOOKUP_BATCH_SIZE


def row_to_product(row) -> dict:
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


class ProductRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def list_all(self) -> list:
        rows = self._connection().execute("SELECT * FROM produtos").fetchall()
        return [row_to_product(row) for row in rows]

    def find_by_id(self, product_id):
        row = self._connection().execute(
            "SELECT * FROM produtos WHERE id = ?", (product_id,)
        ).fetchone()
        return row_to_product(row) if row else None

    def find_many(self, product_ids) -> dict:
        """Products by id in a few set-based queries: {id: product}. Unknown ids are absent."""
        unique_ids = list(dict.fromkeys(product_ids))
        found = {}
        for start in range(0, len(unique_ids), LOOKUP_BATCH_SIZE):
            batch = unique_ids[start:start + LOOKUP_BATCH_SIZE]
            placeholders = ", ".join("?" for _ in batch)  # only "?" marks, never input text
            rows = self._connection().execute(
                "SELECT * FROM produtos WHERE id IN (" + placeholders + ")", batch
            ).fetchall()
            for row in rows:
                found[row["id"]] = row_to_product(row)
        return found

    def create(self, nome, descricao, preco, estoque, categoria) -> int:
        connection = self._connection()
        cursor = connection.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        connection.commit()
        return cursor.lastrowid

    def update(self, product_id, nome, descricao, preco, estoque, categoria) -> None:
        connection = self._connection()
        connection.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, product_id),
        )
        connection.commit()

    def delete(self, product_id) -> None:
        connection = self._connection()
        connection.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
        connection.commit()

    def search(self, termo, categoria=None, preco_min=None, preco_max=None) -> list:
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            pattern = "%" + termo + "%"
            params.extend([pattern, pattern])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        # Truthiness (not "is not None") is preserved verbatim: a bound of 0 is not applied.
        if preco_min:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = self._connection().execute(query, params).fetchall()
        return [row_to_product(row) for row in rows]
