"""Produto: entidade, regras de validação e persistência."""
from dataclasses import dataclass
from numbers import Real

from models.erros import ErroValidacao

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_TAMANHO_MINIMO = 2
NOME_TAMANHO_MAXIMO = 200

_COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


@dataclass(frozen=True)
class Produto:
    id: int
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str
    ativo: int
    criado_em: str


@dataclass(frozen=True)
class DadosProduto:
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str


def _eh_numero(valor):
    return isinstance(valor, Real) and not isinstance(valor, bool)


def validar_dados_produto(dados):
    """Regra única de validação para criação e atualização (antes duplicada e divergente)."""
    if not isinstance(dados, dict) or not dados:
        raise ErroValidacao("Dados inválidos")
    if "nome" not in dados:
        raise ErroValidacao("Nome é obrigatório")
    if "preco" not in dados:
        raise ErroValidacao("Preço é obrigatório")
    if "estoque" not in dados:
        raise ErroValidacao("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ErroValidacao("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ErroValidacao("Descrição deve ser texto")
    if not _eh_numero(preco):
        raise ErroValidacao("Preço deve ser numérico")
    if not _eh_numero(estoque):
        raise ErroValidacao("Estoque deve ser numérico")
    if not isinstance(categoria, str):
        raise ErroValidacao("Categoria deve ser texto")

    if preco < 0:
        raise ErroValidacao("Preço não pode ser negativo")
    if estoque < 0:
        raise ErroValidacao("Estoque não pode ser negativo")
    if len(nome) < NOME_TAMANHO_MINIMO:
        raise ErroValidacao("Nome muito curto")
    if len(nome) > NOME_TAMANHO_MAXIMO:
        raise ErroValidacao("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ErroValidacao("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return DadosProduto(nome, descricao, preco, estoque, categoria)


def _produto(linha):
    return Produto(**{chave: linha[chave] for chave in linha.keys()})


class ProdutoRepositorio:
    def __init__(self, provedor_conexao):
        self._conexao = provedor_conexao

    def listar(self):
        cursor = self._conexao().execute(f"SELECT {_COLUNAS} FROM produtos ORDER BY id")
        return [_produto(linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, produto_id):
        cursor = self._conexao().execute(
            f"SELECT {_COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
        )
        linha = cursor.fetchone()
        return _produto(linha) if linha else None

    def buscar_por_ids(self, produto_ids):
        ids = list(dict.fromkeys(produto_ids))
        if not ids:
            return {}
        marcadores = ", ".join("?" for _ in ids)
        cursor = self._conexao().execute(
            f"SELECT {_COLUNAS} FROM produtos WHERE id IN ({marcadores})", ids
        )
        return {linha["id"]: _produto(linha) for linha in cursor.fetchall()}

    def pesquisar(self, termo, categoria, preco_min, preco_max):
        condicoes, parametros = [], []
        if termo:
            condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
            parametros += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            condicoes.append("categoria = ?")
            parametros.append(categoria)
        if preco_min:
            condicoes.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max:
            condicoes.append("preco <= ?")
            parametros.append(preco_max)
        filtro = " AND ".join(["1=1"] + condicoes)
        cursor = self._conexao().execute(
            f"SELECT {_COLUNAS} FROM produtos WHERE {filtro} ORDER BY id", parametros
        )
        return [_produto(linha) for linha in cursor.fetchall()]

    def inserir(self, dados):
        cursor = self._conexao().execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (dados.nome, dados.descricao, dados.preco, dados.estoque, dados.categoria),
        )
        return cursor.lastrowid

    def atualizar(self, produto_id, dados):
        self._conexao().execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (dados.nome, dados.descricao, dados.preco, dados.estoque, dados.categoria, produto_id),
        )

    def remover(self, produto_id):
        self._conexao().execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def baixar_estoque(self, quantidades_por_produto):
        self._conexao().executemany(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            [(quantidade, produto_id) for produto_id, quantidade in quantidades_por_produto],
        )
