"""
Product persistence — parameterized queries only (fixes AP-02). Converts between the
internal integer-cents column and the decimal number the API has always exposed
(fixes part of AP-20 without changing the response shape).
"""


def _cents_to_amount(cents: int) -> float:
    return round(cents / 100, 2)


def _amount_to_cents(amount) -> int:
    return round(float(amount) * 100)


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": _cents_to_amount(row["preco_cents"]),
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProductRepository:
    def __init__(self, connection):
        self._connection = connection

    def get_todos(self) -> list:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM produtos")
        return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_por_id(self, produto_id: int):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco_cents, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, _amount_to_cents(preco), estoque, categoria),
        )
        self._connection.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco_cents = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, _amount_to_cents(preco), estoque, categoria, produto_id),
        )
        self._connection.commit()

    def deletar(self, produto_id: int) -> None:
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        self._connection.commit()

    def ajustar_estoque(self, produto_id: int, delta: int) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (delta, produto_id)
        )

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None) -> list:
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            like = "%" + termo + "%"
            params.extend([like, like])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco_cents >= ?"
            params.append(_amount_to_cents(preco_min))
        if preco_max is not None:
            query += " AND preco_cents <= ?"
            params.append(_amount_to_cents(preco_max))

        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return [_row_to_dict(row) for row in cursor.fetchall()]

    def contar(self) -> int:
        cursor = self._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        return cursor.fetchone()[0]
