"""Products: domain constants and persistence."""
from models.money import from_centavos

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_MIN_CARACTERES = 2
NOME_MAX_CARACTERES = 200
LOTE_CONSULTA = 500  # ids per IN (...) query, well under the engine's bound-parameter limit

_COLUNAS = "id, nome, descricao, preco_centavos, estoque, categoria, ativo, criado_em"


def _para_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": from_centavos(row["preco_centavos"]),
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoRepository:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def listar(self):
        rows = self._get_connection().execute(
            "SELECT " + _COLUNAS + " FROM produtos ORDER BY id").fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._get_connection().execute(
            "SELECT " + _COLUNAS + " FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _para_dict(row) if row else None

    def criar(self, nome, descricao, preco_centavos, estoque, categoria):
        cursor = self._get_connection().execute(
            "INSERT INTO produtos (nome, descricao, preco_centavos, estoque, categoria)"
            " VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco_centavos, estoque, categoria))
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco_centavos, estoque, categoria):
        self._get_connection().execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco_centavos = ?, estoque = ?,"
            " categoria = ? WHERE id = ?",
            (nome, descricao, preco_centavos, estoque, categoria, produto_id))
        return True

    def deletar(self, produto_id):
        self._get_connection().execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        return True

    def baixar_estoque(self, baixas):
        """Decrease stock for every (produto_id, quantidade) pair in one batch."""
        self._get_connection().executemany(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            [(quantidade, produto_id) for produto_id, quantidade in baixas])

    def buscar(self, termo, categoria=None, preco_min_centavos=None, preco_max_centavos=None):
        consulta = "SELECT " + _COLUNAS + " FROM produtos WHERE 1=1"
        parametros = []
        if termo:
            consulta += " AND (nome LIKE ? OR descricao LIKE ?)"
            parametros.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            consulta += " AND categoria = ?"
            parametros.append(categoria)
        if preco_min_centavos:
            consulta += " AND preco_centavos >= ?"
            parametros.append(preco_min_centavos)
        if preco_max_centavos:
            consulta += " AND preco_centavos <= ?"
            parametros.append(preco_max_centavos)
        consulta += " ORDER BY id"
        rows = self._get_connection().execute(consulta, parametros).fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_para_pedido(self, produto_ids):
        """Only what an order line needs (stock, exact unit price in centavos), keyed by id.

        Ids are looked up in batches of ``LOTE_CONSULTA``: one query per batch, not per line.
        """
        ids = sorted(set(produto_ids))
        encontrados = {}
        for inicio in range(0, len(ids), LOTE_CONSULTA):
            lote = ids[inicio:inicio + LOTE_CONSULTA]
            marcadores = ", ".join(["?"] * len(lote))
            rows = self._get_connection().execute(
                "SELECT id, nome, estoque, preco_centavos FROM produtos WHERE id IN ("
                + marcadores + ")", lote).fetchall()
            encontrados.update({row["id"]: dict(row) for row in rows})
        return encontrados
