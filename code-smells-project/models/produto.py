"""Product: validation rules, serialization and persistence (AP-02, AP-03, AP-11, AP-12)."""

from models.errors import ValidationError

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN_CARACTERES = 2
NOME_MAX_CARACTERES = 200

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def produto_para_dict(linha):
    return {campo: linha[campo] for campo in CAMPOS}


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_dados_produto(dados):
    """The single product validation, used by both create and update (AP-12).

    Returns (nome, descricao, preco, estoque, categoria) or raises ValidationError, with the
    same checks, in the same order and with the same messages as the original create handler.
    """
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _eh_numero(preco):
        raise ValidationError("Preço inválido")
    if not _eh_numero(estoque):
        raise ValidationError("Estoque inválido")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN_CARACTERES:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_CARACTERES:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return nome, descricao, preco, estoque, categoria


class ProdutoRepository:
    def __init__(self, conexao):
        self._conexao = conexao

    def listar_todos(self):
        linhas = self._conexao().execute("SELECT * FROM produtos").fetchall()
        return [produto_para_dict(linha) for linha in linhas]

    def obter_por_id(self, produto_id):
        linha = self._conexao().execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return produto_para_dict(linha) if linha else None

    def obter_varios(self, ids):
        """One query for a set of ids (AP-10). Returns {id: row}."""
        ids = list(ids)
        if not ids:
            return {}
        marcadores = ", ".join("?" for _ in ids)
        linhas = self._conexao().execute(
            "SELECT * FROM produtos WHERE id IN (" + marcadores + ")", ids
        ).fetchall()
        return {linha["id"]: linha for linha in linhas}

    def criar(self, nome, descricao, preco, estoque, categoria):
        conexao = self._conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
                "VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conexao = self._conexao()
        with conexao:
            conexao.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? "
                "WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def remover(self, produto_id):
        conexao = self._conexao()
        with conexao:
            conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        condicoes = []
        parametros = []
        if termo:
            condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
            padrao = "%" + termo + "%"
            parametros.extend((padrao, padrao))
        if categoria:
            condicoes.append("categoria = ?")
            parametros.append(categoria)
        if preco_min:
            condicoes.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max:
            condicoes.append("preco <= ?")
            parametros.append(preco_max)

        sql = "SELECT * FROM produtos"
        if condicoes:
            sql += " WHERE " + " AND ".join(condicoes)
        linhas = self._conexao().execute(sql, parametros).fetchall()
        return [produto_para_dict(linha) for linha in linhas]
