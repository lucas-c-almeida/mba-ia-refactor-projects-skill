"""Product: invariants and persistence."""
from models.erros import ErroDeValidacao

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_TAMANHO_MINIMO = 2
NOME_TAMANHO_MAXIMO = 200

# SQLite binds at most this many parameters per statement on older builds.
_LOTE_DE_IDS = 500


def validar_invariantes(nome: str, preco: float, estoque: int, categoria: str) -> None:
    """The product rules, the same for creation and update."""
    if preco < 0:
        raise ErroDeValidacao("Preço não pode ser negativo")
    if estoque < 0:
        raise ErroDeValidacao("Estoque não pode ser negativo")
    if len(nome) < NOME_TAMANHO_MINIMO:
        raise ErroDeValidacao("Nome muito curto")
    if len(nome) > NOME_TAMANHO_MAXIMO:
        raise ErroDeValidacao("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ErroDeValidacao("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))


def _para_dict(linha) -> dict:
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "descricao": linha["descricao"],
        "preco": linha["preco"],
        "estoque": linha["estoque"],
        "categoria": linha["categoria"],
        "ativo": linha["ativo"],
        "criado_em": linha["criado_em"],
    }


class ProdutoRepository:
    def __init__(self, obter_conexao):
        self._obter_conexao = obter_conexao

    def listar(self) -> list:
        linhas = self._obter_conexao().execute("SELECT * FROM produtos").fetchall()
        return [_para_dict(linha) for linha in linhas]

    def buscar_por_id(self, produto_id: int):
        linha = self._obter_conexao().execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return _para_dict(linha) if linha else None

    def buscar_varios(self, ids) -> dict:
        """Products by id, in as few round trips as the parameter limit allows."""
        unicos = list(dict.fromkeys(ids))
        encontrados = {}
        conexao = self._obter_conexao()
        for inicio in range(0, len(unicos), _LOTE_DE_IDS):
            lote = unicos[inicio:inicio + _LOTE_DE_IDS]
            marcadores = ", ".join("?" for _ in lote)
            for linha in conexao.execute(
                "SELECT * FROM produtos WHERE id IN (" + marcadores + ")", lote
            ).fetchall():
                encontrados[linha["id"]] = _para_dict(linha)
        return encontrados

    def pesquisar(self, termo, categoria=None, preco_min=None, preco_max=None) -> list:
        consulta = "SELECT * FROM produtos WHERE 1=1"
        parametros = []
        if termo:
            consulta += " AND (nome LIKE ? OR descricao LIKE ?)"
            padrao = "%" + termo + "%"
            parametros += [padrao, padrao]
        if categoria:
            consulta += " AND categoria = ?"
            parametros.append(categoria)
        if preco_min:
            consulta += " AND preco >= ?"
            parametros.append(preco_min)
        if preco_max:
            consulta += " AND preco <= ?"
            parametros.append(preco_max)
        linhas = self._obter_conexao().execute(consulta, parametros).fetchall()
        return [_para_dict(linha) for linha in linhas]

    def criar(self, nome, descricao, preco, estoque, categoria) -> int:
        conexao = self._obter_conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
                "VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria) -> None:
        conexao = self._obter_conexao()
        with conexao:
            conexao.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
                "categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def remover(self, produto_id: int) -> None:
        conexao = self._obter_conexao()
        with conexao:
            conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self) -> int:
        return self._obter_conexao().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
