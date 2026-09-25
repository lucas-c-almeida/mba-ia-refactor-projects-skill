"""
Boundary validation helpers (fixes AP-11: values were previously used with no
presence/type/range check, and AP-12: the create/update product checks were
duplicated with drift). Each function returns a list of error strings — empty
means valid — mirroring the original's error message wording so response shapes
for already-covered cases (missing field, negative price) are unchanged.

These answer "is this a well-formed request", not "is this a legal state change" —
domain invariants that need more context stay in src/models (see order_repository).
"""
from src.models.constants import CATEGORIAS_VALIDAS

NOME_MIN_LENGTH = 2
NOME_MAX_LENGTH = 200


def validar_produto_campos_basicos(dados: dict) -> list:
    """The part criar_produto and atualizar_produto have always agreed on."""
    erros = []
    if not dados:
        return ["Dados inválidos"]
    if "nome" not in dados:
        erros.append("Nome é obrigatório")
    if "preco" not in dados:
        erros.append("Preço é obrigatório")
    if "estoque" not in dados:
        erros.append("Estoque é obrigatório")
    if erros:
        return erros

    if dados["preco"] < 0:
        erros.append("Preço não pode ser negativo")
    if dados["estoque"] < 0:
        erros.append("Estoque não pode ser negativo")
    return erros


def validar_produto_criacao_extra(dados: dict) -> list:
    """Checks criar_produto has always applied but atualizar_produto never did.
    Kept separate from the shared check above rather than added to
    atualizar_produto, which would newly reject PUT requests that succeed today
    (see AP-12 in the audit report: proposed, not applied, for the update path)."""
    erros = []
    nome = dados.get("nome", "")
    if len(nome) < NOME_MIN_LENGTH:
        erros.append("Nome muito curto")
    if len(nome) > NOME_MAX_LENGTH:
        erros.append("Nome muito longo")
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))
    return erros


def parse_preco_opcional(raw):
    """Returns (value, error). A non-numeric value is now a clear failure instead
    of an uncaught ValueError that a broad except turned into a 500 (AP-11)."""
    if raw is None:
        return None, None
    try:
        return float(raw), None
    except (TypeError, ValueError):
        return None, "Valor de preço inválido"


def validar_item_pedido(item: dict) -> list:
    """A positive integer product id and quantity — invalid on their face,
    something no legitimate client would ever need to send (AP-11)."""
    erros = []
    produto_id = item.get("produto_id")
    if not isinstance(produto_id, int) or isinstance(produto_id, bool) or produto_id <= 0:
        erros.append("produto_id deve ser um inteiro positivo")
    quantidade = item.get("quantidade")
    if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
        erros.append("quantidade deve ser um inteiro positivo")
    return erros
