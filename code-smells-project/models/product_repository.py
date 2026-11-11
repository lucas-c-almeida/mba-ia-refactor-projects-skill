"""Persistence for products. Every statement is parameterized."""
from models.database import transaction

_COLUMNS = "id, nome, descricao, preco_centavos, estoque, categoria, ativo, criado_em"


def _to_product(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco_centavos": row["preco_centavos"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProductRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def list_all(self):
        rows = self._connection().execute("SELECT {0} FROM produtos ORDER BY id".format(_COLUMNS))
        return [_to_product(row) for row in rows]

    def find_by_id(self, product_id):
        row = self._connection().execute(
            "SELECT {0} FROM produtos WHERE id = ?".format(_COLUMNS), (product_id,)
        ).fetchone()
        return _to_product(row) if row else None

    def find_by_ids(self, product_ids):
        ids = sorted(set(product_ids))
        if not ids:
            return {}
        placeholders = ", ".join("?" for _ in ids)
        rows = self._connection().execute(
            "SELECT {0} FROM produtos WHERE id IN ({1})".format(_COLUMNS, placeholders), ids
        )
        return {row["id"]: _to_product(row) for row in rows}

    def search(self, term, category, min_price_cents, max_price_cents):
        clauses, params = [], []
        if term:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params.extend(["%" + term + "%", "%" + term + "%"])
        if category:
            clauses.append("categoria = ?")
            params.append(category)
        if min_price_cents is not None:
            clauses.append("preco_centavos >= ?")
            params.append(min_price_cents)
        if max_price_cents is not None:
            clauses.append("preco_centavos <= ?")
            params.append(max_price_cents)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self._connection().execute(
            "SELECT {0} FROM produtos{1} ORDER BY id".format(_COLUMNS, where), params
        )
        return [_to_product(row) for row in rows]

    def create(self, nome, descricao, preco_centavos, estoque, categoria):
        connection = self._connection()
        with transaction(connection):
            cursor = connection.execute(
                "INSERT INTO produtos (nome, descricao, preco_centavos, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco_centavos, estoque, categoria),
            )
        return cursor.lastrowid

    def update(self, product_id, nome, descricao, preco_centavos, estoque, categoria):
        connection = self._connection()
        with transaction(connection):
            connection.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco_centavos = ?, estoque = ?, categoria = ? "
                "WHERE id = ?",
                (nome, descricao, preco_centavos, estoque, categoria, product_id),
            )

    def delete(self, product_id):
        connection = self._connection()
        with transaction(connection):
            connection.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
